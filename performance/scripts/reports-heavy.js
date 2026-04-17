/**
 * reports-heavy.js - TEST ESPECIFICO: Reportes Excel y Operaciones Pesadas
 * ──────────────────────────────────────────────────────────────────────────
 * Objetivo: Evaluar el comportamiento del sistema cuando multiples usuarios
 *           descargan reportes Excel concurrentemente o ejecutan queries pesadas.
 *
 * Escenario critico para Railway:
 *   - openpyxl genera el Excel en memoria de Python
 *   - Si 5 usuarios descargan el reporte al mismo tiempo, el uso de RAM
 *     puede superar los 512MB y Railway reinicia el dyno (OOM kill)
 *   - El preview de migracion hace queries costosas de JOIN
 *
 * Endpoints testeados:
 *   - GET  /api/v1/reports/morosidad-excel/    (Excel en memoria)
 *   - POST /api/v1/migrations/preview/         (query pesada sin escribir)
 *   - GET  /api/v1/cashflow/cash-transactions/ (filtrado con agregaciones)
 *   - GET  /api/v1/dashboard/resumen/          (multiples queries en una)
 *
 * Configuracion: ramp hasta 10 VUs concurrentes descargando Excel
 * Ejecutar: k6 run --env ENV=staging scripts/reports-heavy.js
 */

import http   from 'k6/http';
import { sleep, check, group } from 'k6';
import { Counter, Rate, Trend, Gauge } from 'k6/metrics';

import { getEnvConfig }       from '../config/environments.js';
import { REPORTS_THRESHOLDS } from '../config/thresholds.js';
import { getMultiRoleTokens, authHeaders, authHeadersBinary } from '../helpers/auth.js';
import {
  generateMigrationPreviewPayload,
} from '../helpers/data.js';

// ─── Metricas custom ──────────────────────────────────────────────────────────

const reportDuration         = new Trend('report_generation_duration', true);
const migrationPreviewDuration = new Trend('migration_preview_duration', true);
const dashboardDuration      = new Trend('dashboard_duration', true);

const reportsGenerated       = new Counter('reports_generated_total');
const reportsFailed          = new Counter('reports_failed_total');
const reportErrorRate        = new Rate('report_error_rate');

// Gauge para monitorear el tamano de las respuestas (proxy de uso de RAM)
const responseBodySizeKB     = new Gauge('report_response_size_kb');

// ─── Opciones ─────────────────────────────────────────────────────────────────

export const options = {
  stages: [
    { duration: '1m',  target: 2  }, // warm-up: 2 usuarios
    { duration: '2m',  target: 5  }, // carga moderada: 5 usuarios concurrentes
    { duration: '2m',  target: 8  }, // carga alta: 8 usuarios - zona de riesgo en Railway
    { duration: '2m',  target: 10 }, // maximo probable antes de OOM
    { duration: '1m',  target: 0  }, // recovery
  ],
  thresholds: REPORTS_THRESHOLDS,
  tags: { testType: 'reports-heavy', project: 'saas-corem' },
};

// ─── Setup ───────────────────────────────────────────────────────────────────

export function setup() {
  const env    = getEnvConfig();
  const tokens = getMultiRoleTokens(env.apiBase, env.tenantHost, {
    director: env.credentials.director,
    admin:    env.credentials.admin,
  });
  return { tokens, env };
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function (data) {
  const { tokens, env } = data;
  const { fixtures }    = env;

  // Distribucion de carga entre endpoints pesados
  const roll = Math.random();

  if (roll < 0.45) {
    runMorosidadExcel(tokens.director.access, env);
  } else if (roll < 0.65) {
    runMigrationPreview(tokens.admin.access, env, fixtures);
  } else if (roll < 0.85) {
    runDashboardAndCashflow(tokens.director.access, env, fixtures);
  } else {
    runConcurrentHeavyBatch(tokens.director.access, env, fixtures);
  }
}

// ─── Descarga de Excel de morosidad ──────────────────────────────────────────

function runMorosidadExcel(accessToken, env) {
  const hdrs = authHeadersBinary(accessToken, env.tenantHost);

  group('Reports: morosidad Excel', () => {
    const start = Date.now();
    const res   = http.get(
      `${env.apiBase}/reports/morosidad-excel/`,
      {
        headers: hdrs,
        tags:    { endpoint: 'reports_morosidad_excel' },
        timeout: '30s',  // timeout generoso: el Excel puede tardar en generarse
      }
    );
    const duration = Date.now() - start;
    reportDuration.add(duration);

    const ok = check(res, {
      'excel morosidad: status 200':      (r) => r.status === 200,
      'excel morosidad: tiempo < 3000ms': (r) => r.timings.duration < 3000,
      'excel morosidad: no 503':          (r) => r.status !== 503,
      'excel morosidad: no 500':          (r) => r.status !== 500,
      'excel morosidad: tiene contenido': (r) => r.body.length > 100,
    });

    if (ok) {
      reportsGenerated.add(1);
      reportErrorRate.add(0);
      // Registrar tamano de la respuesta (indicador de uso de RAM)
      responseBodySizeKB.add(Math.round(res.body.length / 1024));
    } else {
      reportsFailed.add(1);
      reportErrorRate.add(1);
      // Loguear el error para diagnostico
      if (res.status === 503) {
        console.warn(`[VU ${__VU}] Railway 503 en reports/morosidad-excel/ - posible OOM kill`);
      }
    }

    // Think time largo: descarga de reportes no es continua
    sleep(Math.random() * 3 + 2);
  });
}

// ─── Preview de migracion academica ──────────────────────────────────────────

function runMigrationPreview(accessToken, env, fixtures) {
  const hdrs    = authHeaders(accessToken, env.tenantHost);
  const payload = generateMigrationPreviewPayload(fixtures.academicYearId);

  group('Reports: preview migracion academica', () => {
    const start = Date.now();
    const res   = http.post(
      `${env.apiBase}/migrations/preview/`,
      JSON.stringify(payload),
      {
        headers: hdrs,
        tags:    { endpoint: 'migrations_preview' },
        timeout: '30s',
      }
    );
    migrationPreviewDuration.add(Date.now() - start);

    check(res, {
      'migration preview: status 200':       (r) => r.status === 200,
      'migration preview: tiempo < 5000ms':  (r) => r.timings.duration < 5000,
      'migration preview: no 500':           (r) => r.status !== 500,
      'migration preview: tiene datos':      (r) => r.body.length > 10,
    });
    if (res.status >= 500) reportErrorRate.add(1); else reportErrorRate.add(0);

    sleep(3);
  });
}

// ─── Dashboard + Cashflow combinados ─────────────────────────────────────────

function runDashboardAndCashflow(accessToken, env, fixtures) {
  const hdrs = authHeaders(accessToken, env.tenantHost);

  group('Reports: dashboard y cashflow combinados', () => {
    // Dashboard
    const startDash = Date.now();
    const dashboard = http.get(
      `${env.apiBase}/dashboard/resumen/`,
      { headers: hdrs, tags: { endpoint: 'dashboard_resumen' } }
    );
    dashboardDuration.add(Date.now() - startDash);

    check(dashboard, {
      'dashboard: status 200':       (r) => r.status === 200,
      'dashboard: tiempo < 1000ms':  (r) => r.timings.duration < 1000,
    });
    sleep(1);

    // Cashflow con filtros
    const cashflow = http.get(
      `${env.apiBase}/cashflow/cash-transactions/?mes=${fixtures.mes}&anio=${fixtures.anio}`,
      { headers: hdrs, tags: { endpoint: 'cashflow_transactions' } }
    );
    check(cashflow, {
      'cashflow: status 200':      (r) => r.status === 200,
      'cashflow: tiempo < 800ms':  (r) => r.timings.duration < 800,
    });

    if (dashboard.status !== 200 || cashflow.status !== 200) {
      reportErrorRate.add(1);
    } else {
      reportErrorRate.add(0);
    }
    sleep(2);
  });
}

// ─── Batch pesado concurrente ─────────────────────────────────────────────────

function runConcurrentHeavyBatch(accessToken, env, fixtures) {
  const hdrs    = authHeaders(accessToken, env.tenantHost);
  const hdrsBin = authHeadersBinary(accessToken, env.tenantHost);

  group('Reports: batch pesado concurrente', () => {
    // Todas las requests pesadas al mismo tiempo (worst case)
    const responses = http.batch([
      ['GET', `${env.apiBase}/dashboard/resumen/`,
        null, { headers: hdrs, tags: { endpoint: 'dashboard_batch' }, timeout: '15s' }],
      ['GET', `${env.apiBase}/cashflow/cash-transactions/?mes=${fixtures.mes}&anio=${fixtures.anio}`,
        null, { headers: hdrs, tags: { endpoint: 'cashflow_batch' }, timeout: '15s' }],
      ['GET', `${env.apiBase}/payments/?estado=VENCIDO&page_size=100`,
        null, { headers: hdrs, tags: { endpoint: 'payments_batch' }, timeout: '15s' }],
    ]);

    responses.forEach((res, i) => {
      const endpoints = ['dashboard', 'cashflow', 'payments_morosos'];
      check(res, {
        [`batch ${endpoints[i]}: responde`]:    (r) => r.status < 500,
        [`batch ${endpoints[i]}: no timeout`]:  (r) => r.timings.duration < 10000,
      });
      if (res.status >= 500) reportErrorRate.add(1);
    });

    sleep(3);
  });
}

// ─── Teardown ─────────────────────────────────────────────────────────────────

export function teardown(data) {
  console.log(`Reports Heavy test finalizado. Ambiente: ${data.env.envName}`);
  console.log('');
  console.log('Indicadores criticos para Railway (512MB RAM):');
  console.log('  - report_response_size_kb: tamano promedio de los Excel generados');
  console.log('  - report_generation_duration p95: tiempo de generacion bajo carga');
  console.log('  - Errores 503: Railway reinicio el dyno (OOM)');
  console.log('');
  console.log('Si hay errores 503 con 5+ VUs concurrentes descargando Excel:');
  console.log('  Opcion A: Generar Excel de forma asincrona (Celery + Redis)');
  console.log('  Opcion B: Streaming de la respuesta (no cargar todo en RAM)');
  console.log('  Opcion C: Cache del Excel por N minutos (no regenerar si no hubo cambios)');
}
