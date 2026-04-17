/**
 * soak.js - SOAK TEST
 * ────────────────────
 * Objetivo: Detectar problemas de memoria, resource leaks y degradacion gradual
 *           en SAAS COREM desplegado en Railway.
 *
 * Lo que se busca detectar:
 *   1. Memory leak en Django (objetos no liberados, queries sin cerrar)
 *   2. Connection pool exhaustion de PostgreSQL (conexiones no devueltas)
 *   3. Redis cache fill (keys sin TTL que llenan la memoria)
 *   4. Degradacion gradual del p95 response time (p.ej. 300ms -> 800ms en 30 min)
 *   5. File descriptor leaks (por generacion repetida de Excel)
 *
 * Configuracion: 15 VUs, 30 minutos de carga sostenida
 * Duracion total: 5 min ramp + 30 min soak + 2 min ramp down = ~37 min
 *
 * NOTA: Para detectar degradacion gradual, exportar metricas a InfluxDB/Grafana
 * y observar la tendencia del p95 a lo largo del tiempo.
 *
 * Ejecutar: k6 run --env ENV=staging scripts/soak.js
 *           k6 run --env ENV=staging --out influxdb=http://localhost:8086/k6 scripts/soak.js
 */

import http   from 'k6/http';
import { sleep, check, group } from 'k6';
import { Counter, Rate, Trend, Gauge } from 'k6/metrics';

import { getEnvConfig }     from '../config/environments.js';
import { SOAK_THRESHOLDS }  from '../config/thresholds.js';
import { getMultiRoleTokens, authHeaders, refreshAccessToken, authHeadersBinary } from '../helpers/auth.js';
import {
  generateBulkAttendancePayload,
  generatePaymentPayload,
  MOCK_STUDENT_IDS,
  randomItem,
  MESES_ESCOLARES,
} from '../helpers/data.js';

// ─── Metricas custom ──────────────────────────────────────────────────────────

const dashboardDuration        = new Trend('dashboard_duration', true);
const reportGenerationDuration = new Trend('report_generation_duration', true);
const bulkAttendanceDuration   = new Trend('bulk_attendance_duration', true);
const paymentDuration          = new Trend('payment_registration_duration', true);

// Gauge para detectar degradacion: si el valor sube con el tiempo, hay un leak
const currentResponseTime      = new Gauge('current_avg_response_time');

const paymentsTotal            = new Counter('soak_payments_total');
const reportsTotal             = new Counter('soak_reports_total');
const attendanceTotal          = new Counter('soak_attendance_total');
const errorRate                = new Rate('soak_error_rate');

// ─── Opciones ─────────────────────────────────────────────────────────────────

export const options = {
  stages: [
    { duration: '5m',  target: 15 },   // ramp up
    { duration: '30m', target: 15 },   // soak sostenido
    { duration: '2m',  target: 0  },   // ramp down
  ],
  thresholds: SOAK_THRESHOLDS,
  tags: { testType: 'soak', project: 'saas-corem' },
};

// ─── Setup ───────────────────────────────────────────────────────────────────

export function setup() {
  const env    = getEnvConfig();
  const tokens = getMultiRoleTokens(env.apiBase, env.tenantHost, {
    secretary: env.credentials.secretary,
    director:  env.credentials.director,
    teacher:   env.credentials.teacher,
  });
  return { tokens, env, startTime: Date.now() };
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function (data) {
  const { tokens, env } = data;
  const { fixtures }    = env;

  // Distribucion de trabajo similar al load test pero sostenida
  const roll = Math.random();

  if (roll < 0.40) {
    runSoakReadOps(tokens.secretary.access, env, fixtures);
  } else if (roll < 0.65) {
    runSoakWriteOps(tokens.secretary.access, env, fixtures);
  } else if (roll < 0.80) {
    runSoakAttendance(tokens.teacher.access, env, fixtures);
  } else if (roll < 0.93) {
    runSoakDashboard(tokens.director.access, env, fixtures);
  } else {
    // El 7% genera Excel: detectar file descriptor leaks
    runSoakExcelGeneration(tokens.director.access, env);
  }
}

// ─── Operaciones de lectura sostenida ────────────────────────────────────────

function runSoakReadOps(accessToken, env, fixtures) {
  const hdrs = authHeaders(accessToken, env.tenantHost);

  group('Soak: lecturas continuas', () => {
    const t0 = Date.now();

    const students = http.get(
      `${env.apiBase}/students/?page=1&page_size=25`,
      { headers: hdrs, tags: { endpoint: 'students_list', role: 'secretary' } }
    );
    check(students, {
      'soak students: status 200':      (r) => r.status === 200,
      'soak students: tiempo < 500ms':  (r) => r.timings.duration < 500,
    });
    if (students.status !== 200) errorRate.add(1);
    else                          errorRate.add(0);
    sleep(1);

    const payments = http.get(
      `${env.apiBase}/payments/?page=1&page_size=25`,
      { headers: hdrs, tags: { endpoint: 'payments_list', role: 'secretary' } }
    );
    check(payments, {
      'soak payments: status 200':      (r) => r.status === 200,
      'soak payments: tiempo < 500ms':  (r) => r.timings.duration < 500,
    });
    if (payments.status !== 200) errorRate.add(1);
    else                          errorRate.add(0);
    sleep(1);

    const morosos = http.get(
      `${env.apiBase}/payments/?estado=VENCIDO`,
      { headers: hdrs, tags: { endpoint: 'payments_morosos', role: 'secretary' } }
    );
    check(morosos, { 'soak morosos: status 200': (r) => r.status === 200 });
    sleep(1);

    // Actualizar gauge de tiempo de respuesta (indicador de degradacion)
    const avgDuration = (students.timings.duration + payments.timings.duration) / 2;
    currentResponseTime.add(avgDuration);

    sleep(2);
  });
}

// ─── Escrituras sostenidas (detectar connection leaks) ───────────────────────

function runSoakWriteOps(accessToken, env, fixtures) {
  const hdrs = authHeaders(accessToken, env.tenantHost);

  group('Soak: escrituras continuas', () => {
    const mes     = randomItem(MESES_ESCOLARES);
    const payload = generatePaymentPayload(fixtures.studentId, mes, fixtures.anio);
    const start   = Date.now();
    const res     = http.post(
      `${env.apiBase}/payments/`,
      JSON.stringify(payload),
      { headers: hdrs, tags: { endpoint: 'payments_create', role: 'secretary' } }
    );
    paymentDuration.add(Date.now() - start);

    const ok = check(res, {
      'soak pago: status 201':       (r) => r.status === 201,
      'soak pago: tiempo < 500ms':   (r) => r.timings.duration < 500,
      'soak pago: tiene id':         (r) => r.json('id') !== undefined,
    });
    if (ok) paymentsTotal.add(1);
    else    errorRate.add(1);

    sleep(2);
  });
}

// ─── Asistencia masiva sostenida ──────────────────────────────────────────────

function runSoakAttendance(accessToken, env, fixtures) {
  const hdrs = authHeaders(accessToken, env.tenantHost);

  group('Soak: asistencia masiva continua', () => {
    const fecha   = new Date().toISOString().split('T')[0];
    const payload = generateBulkAttendancePayload(MOCK_STUDENT_IDS, fecha);
    const start   = Date.now();
    const res     = http.post(
      `${env.apiBase}/attendance/registro-masivo/`,
      JSON.stringify(payload),
      { headers: hdrs, tags: { endpoint: 'attendance_bulk', role: 'teacher' } }
    );
    bulkAttendanceDuration.add(Date.now() - start);

    const ok = check(res, {
      'soak asistencia: status 2xx':       (r) => r.status >= 200 && r.status < 300,
      'soak asistencia: tiempo < 2000ms':  (r) => r.timings.duration < 2000,
    });
    if (ok) attendanceTotal.add(MOCK_STUDENT_IDS.length);
    else    errorRate.add(1);

    sleep(3);
  });
}

// ─── Dashboard sostenido ──────────────────────────────────────────────────────

function runSoakDashboard(accessToken, env, fixtures) {
  const hdrs = authHeaders(accessToken, env.tenantHost);

  group('Soak: dashboard continuo', () => {
    const start = Date.now();
    const res   = http.get(
      `${env.apiBase}/dashboard/resumen/`,
      { headers: hdrs, tags: { endpoint: 'dashboard_resumen', role: 'director' } }
    );
    dashboardDuration.add(Date.now() - start);

    check(res, {
      'soak dashboard: status 200':       (r) => r.status === 200,
      'soak dashboard: tiempo < 1000ms':  (r) => r.timings.duration < 1000,
    });
    if (res.status !== 200) errorRate.add(1);
    else                     errorRate.add(0);

    // Cashflow
    const cash = http.get(
      `${env.apiBase}/cashflow/cash-transactions/?mes=${fixtures.mes}&anio=${fixtures.anio}`,
      { headers: hdrs, tags: { endpoint: 'cashflow_transactions', role: 'director' } }
    );
    check(cash, { 'soak cashflow: status 200': (r) => r.status === 200 });

    sleep(3);
  });
}

// ─── Generacion de Excel sostenida (detectar file/memory leaks) ──────────────

function runSoakExcelGeneration(accessToken, env) {
  const hdrs = authHeadersBinary(accessToken, env.tenantHost);

  group('Soak: generacion Excel repetida', () => {
    const start = Date.now();
    const res   = http.get(
      `${env.apiBase}/reports/morosidad-excel/`,
      { headers: hdrs, tags: { endpoint: 'reports_morosidad_excel', role: 'director' } }
    );
    reportGenerationDuration.add(Date.now() - start);

    const ok = check(res, {
      'soak excel: status 200':       (r) => r.status === 200,
      'soak excel: tiempo < 3000ms':  (r) => r.timings.duration < 3000,
      'soak excel: tiene contenido':  (r) => r.body.length > 100,
    });
    if (ok) reportsTotal.add(1);
    else    errorRate.add(1);

    // Think time mayor: la descarga de Excel no es frecuente
    sleep(5);
  });
}

// ─── Teardown ─────────────────────────────────────────────────────────────────

export function teardown(data) {
  const duracionMin = Math.round((Date.now() - data.startTime) / 60000);
  console.log(`Soak test finalizado. Duracion real: ~${duracionMin} minutos`);
  console.log(`Ambiente: ${data.env.envName}`);
  console.log('');
  console.log('Signos de leak a buscar en Grafana:');
  console.log('  - current_avg_response_time: debe ser PLANO durante los 30 minutos');
  console.log('  - dashboard_duration: no debe crecer con el tiempo');
  console.log('  - report_generation_duration: no debe crecer con el tiempo');
  console.log('  - RAM del proceso Django en Railway: debe ser estable');
  console.log('  - Conexiones activas de PostgreSQL: no deben crecer indefinidamente');
  console.log('');
  console.log('NOTA: Eliminar registros con prefijo PERF_ de la BD de prueba.');
}
