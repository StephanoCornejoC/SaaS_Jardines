/**
 * smoke.js - SMOKE TEST
 * ─────────────────────
 * Objetivo: Verificar que todos los endpoints criticos responden correctamente
 *           bajo carga minima (1 VU). Es el test de "semaforo en verde" antes
 *           de ejecutar load o stress.
 *
 * Configuracion: 1 VU, 30 segundos
 * Ejecutar:      k6 run --env ENV=local scripts/smoke.js
 *
 * REGLA: Si el smoke test falla, NO ejecutar load/stress test.
 */

import http   from 'k6/http';
import { sleep, check, group } from 'k6';
import { Trend } from 'k6/metrics';

import { getEnvConfig }          from '../config/environments.js';
import { SMOKE_THRESHOLDS }      from '../config/thresholds.js';
import { getMultiRoleTokens, authHeaders, authHeadersBinary } from '../helpers/auth.js';

// ─── Metricas custom ──────────────────────────────────────────────────────────

const dashboardDuration = new Trend('dashboard_duration', true);
const authDuration      = new Trend('auth_duration', true);

// ─── Opciones ─────────────────────────────────────────────────────────────────

export const options = {
  vus:        1,
  duration:   '30s',
  thresholds: SMOKE_THRESHOLDS,
  tags:       { testType: 'smoke', project: 'saas-corem' },
};

// ─── Setup: autenticacion una sola vez ───────────────────────────────────────

export function setup() {
  const env    = getEnvConfig();
  const start  = Date.now();
  const tokens = getMultiRoleTokens(env.apiBase, env.tenantHost, {
    secretary: env.credentials.secretary,
    director:  env.credentials.director,
    teacher:   env.credentials.teacher,
  });
  authDuration.add(Date.now() - start);
  return { tokens, env };
}

// ─── Escenario principal ─────────────────────────────────────────────────────

export default function (data) {
  const { tokens, env } = data;
  const hdrsSecretary   = authHeaders(tokens.secretary.access, env.tenantHost);
  const hdrsDirector    = authHeaders(tokens.director.access,  env.tenantHost);
  const hdrsTeacher     = authHeaders(tokens.teacher.access,   env.tenantHost);
  const { fixtures }    = env;

  // ── 1. Auth: refresh token ────────────────────────────────────────────────
  group('Auth', () => {
    const res = http.post(
      `${env.apiBase}/auth/token/refresh/`,
      JSON.stringify({ refresh: tokens.secretary.refresh }),
      { headers: hdrsSecretary, tags: { endpoint: 'auth_refresh', role: 'secretary' } }
    );
    check(res, {
      'refresh token: status 200':        (r) => r.status === 200,
      'refresh token: nuevo access token': (r) => !!r.json('access'),
    });
    sleep(0.5);
  });

  // ── 2. Alumnos: listado y detalle ─────────────────────────────────────────
  group('Estudiantes', () => {
    const list = http.get(
      `${env.apiBase}/students/?page=1&page_size=25`,
      { headers: hdrsSecretary, tags: { endpoint: 'students_list', role: 'secretary' } }
    );
    check(list, {
      'students list: status 200':          (r) => r.status === 200,
      'students list: tiene resultados':    (r) => r.json('results') !== undefined || r.json('count') !== undefined,
      'students list: tiempo < 500ms':      (r) => r.timings.duration < 500,
    });
    sleep(0.5);

    const detail = http.get(
      `${env.apiBase}/students/${fixtures.studentId}/`,
      { headers: hdrsSecretary, tags: { endpoint: 'students_detail', role: 'secretary' } }
    );
    check(detail, {
      'students detail: status 200':   (r) => r.status === 200,
      'students detail: tiene id':     (r) => r.json('id') !== undefined,
      'students detail: tiempo < 500ms': (r) => r.timings.duration < 500,
    });
    sleep(0.5);
  });

  // ── 3. Aulas ──────────────────────────────────────────────────────────────
  group('Aulas', () => {
    const res = http.get(
      `${env.apiBase}/classrooms/`,
      { headers: hdrsTeacher, tags: { endpoint: 'classrooms_list', role: 'teacher' } }
    );
    check(res, {
      'classrooms: status 200':       (r) => r.status === 200,
      'classrooms: tiempo < 500ms':   (r) => r.timings.duration < 500,
    });
    sleep(0.5);
  });

  // ── 4. Pagos ──────────────────────────────────────────────────────────────
  group('Pagos', () => {
    const list = http.get(
      `${env.apiBase}/payments/?page=1&page_size=25`,
      { headers: hdrsSecretary, tags: { endpoint: 'payments_list', role: 'secretary' } }
    );
    check(list, {
      'payments list: status 200':     (r) => r.status === 200,
      'payments list: tiempo < 500ms': (r) => r.timings.duration < 500,
    });
    sleep(0.5);

    const morosos = http.get(
      `${env.apiBase}/payments/?estado=VENCIDO`,
      { headers: hdrsSecretary, tags: { endpoint: 'payments_morosos', role: 'secretary' } }
    );
    check(morosos, {
      'payments morosos: status 200':     (r) => r.status === 200,
      'payments morosos: tiempo < 500ms': (r) => r.timings.duration < 500,
    });
    sleep(0.5);
  });

  // ── 5. Dashboard ──────────────────────────────────────────────────────────
  group('Dashboard', () => {
    const start = Date.now();
    const res = http.get(
      `${env.apiBase}/dashboard/resumen/`,
      { headers: hdrsDirector, tags: { endpoint: 'dashboard_resumen', role: 'director' } }
    );
    dashboardDuration.add(Date.now() - start);
    check(res, {
      'dashboard: status 200':        (r) => r.status === 200,
      'dashboard: tiempo < 1000ms':   (r) => r.timings.duration < 1000,
      'dashboard: tiene datos':       (r) => r.body.length > 10,
    });
    sleep(0.5);
  });

  // ── 6. Cashflow ───────────────────────────────────────────────────────────
  group('Cashflow', () => {
    const res = http.get(
      `${env.apiBase}/cashflow/cash-transactions/?mes=${fixtures.mes}&anio=${fixtures.anio}`,
      { headers: hdrsDirector, tags: { endpoint: 'cashflow_transactions', role: 'director' } }
    );
    check(res, {
      'cashflow: status 200':       (r) => r.status === 200,
      'cashflow: tiempo < 800ms':   (r) => r.timings.duration < 800,
    });
    sleep(0.5);
  });

  // ── 7. Reporte morosidad Excel ────────────────────────────────────────────
  group('Reportes', () => {
    const hdrs = authHeadersBinary(tokens.director.access, env.tenantHost);
    const res  = http.get(
      `${env.apiBase}/reports/morosidad-excel/`,
      { headers: hdrs, tags: { endpoint: 'reports_morosidad_excel', role: 'director' } }
    );
    check(res, {
      'morosidad excel: status 200':      (r) => r.status === 200,
      'morosidad excel: tiempo < 3000ms': (r) => r.timings.duration < 3000,
      'morosidad excel: tiene contenido': (r) => r.body.length > 100,
    });
    sleep(1);
  });

  sleep(1);
}

// ─── Teardown ─────────────────────────────────────────────────────────────────

export function teardown(data) {
  // El smoke test no crea datos, no hay nada que limpiar.
  console.log(`Smoke test completado. Ambiente: ${data.env.envName}`);
}
