/**
 * stress.js - STRESS TEST
 * ────────────────────────
 * Objetivo: Encontrar el punto de quiebre de SAAS COREM desplegado en Railway
 *           (512 MB RAM, ~0.5-1 vCPU compartido).
 *
 * Estrategia: incremento gradual de VUs hasta detectar degradacion severa.
 * En cada escalon se mantiene la carga 5 minutos para estabilizar las metricas.
 *
 * Indicadores de quiebre buscados:
 *   - Error rate > 15%
 *   - p95 response time > 2000ms
 *   - Timeouts de conexion (http_req_failed por timeout)
 *   - Errores 502/503 de Railway (OOM o restart del dyno)
 *
 * Escalone de VUs: 10 -> 25 -> 50 -> 75 -> 100 -> 0 (recovery)
 * Duracion total: ~45 min
 *
 * PRECAUCION: Solo ejecutar en staging o local, NUNCA en produccion.
 * Ejecutar: k6 run --env ENV=staging scripts/stress.js
 */

import http   from 'k6/http';
import { sleep, check, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

import { getEnvConfig }    from '../config/environments.js';
import { STRESS_THRESHOLDS } from '../config/thresholds.js';
import { getMultiRoleTokens, authHeaders, authHeadersBinary } from '../helpers/auth.js';
import {
  generateBulkAttendancePayload,
  generatePaymentPayload,
  MOCK_STUDENT_IDS,
  randomItem,
  MESES_ESCOLARES,
} from '../helpers/data.js';

// ─── Metricas custom ──────────────────────────────────────────────────────────

const dashboardDuration      = new Trend('dashboard_duration', true);
const bulkAttendanceDuration = new Trend('bulk_attendance_duration', true);
const errorsByStatus         = new Counter('errors_by_status');
const http502Errors          = new Counter('http_502_errors');
const http503Errors          = new Counter('http_503_errors');
const timeouts               = new Counter('connection_timeouts');
const degradationRate        = new Rate('degradation_rate');

// ─── Opciones ─────────────────────────────────────────────────────────────────

export const options = {
  stages: [
    // Warm-up gradual
    { duration: '2m', target: 10  },
    { duration: '5m', target: 10  }, // baseline
    // Escalon 1: carga moderada
    { duration: '2m', target: 25  },
    { duration: '5m', target: 25  },
    // Escalon 2: carga alta (probable limite Railway)
    { duration: '2m', target: 50  },
    { duration: '5m', target: 50  },
    // Escalon 3: carga muy alta
    { duration: '2m', target: 75  },
    { duration: '5m', target: 75  },
    // Escalon 4: limite maximo - probablemente OOM en Railway
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    // Recovery: el sistema debe recuperarse
    { duration: '5m', target: 0   },
  ],
  thresholds: STRESS_THRESHOLDS,
  tags: { testType: 'stress', project: 'saas-corem' },
};

// ─── Setup ───────────────────────────────────────────────────────────────────

export function setup() {
  const env    = getEnvConfig();
  const tokens = getMultiRoleTokens(env.apiBase, env.tenantHost, {
    secretary: env.credentials.secretary,
    director:  env.credentials.director,
    teacher:   env.credentials.teacher,
  });
  return { tokens, env };
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function (data) {
  const { tokens, env } = data;
  const { fixtures }    = env;

  // En stress test todos los VUs hacen lo mismo: mezcla de endpoints
  // para estresar diferentes capas (DB queries, file generation, cache)
  const roll = Math.random();

  if (roll < 0.35) {
    runListOperations(tokens.secretary.access, env, fixtures);
  } else if (roll < 0.55) {
    runDashboardLoad(tokens.director.access, env, fixtures);
  } else if (roll < 0.70) {
    runBulkAttendance(tokens.teacher.access, env, fixtures);
  } else if (roll < 0.85) {
    runPaymentOps(tokens.secretary.access, env, fixtures);
  } else {
    runReportLoad(tokens.director.access, env);
  }
}

// ─── Operaciones de listado (estresan el ORM Django + PostgreSQL) ─────────────

function runListOperations(accessToken, env, fixtures) {
  const hdrs = authHeaders(accessToken, env.tenantHost);

  group('Stress: listados concurrentes', () => {
    // Ejecutar varias requests en paralelo para estresar el connection pool de PostgreSQL
    const responses = http.batch([
      ['GET', `${env.apiBase}/students/?page=1&page_size=25`,
        null, { headers: hdrs, tags: { endpoint: 'students_list' } }],
      ['GET', `${env.apiBase}/payments/?page=1&page_size=25`,
        null, { headers: hdrs, tags: { endpoint: 'payments_list' } }],
      ['GET', `${env.apiBase}/classrooms/`,
        null, { headers: hdrs, tags: { endpoint: 'classrooms_list' } }],
      ['GET', `${env.apiBase}/payments/?estado=VENCIDO`,
        null, { headers: hdrs, tags: { endpoint: 'payments_morosos' } }],
    ]);

    responses.forEach((res, i) => {
      const ok = check(res, {
        [`batch request ${i}: status 200`]:    (r) => r.status === 200,
        [`batch request ${i}: no timeout`]:    (r) => r.timings.duration < 5000,
      });
      if (!ok) {
        errorsByStatus.add(1);
        if (res.status === 502) http502Errors.add(1);
        if (res.status === 503) http503Errors.add(1);
        if (res.timings.duration >= 5000) timeouts.add(1);
        degradationRate.add(1);
      } else {
        degradationRate.add(0);
      }
    });

    sleep(1);
  });
}

// ─── Dashboard bajo stress (query costosa) ────────────────────────────────────

function runDashboardLoad(accessToken, env, fixtures) {
  const hdrs = authHeaders(accessToken, env.tenantHost);

  group('Stress: dashboard KPIs', () => {
    const start = Date.now();
    const res = http.get(
      `${env.apiBase}/dashboard/resumen/`,
      { headers: hdrs, tags: { endpoint: 'dashboard_resumen' } }
    );
    dashboardDuration.add(Date.now() - start);

    const ok = check(res, {
      'dashboard stress: status OK':    (r) => r.status === 200 || r.status === 503,
      'dashboard stress: no crash':     (r) => r.status !== 500,
    });
    if (res.status >= 500) {
      errorsByStatus.add(1);
      if (res.status === 502) http502Errors.add(1);
      if (res.status === 503) http503Errors.add(1);
      degradationRate.add(1);
    } else {
      degradationRate.add(0);
    }

    // Cashflow tambien
    const cashRes = http.get(
      `${env.apiBase}/cashflow/cash-transactions/?mes=${fixtures.mes}&anio=${fixtures.anio}`,
      { headers: hdrs, tags: { endpoint: 'cashflow_transactions' } }
    );
    check(cashRes, { 'cashflow stress: status 200': (r) => r.status === 200 });
    sleep(2);
  });
}

// ─── Registro masivo de asistencia (estresar escrituras en bulk) ──────────────

function runBulkAttendance(accessToken, env, fixtures) {
  const hdrs = authHeaders(accessToken, env.tenantHost);

  group('Stress: registro masivo asistencia', () => {
    const fecha   = new Date().toISOString().split('T')[0];
    const payload = generateBulkAttendancePayload(MOCK_STUDENT_IDS, fecha);
    const start   = Date.now();
    const res     = http.post(
      `${env.apiBase}/attendance/registro-masivo/`,
      JSON.stringify(payload),
      { headers: hdrs, tags: { endpoint: 'attendance_bulk' } }
    );
    bulkAttendanceDuration.add(Date.now() - start);

    const ok = check(res, {
      'bulk attendance: status 2xx':      (r) => r.status >= 200 && r.status < 300,
      'bulk attendance: no 500':          (r) => r.status !== 500,
      'bulk attendance: tiempo < 5000ms': (r) => r.timings.duration < 5000,
    });
    if (!ok) {
      errorsByStatus.add(1);
      degradationRate.add(1);
    } else {
      degradationRate.add(0);
    }
    sleep(2);
  });
}

// ─── Operaciones de pagos ─────────────────────────────────────────────────────

function runPaymentOps(accessToken, env, fixtures) {
  const hdrs = authHeaders(accessToken, env.tenantHost);

  group('Stress: operaciones de pagos', () => {
    // Consulta lista
    const list = http.get(
      `${env.apiBase}/payments/?page=1&page_size=25`,
      { headers: hdrs, tags: { endpoint: 'payments_list' } }
    );
    check(list, { 'payments list stress: status 200': (r) => r.status === 200 });
    sleep(0.5);

    // Detalle de pago
    const detail = http.get(
      `${env.apiBase}/payments/${fixtures.paymentId}/`,
      { headers: hdrs, tags: { endpoint: 'payments_detail' } }
    );
    check(detail, { 'payments detail stress: status 200': (r) => r.status === 200 });

    if (detail.status >= 500) {
      errorsByStatus.add(1);
      degradationRate.add(1);
    } else {
      degradationRate.add(0);
    }
    sleep(1);
  });
}

// ─── Descarga de reportes Excel (operacion mas costosa) ───────────────────────

function runReportLoad(accessToken, env) {
  const hdrs = authHeadersBinary(accessToken, env.tenantHost);

  group('Stress: generacion Excel concurrente', () => {
    const res = http.get(
      `${env.apiBase}/reports/morosidad-excel/`,
      { headers: hdrs, tags: { endpoint: 'reports_morosidad_excel' }, timeout: '30s' }
    );
    const ok = check(res, {
      'report excel stress: status 200':      (r) => r.status === 200,
      'report excel stress: no 503':          (r) => r.status !== 503,
      'report excel stress: tiempo < 10000ms': (r) => r.timings.duration < 10000,
    });
    if (!ok) {
      errorsByStatus.add(1);
      if (res.status === 503) http503Errors.add(1);
      degradationRate.add(1);
    } else {
      degradationRate.add(0);
    }
    sleep(3);
  });
}

// ─── Teardown ─────────────────────────────────────────────────────────────────

export function teardown(data) {
  console.log(`Stress test finalizado. Ambiente: ${data.env.envName}`);
  console.log(
    'Revisar: errores 502/503 indican que Railway reinicio el dyno (OOM o CPU throttling). ' +
    'Correlacionar con metricas de Railway (RAM, CPU) en el mismo periodo de tiempo.'
  );
}
