/**
 * spike.js - SPIKE TEST
 * ──────────────────────
 * Objetivo: Verificar el comportamiento del sistema ante picos subitos de carga.
 *
 * Escenario real para SAAS COREM:
 *   - Inicio del mes escolar: todos los padres pagan la pension el mismo dia
 *   - La secretaria recibe llamadas y hace consultas intensivas por la manana
 *   - Los docentes pasan asistencia todos al mismo tiempo (apertura de clases 8am)
 *
 * Patron: carga baja (5 VUs) -> pico subito (80 VUs) -> vuelta a normal (5 VUs)
 *         Se repite el pico para verificar que el sistema se recupera consistentemente.
 *
 * Lo que se evalua:
 *   1. El sistema no colapsa durante el pico (no 500/502)
 *   2. Vuelve a tiempos normales despues del pico (recovery)
 *   3. No hay errores despues del pico (no memory leak que cause errores residuales)
 *
 * Duracion total: ~11 min
 * Ejecutar: k6 run --env ENV=staging scripts/spike.js
 */

import http   from 'k6/http';
import { sleep, check, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

import { getEnvConfig }      from '../config/environments.js';
import { SPIKE_THRESHOLDS }  from '../config/thresholds.js';
import { getMultiRoleTokens, authHeaders } from '../helpers/auth.js';
import {
  generateBulkAttendancePayload,
  generatePaymentPayload,
  MOCK_STUDENT_IDS,
  randomItem,
  MESES_ESCOLARES,
} from '../helpers/data.js';

// ─── Metricas custom ──────────────────────────────────────────────────────────

const spikeDuration    = new Trend('spike_response_duration', true);
const recoveryDuration = new Trend('post_spike_duration', true);
const spikeErrors      = new Counter('spike_errors');
const spikeErrorRate   = new Rate('spike_error_rate');

// ─── Opciones ─────────────────────────────────────────────────────────────────

export const options = {
  stages: [
    // Carga baja inicial (simula la noche/madrugada)
    { duration: '1m',  target: 5  },
    // PICO 1: inicio de clases 8am - todos llegan al mismo tiempo
    { duration: '30s', target: 80 },
    { duration: '2m',  target: 80 },
    // Recovery post-pico
    { duration: '30s', target: 5  },
    { duration: '2m',  target: 5  },
    // PICO 2: cierre del mes - pago de pensiones
    { duration: '30s', target: 80 },
    { duration: '2m',  target: 80 },
    // Vuelta a calma
    { duration: '1m',  target: 0  },
  ],
  thresholds: SPIKE_THRESHOLDS,
  tags: { testType: 'spike', project: 'saas-corem' },
};

// ─── Setup ───────────────────────────────────────────────────────────────────

export function setup() {
  const env    = getEnvConfig();
  const tokens = getMultiRoleTokens(env.apiBase, env.tenantHost, {
    secretary: env.credentials.secretary,
    teacher:   env.credentials.teacher,
    director:  env.credentials.director,
  });
  return { tokens, env };
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function (data) {
  const { tokens, env } = data;
  const { fixtures }    = env;

  // Durante el pico todos hacen lo mismo simultaneamente:
  // simula el caso real donde todos abren la app al mismo tiempo
  const vuIndex = __VU % 3;

  if (vuIndex === 0) {
    runSpikeSecretaryOps(tokens.secretary.access, env, fixtures);
  } else if (vuIndex === 1) {
    runSpikeTeacherOps(tokens.teacher.access, env, fixtures);
  } else {
    runSpikeDashboardOps(tokens.director.access, env, fixtures);
  }
}

// ─── Operaciones de secretaria durante el pico ───────────────────────────────

function runSpikeSecretaryOps(accessToken, env, fixtures) {
  const hdrs = authHeaders(accessToken, env.tenantHost);

  group('Spike: secretaria - consultas masivas', () => {
    const start = Date.now();

    // Listado de alumnos (primera operacion del dia)
    const students = http.get(
      `${env.apiBase}/students/?page=1&page_size=25`,
      { headers: hdrs, tags: { endpoint: 'students_list', phase: 'spike' } }
    );
    spikeDuration.add(Date.now() - start);

    const ok = check(students, {
      'spike students: responde':       (r) => r.status < 500,
      'spike students: no timeout':     (r) => r.timings.duration < 10000,
    });
    if (!ok) {
      spikeErrors.add(1);
      spikeErrorRate.add(1);
    } else {
      spikeErrorRate.add(0);
    }
    sleep(0.5);

    // Morosos del mes
    const morosos = http.get(
      `${env.apiBase}/payments/?estado=VENCIDO`,
      { headers: hdrs, tags: { endpoint: 'payments_morosos', phase: 'spike' } }
    );
    check(morosos, {
      'spike morosos: responde': (r) => r.status < 500,
    });
    sleep(0.5);

    // Registro de pago (no todos, 50% de los VUs)
    if (Math.random() < 0.5) {
      const mes     = randomItem(MESES_ESCOLARES);
      const payload = generatePaymentPayload(fixtures.studentId, mes, fixtures.anio);
      const payment = http.post(
        `${env.apiBase}/payments/`,
        JSON.stringify(payload),
        { headers: hdrs, tags: { endpoint: 'payments_create', phase: 'spike' } }
      );
      check(payment, {
        'spike pago: status 201 o 400': (r) => r.status === 201 || r.status === 400,
        'spike pago: no 500':           (r) => r.status !== 500,
      });
      if (payment.status >= 500) spikeErrors.add(1);
    }

    sleep(1);
  });
}

// ─── Operaciones de docente durante el pico ──────────────────────────────────

function runSpikeTeacherOps(accessToken, env, fixtures) {
  const hdrs = authHeaders(accessToken, env.tenantHost);

  group('Spike: docente - apertura de aula', () => {
    // Ver alumnos del aula
    const start   = Date.now();
    const students = http.get(
      `${env.apiBase}/students/?classroom=${fixtures.classroomId}&page_size=50`,
      { headers: hdrs, tags: { endpoint: 'students_by_classroom', phase: 'spike' } }
    );
    spikeDuration.add(Date.now() - start);

    check(students, {
      'spike alumnos aula: responde': (r) => r.status < 500,
      'spike alumnos aula: no hang':  (r) => r.timings.duration < 10000,
    });
    sleep(1);

    // Registro masivo de asistencia (todos los docentes al mismo tiempo = spike real)
    const fecha   = new Date().toISOString().split('T')[0];
    const payload = generateBulkAttendancePayload(MOCK_STUDENT_IDS, fecha);
    const attend  = http.post(
      `${env.apiBase}/attendance/registro-masivo/`,
      JSON.stringify(payload),
      { headers: hdrs, tags: { endpoint: 'attendance_bulk', phase: 'spike' } }
    );
    check(attend, {
      'spike asistencia: responde':   (r) => r.status < 500,
      'spike asistencia: no timeout': (r) => r.timings.duration < 15000,
    });
    if (attend.status >= 500) spikeErrors.add(1);
    sleep(1);
  });
}

// ─── Dashboard durante el pico ────────────────────────────────────────────────

function runSpikeDashboardOps(accessToken, env, fixtures) {
  const hdrs = authHeaders(accessToken, env.tenantHost);

  group('Spike: director - revisa en pico', () => {
    const start = Date.now();
    const res   = http.get(
      `${env.apiBase}/dashboard/resumen/`,
      { headers: hdrs, tags: { endpoint: 'dashboard_resumen', phase: 'spike' } }
    );
    recoveryDuration.add(Date.now() - start);

    const ok = check(res, {
      'spike dashboard: responde':    (r) => r.status < 500,
      'spike dashboard: no colapsa':  (r) => r.status !== 500,
    });
    if (!ok) spikeErrors.add(1);

    sleep(2);
  });
}

// ─── Teardown ─────────────────────────────────────────────────────────────────

export function teardown(data) {
  console.log(`Spike test finalizado. Ambiente: ${data.env.envName}`);
  console.log(
    'Clave a evaluar: comparar spike_response_duration vs post_spike_duration. ' +
    'Si post_spike_duration > 2x spike_response_duration, el sistema no se recupero correctamente.'
  );
}
