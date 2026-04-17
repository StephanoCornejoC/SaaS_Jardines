/**
 * mixed-realistic.js - ESCENARIO MIXTO REALISTA
 * ─────────────────────────────────────────────
 * Objetivo: Simular el trafico real de un jardin de infancia durante un dia
 *           completo, con la distribucion de operaciones que ocurre en produccion.
 *
 * Distribucion de trafico (basada en uso tipico de COREM):
 *   70% LECTURA      - Consultas de alumnos, pagos, aulas, dashboard
 *   20% ESCRITURA    - Registro de pagos, asistencia masiva, nuevos alumnos
 *   10% REPORTES     - Descarga de Excel, cashflow, preview migracion
 *
 * Esta distribucion refleja que:
 *   - La secretaria consulta mucho mas de lo que escribe
 *   - Los docentes leen la lista de alumnos antes de pasar asistencia
 *   - Los reportes son esporadicos (tipicamente a fin de mes)
 *
 * Se usan k6 scenarios (multiple workloads) con diferentes ejecutores
 * para modelar exactamente esta distribucion.
 *
 * Ejecutar: k6 run --env ENV=staging scenarios/mixed-realistic.js
 *           k6 run --env ENV=staging --out json=results/mixed-results.json scenarios/mixed-realistic.js
 */

import http   from 'k6/http';
import { sleep, check, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

import { getEnvConfig }      from '../config/environments.js';
import { MIXED_THRESHOLDS }  from '../config/thresholds.js';
import { getMultiRoleTokens, authHeaders, authHeadersBinary } from '../helpers/auth.js';
import {
  generateStudentData,
  generateBulkAttendancePayload,
  generatePaymentPayload,
  MOCK_STUDENT_IDS,
  randomItem,
  MESES_ESCOLARES,
  randomPagination,
} from '../helpers/data.js';

// ─── Metricas custom de negocio ───────────────────────────────────────────────

const dashboardDuration        = new Trend('dashboard_duration',        true);
const reportGenerationDuration = new Trend('report_generation_duration', true);
const bulkAttendanceDuration   = new Trend('bulk_attendance_duration',   true);
const paymentRegDuration       = new Trend('payment_registration_duration', true);

const totalReads               = new Counter('mixed_reads_total');
const totalWrites              = new Counter('mixed_writes_total');
const totalReports             = new Counter('mixed_reports_total');
const businessErrors           = new Rate('business_error_rate');

// ─── Opciones con multiples scenarios ────────────────────────────────────────

export const options = {
  scenarios: {
    /**
     * LECTURAS (70% del trafico)
     * Ejecutor: constant-arrival-rate garantiza un throughput fijo independiente
     * de la latencia. Simula consultas continuas durante el dia.
     */
    reads_workload: {
      executor:        'constant-arrival-rate',
      rate:            35,        // 35 iteraciones por segundo = 70% de 50 req/s objetivo
      timeUnit:        '1s',
      duration:        '8m',
      preAllocatedVUs: 10,
      maxVUs:          30,
      exec:            'readsWorkload',
      tags:            { workload: 'reads' },
    },

    /**
     * ESCRITURAS (20% del trafico)
     * Ejecutor: ramping-arrival-rate simula el ritmo del dia escolar:
     * mas actividad en la manana (registro de asistencia, pagos) y baja al mediodia.
     */
    writes_workload: {
      executor:        'ramping-arrival-rate',
      startRate:       5,
      timeUnit:        '1s',
      stages: [
        { duration: '2m', target: 10 }, // manana: muchas escrituras
        { duration: '3m', target: 5  }, // mediodia: actividad normal
        { duration: '3m', target: 3  }, // tarde: pocas escrituras
      ],
      preAllocatedVUs: 5,
      maxVUs:          20,
      exec:            'writesWorkload',
      tags:            { workload: 'writes' },
    },

    /**
     * REPORTES (10% del trafico)
     * Ejecutor: constant-vus con think time largo.
     * Los reportes son operaciones poco frecuentes pero costosas.
     */
    reports_workload: {
      executor:  'constant-vus',
      vus:       2,
      duration:  '8m',
      exec:      'reportsWorkload',
      tags:      { workload: 'reports' },
    },
  },

  thresholds: MIXED_THRESHOLDS,
  tags:       { testType: 'mixed-realistic', project: 'saas-corem' },
};

// ─── Setup global ────────────────────────────────────────────────────────────

export function setup() {
  const env    = getEnvConfig();
  const tokens = getMultiRoleTokens(env.apiBase, env.tenantHost, {
    secretary: env.credentials.secretary,
    director:  env.credentials.director,
    teacher:   env.credentials.teacher,
  });
  return { tokens, env };
}

// ─── Workload: LECTURAS (70%) ─────────────────────────────────────────────────

export function readsWorkload(data) {
  const { tokens, env } = data;
  const { fixtures }    = env;

  // Rotar entre roles de lectura
  const roll = Math.random();
  const accessToken = roll < 0.5 ? tokens.secretary.access
    : roll < 0.8 ? tokens.teacher.access
    : tokens.director.access;
  const hdrs = authHeaders(accessToken, env.tenantHost);

  // Distribucion de endpoints de lectura
  const endpoint = Math.random();

  if (endpoint < 0.30) {
    // 30%: listado de alumnos (mas frecuente)
    group('Mixed: listar alumnos', () => {
      const pagination = randomPagination();
      const res = http.get(
        `${env.apiBase}/students/?page=${pagination.page}&page_size=${pagination.page_size}`,
        { headers: hdrs, tags: { endpoint: 'students_list', workload: 'reads' } }
      );
      check(res, {
        'read students: status 200':      (r) => r.status === 200,
        'read students: tiempo < 500ms':  (r) => r.timings.duration < 500,
      });
      if (res.status === 200) totalReads.add(1);
      else                     businessErrors.add(1);
      sleep(0.5);
    });

  } else if (endpoint < 0.50) {
    // 20%: detalle de alumno
    group('Mixed: detalle alumno', () => {
      const res = http.get(
        `${env.apiBase}/students/${fixtures.studentId}/`,
        { headers: hdrs, tags: { endpoint: 'students_detail', workload: 'reads' } }
      );
      check(res, {
        'read detail: status 200':      (r) => r.status === 200,
        'read detail: tiempo < 500ms':  (r) => r.timings.duration < 500,
      });
      if (res.status === 200) totalReads.add(1);
      sleep(0.5);
    });

  } else if (endpoint < 0.65) {
    // 15%: listado de pagos
    group('Mixed: listar pagos', () => {
      const res = http.get(
        `${env.apiBase}/payments/?page=1&page_size=25`,
        { headers: hdrs, tags: { endpoint: 'payments_list', workload: 'reads' } }
      );
      check(res, {
        'read payments: status 200':      (r) => r.status === 200,
        'read payments: tiempo < 500ms':  (r) => r.timings.duration < 500,
      });
      if (res.status === 200) totalReads.add(1);
      sleep(0.5);
    });

  } else if (endpoint < 0.75) {
    // 10%: morosos
    group('Mixed: morosos', () => {
      const res = http.get(
        `${env.apiBase}/payments/?estado=VENCIDO`,
        { headers: hdrs, tags: { endpoint: 'payments_morosos', workload: 'reads' } }
      );
      check(res, { 'read morosos: status 200': (r) => r.status === 200 });
      if (res.status === 200) totalReads.add(1);
      sleep(0.5);
    });

  } else if (endpoint < 0.85) {
    // 10%: aulas
    group('Mixed: aulas', () => {
      const res = http.get(
        `${env.apiBase}/classrooms/`,
        { headers: hdrs, tags: { endpoint: 'classrooms_list', workload: 'reads' } }
      );
      check(res, { 'read classrooms: status 200': (r) => r.status === 200 });
      if (res.status === 200) totalReads.add(1);
      sleep(0.3);
    });

  } else {
    // 15%: dashboard (lectura costosa)
    group('Mixed: dashboard', () => {
      const start = Date.now();
      const res = http.get(
        `${env.apiBase}/dashboard/resumen/`,
        { headers: hdrs, tags: { endpoint: 'dashboard_resumen', workload: 'reads' } }
      );
      dashboardDuration.add(Date.now() - start);
      check(res, {
        'read dashboard: status 200':       (r) => r.status === 200,
        'read dashboard: tiempo < 1000ms':  (r) => r.timings.duration < 1000,
      });
      if (res.status === 200) totalReads.add(1);
      else                     businessErrors.add(1);
      sleep(1);
    });
  }
}

// ─── Workload: ESCRITURAS (20%) ───────────────────────────────────────────────

export function writesWorkload(data) {
  const { tokens, env } = data;
  const { fixtures }    = env;

  const roll = Math.random();

  if (roll < 0.50) {
    // 50% de las escrituras: registrar un pago
    group('Mixed: registrar pago', () => {
      const hdrs    = authHeaders(tokens.secretary.access, env.tenantHost);
      const mes     = randomItem(MESES_ESCOLARES);
      const payload = generatePaymentPayload(fixtures.studentId, mes, fixtures.anio);
      const start   = Date.now();
      const res     = http.post(
        `${env.apiBase}/payments/`,
        JSON.stringify(payload),
        { headers: hdrs, tags: { endpoint: 'payments_create', workload: 'writes' } }
      );
      paymentRegDuration.add(Date.now() - start);
      const ok = check(res, {
        'write payment: status 201':      (r) => r.status === 201,
        'write payment: tiempo < 500ms':  (r) => r.timings.duration < 500,
      });
      if (ok) totalWrites.add(1);
      else if (res.status !== 400) businessErrors.add(1);  // 400 = duplicado, es esperado
      sleep(1.5);
    });

  } else if (roll < 0.85) {
    // 35% de las escrituras: asistencia masiva
    group('Mixed: asistencia masiva', () => {
      const hdrs    = authHeaders(tokens.teacher.access, env.tenantHost);
      const fecha   = new Date().toISOString().split('T')[0];
      const payload = generateBulkAttendancePayload(MOCK_STUDENT_IDS, fecha);
      const start   = Date.now();
      const res     = http.post(
        `${env.apiBase}/attendance/registro-masivo/`,
        JSON.stringify(payload),
        { headers: hdrs, tags: { endpoint: 'attendance_bulk', workload: 'writes' } }
      );
      bulkAttendanceDuration.add(Date.now() - start);
      const ok = check(res, {
        'write attendance: status 2xx':      (r) => r.status >= 200 && r.status < 300,
        'write attendance: tiempo < 2000ms': (r) => r.timings.duration < 2000,
      });
      if (ok) totalWrites.add(1);
      else    businessErrors.add(1);
      sleep(2);
    });

  } else {
    // 15% de las escrituras: crear alumno
    group('Mixed: crear alumno', () => {
      const hdrs    = authHeaders(tokens.secretary.access, env.tenantHost);
      const payload = generateStudentData();
      const res     = http.post(
        `${env.apiBase}/students/`,
        JSON.stringify(payload),
        { headers: hdrs, tags: { endpoint: 'students_create', workload: 'writes' } }
      );
      const ok = check(res, {
        'write student: status 201':      (r) => r.status === 201,
        'write student: tiempo < 500ms':  (r) => r.timings.duration < 500,
      });
      if (ok) totalWrites.add(1);
      else    businessErrors.add(1);
      sleep(1.5);
    });
  }
}

// ─── Workload: REPORTES (10%) ─────────────────────────────────────────────────

export function reportsWorkload(data) {
  const { tokens, env } = data;
  const { fixtures }    = env;
  const hdrsBin = authHeadersBinary(tokens.director.access, env.tenantHost);
  const hdrs    = authHeaders(tokens.director.access, env.tenantHost);

  group('Mixed: reporte pesado', () => {
    const roll = Math.random();

    if (roll < 0.60) {
      // 60%: Excel de morosidad
      const start = Date.now();
      const res   = http.get(
        `${env.apiBase}/reports/morosidad-excel/`,
        { headers: hdrsBin, tags: { endpoint: 'reports_morosidad_excel', workload: 'reports' }, timeout: '30s' }
      );
      reportGenerationDuration.add(Date.now() - start);
      const ok = check(res, {
        'report excel: status 200':      (r) => r.status === 200,
        'report excel: tiempo < 3000ms': (r) => r.timings.duration < 3000,
      });
      if (ok) totalReports.add(1);
      else    businessErrors.add(1);
      sleep(5);

    } else {
      // 40%: cashflow completo del mes
      const res = http.get(
        `${env.apiBase}/cashflow/cash-transactions/?mes=${fixtures.mes}&anio=${fixtures.anio}`,
        { headers: hdrs, tags: { endpoint: 'cashflow_transactions', workload: 'reports' } }
      );
      check(res, {
        'report cashflow: status 200':     (r) => r.status === 200,
        'report cashflow: tiempo < 800ms': (r) => r.timings.duration < 800,
      });
      if (res.status === 200) totalReports.add(1);
      sleep(3);
    }
  });
}

// ─── Teardown ─────────────────────────────────────────────────────────────────

export function teardown(data) {
  console.log(`Mixed Realistic test finalizado. Ambiente: ${data.env.envName}`);
  console.log('');
  console.log('Metricas clave para evaluar:');
  console.log('  - mixed_reads_total / mixed_writes_total / mixed_reports_total: ratio real de operaciones');
  console.log('  - business_error_rate: errores de negocio (no solo HTTP errors)');
  console.log('  - http_reqs rate: throughput total alcanzado');
  console.log('  - dashboard_duration p95: impacto de las lecturas costosas');
  console.log('  - bulk_attendance_duration p95: impacto de las escrituras masivas');
  console.log('');
  console.log('NOTA: Limpiar datos de prueba generados (prefijo PERF_).');
}
