/**
 * load.js - LOAD TEST
 * ────────────────────
 * Objetivo: Simular un dia normal de trabajo en el Jardin Garabato.
 *
 * Escenario simulado (un turno tipico de 8hs):
 *   - Secretaria: registra pagos, busca alumnos, gestiona morosidad
 *   - Docentes (2-3): pasan asistencia al inicio del dia, consultan aulas
 *   - Director: revisa dashboard y reportes durante el dia
 *
 * Configuracion:
 *   - Ramp up:    2 min hasta 20 VUs
 *   - Carga:      5 min a 20 VUs (estado estable)
 *   - Ramp down:  1 min hasta 0 VUs
 *   Total: ~8 min
 *
 * 20 VUs es un upper bound realista para un jardin de infancia con 3-5 usuarios
 * simultaneos maximos (secretaria + 2 docentes + director + app movil).
 *
 * Ejecutar: k6 run --env ENV=local scripts/load.js
 */

import http   from 'k6/http';
import { sleep, check, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

import { getEnvConfig }          from '../config/environments.js';
import { LOAD_THRESHOLDS }       from '../config/thresholds.js';
import { getMultiRoleTokens, authHeaders, authHeadersBinary } from '../helpers/auth.js';
import {
  generateStudentData,
  generateBulkAttendancePayload,
  generatePaymentPayload,
  MOCK_STUDENT_IDS,
  randomPagination,
  randomItem,
  MESES_ESCOLARES,
} from '../helpers/data.js';

// ─── Metricas custom de negocio ───────────────────────────────────────────────

const dashboardDuration        = new Trend('dashboard_duration',       true);
const reportGenerationDuration = new Trend('report_generation_duration', true);
const bulkAttendanceDuration   = new Trend('bulk_attendance_duration', true);
const paymentRegDuration       = new Trend('payment_registration_duration', true);

const paymentsRegistered       = new Counter('payments_registered');
const attendanceRecordsSaved   = new Counter('attendance_records_saved');
const reportsGenerated         = new Counter('reports_generated');
const apiErrors                = new Rate('api_errors');

// ─── Opciones ─────────────────────────────────────────────────────────────────

export const options = {
  stages: [
    { duration: '2m', target: 20 },
    { duration: '5m', target: 20 },
    { duration: '1m', target: 0  },
  ],
  thresholds: LOAD_THRESHOLDS,
  tags:       { testType: 'load', project: 'saas-corem' },
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

// ─── VU logic: cada VU ejecuta uno de los perfiles de usuario ────────────────

export default function (data) {
  const { tokens, env } = data;
  const { fixtures }    = env;

  // Distribucion de roles por VU:
  //   VU  1-8  -> secretaria (40%)
  //   VU  9-15 -> docente    (35%)
  //   VU 16-20 -> director   (25%)
  const vuIndex = __VU % 20;

  if (vuIndex <= 8) {
    runSecretaryScenario(tokens.secretary.access, env, fixtures);
  } else if (vuIndex <= 15) {
    runTeacherScenario(tokens.teacher.access, env, fixtures);
  } else {
    runDirectorScenario(tokens.director.access, env, fixtures);
  }
}

// ─── Escenario: Secretaria ────────────────────────────────────────────────────

function runSecretaryScenario(accessToken, env, fixtures) {
  const hdrs = authHeaders(accessToken, env.tenantHost);

  group('Secretaria: busqueda de alumnos', () => {
    const pagination = randomPagination();
    const res = http.get(
      `${env.apiBase}/students/?page=${pagination.page}&page_size=${pagination.page_size}`,
      { headers: hdrs, tags: { endpoint: 'students_list', role: 'secretary' } }
    );
    const ok = check(res, {
      'students list: status 200':       (r) => r.status === 200,
      'students list: tiene resultados': (r) => r.json('count') !== undefined || Array.isArray(r.json()),
    });
    apiErrors.add(!ok ? 1 : 0);
    sleep(1.5);
  });

  group('Secretaria: detalle de alumno', () => {
    const res = http.get(
      `${env.apiBase}/students/${fixtures.studentId}/`,
      { headers: hdrs, tags: { endpoint: 'students_detail', role: 'secretary' } }
    );
    check(res, {
      'students detail: status 200': (r) => r.status === 200,
      'students detail: tiene id':   (r) => r.json('id') !== undefined,
    });
    sleep(1);
  });

  group('Secretaria: listado de pagos', () => {
    const res = http.get(
      `${env.apiBase}/payments/?page=1&page_size=25`,
      { headers: hdrs, tags: { endpoint: 'payments_list', role: 'secretary' } }
    );
    check(res, { 'payments list: status 200': (r) => r.status === 200 });
    sleep(1);
  });

  group('Secretaria: consulta morosidad', () => {
    const res = http.get(
      `${env.apiBase}/payments/?estado=VENCIDO`,
      { headers: hdrs, tags: { endpoint: 'payments_morosos', role: 'secretary' } }
    );
    check(res, { 'payments morosos: status 200': (r) => r.status === 200 });
    sleep(1);
  });

  // Solo el 30% de las iteraciones registra un pago (no todas las visitas terminan en pago)
  if (Math.random() < 0.3) {
    group('Secretaria: registrar pago', () => {
      const mes     = randomItem(MESES_ESCOLARES);
      const payload = generatePaymentPayload(fixtures.studentId, mes, fixtures.anio);
      const start   = Date.now();
      const res     = http.post(
        `${env.apiBase}/payments/`,
        JSON.stringify(payload),
        { headers: hdrs, tags: { endpoint: 'payments_create', role: 'secretary' } }
      );
      paymentRegDuration.add(Date.now() - start);
      const ok = check(res, {
        'registrar pago: status 201':        (r) => r.status === 201,
        'registrar pago: tiene id':          (r) => r.json('id') !== undefined,
        'registrar pago: tiempo < 500ms':    (r) => r.timings.duration < 500,
      });
      if (ok) paymentsRegistered.add(1);
      else    apiErrors.add(1);
      sleep(2);
    });
  }

  sleep(2);
}

// ─── Escenario: Docente ───────────────────────────────────────────────────────

function runTeacherScenario(accessToken, env, fixtures) {
  const hdrs = authHeaders(accessToken, env.tenantHost);

  group('Docente: ver aulas asignadas', () => {
    const res = http.get(
      `${env.apiBase}/classrooms/`,
      { headers: hdrs, tags: { endpoint: 'classrooms_list', role: 'teacher' } }
    );
    check(res, { 'classrooms: status 200': (r) => r.status === 200 });
    sleep(1);
  });

  group('Docente: listado alumnos del aula', () => {
    const res = http.get(
      `${env.apiBase}/students/?classroom=${fixtures.classroomId}&page_size=50`,
      { headers: hdrs, tags: { endpoint: 'students_by_classroom', role: 'teacher' } }
    );
    check(res, { 'alumnos por aula: status 200': (r) => r.status === 200 });
    sleep(2);
  });

  // Solo el 40% de las iteraciones registra asistencia (ocurre una vez al dia por docente)
  if (Math.random() < 0.4) {
    group('Docente: registro masivo de asistencia', () => {
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
        'registro asistencia: status 201 o 200': (r) => r.status === 201 || r.status === 200,
        'registro asistencia: tiempo < 2000ms':  (r) => r.timings.duration < 2000,
      });
      if (ok) attendanceRecordsSaved.add(MOCK_STUDENT_IDS.length);
      else    apiErrors.add(1);
      sleep(3);
    });
  }

  sleep(2);
}

// ─── Escenario: Director ──────────────────────────────────────────────────────

function runDirectorScenario(accessToken, env, fixtures) {
  const hdrs      = authHeaders(accessToken, env.tenantHost);
  const hdrsBin   = authHeadersBinary(accessToken, env.tenantHost);

  group('Director: dashboard KPIs', () => {
    const start = Date.now();
    const res = http.get(
      `${env.apiBase}/dashboard/resumen/`,
      { headers: hdrs, tags: { endpoint: 'dashboard_resumen', role: 'director' } }
    );
    dashboardDuration.add(Date.now() - start);
    check(res, {
      'dashboard: status 200':       (r) => r.status === 200,
      'dashboard: tiempo < 1000ms':  (r) => r.timings.duration < 1000,
    });
    sleep(3);
  });

  group('Director: cashflow del mes', () => {
    const res = http.get(
      `${env.apiBase}/cashflow/cash-transactions/?mes=${fixtures.mes}&anio=${fixtures.anio}`,
      { headers: hdrs, tags: { endpoint: 'cashflow_transactions', role: 'director' } }
    );
    check(res, {
      'cashflow: status 200':     (r) => r.status === 200,
      'cashflow: tiempo < 800ms': (r) => r.timings.duration < 800,
    });
    sleep(2);
  });

  // Solo el 20% de las iteraciones descarga el reporte (operacion pesada, no frecuente)
  if (Math.random() < 0.2) {
    group('Director: reporte morosidad Excel', () => {
      const start = Date.now();
      const res   = http.get(
        `${env.apiBase}/reports/morosidad-excel/`,
        { headers: hdrsBin, tags: { endpoint: 'reports_morosidad_excel', role: 'director' } }
      );
      reportGenerationDuration.add(Date.now() - start);
      const ok = check(res, {
        'reporte excel: status 200':      (r) => r.status === 200,
        'reporte excel: tiempo < 3000ms': (r) => r.timings.duration < 3000,
        'reporte excel: tiene contenido': (r) => r.body.length > 100,
      });
      if (ok) reportsGenerated.add(1);
      else    apiErrors.add(1);
      sleep(4);
    });
  }

  sleep(2);
}

// ─── Teardown ─────────────────────────────────────────────────────────────────

export function teardown(data) {
  console.log(`Load test finalizado. Ambiente: ${data.env.envName}`);
  console.log('NOTA: Eliminar registros con prefijo PERF_ de la BD de prueba.');
}
