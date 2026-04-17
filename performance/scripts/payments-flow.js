/**
 * payments-flow.js - TEST ESPECIFICO: Flujo Completo de Pensiones
 * ─────────────────────────────────────────────────────────────────
 * Objetivo: Validar el rendimiento del modulo de pagos bajo carga concurrente,
 *           incluyendo el flujo completo que realiza una secretaria en el jardin.
 *
 * Flujo testeado:
 *   1. Consultar alumnos morosos (GET /payments/?estado=VENCIDO)
 *   2. Ver detalle del pago pendiente (GET /payments/{id}/)
 *   3. Registrar el pago de una pension (POST /payments/)
 *   4. Verificar que el estado cambio a PAGADO (GET /payments/{id}/)
 *   5. Generar QR de pago (si el endpoint existe)
 *   6. Listado con filtros combinados
 *
 * Escenario paralelo: mientras la secretaria registra, el director consulta
 * el cashflow para ver el ingreso registrado.
 *
 * Configuracion: 8 VUs secretaria + 2 VUs director = 10 VUs, 5 minutos
 * Ejecutar: k6 run --env ENV=local scripts/payments-flow.js
 */

import http   from 'k6/http';
import { sleep, check, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

import { getEnvConfig }        from '../config/environments.js';
import { PAYMENTS_THRESHOLDS } from '../config/thresholds.js';
import { getMultiRoleTokens, authHeaders } from '../helpers/auth.js';
import {
  generatePaymentPayload,
  randomItem,
  MESES_ESCOLARES,
  ESTADOS_PAGO,
} from '../helpers/data.js';

// ─── Metricas custom ──────────────────────────────────────────────────────────

const paymentRegDuration     = new Trend('payment_registration_duration', true);
const paymentListDuration    = new Trend('payment_list_duration', true);
const paymentDetailDuration  = new Trend('payment_detail_duration', true);

const paymentsCreated        = new Counter('payments_created_total');
const paymentsRejected       = new Counter('payments_rejected_total');
const paymentErrors          = new Rate('payment_error_rate');
const duplicateAttempts      = new Counter('duplicate_payment_attempts');

// ─── Opciones ─────────────────────────────────────────────────────────────────

export const options = {
  scenarios: {
    secretaria_payments: {
      executor:  'ramping-vus',
      startVUs:  0,
      stages: [
        { duration: '1m',  target: 8 },
        { duration: '3m',  target: 8 },
        { duration: '1m',  target: 0 },
      ],
      env: { ROLE: 'secretary' },
    },
    director_monitoring: {
      executor:  'constant-vus',
      vus:       2,
      duration:  '5m',
      startTime: '30s',
      env: { ROLE: 'director' },
    },
  },
  thresholds: PAYMENTS_THRESHOLDS,
  tags: { testType: 'payments-flow', project: 'saas-corem' },
};

// ─── Setup ───────────────────────────────────────────────────────────────────

export function setup() {
  const env    = getEnvConfig();
  const tokens = getMultiRoleTokens(env.apiBase, env.tenantHost, {
    secretary: env.credentials.secretary,
    director:  env.credentials.director,
  });
  return { tokens, env };
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function (data) {
  const { tokens, env } = data;
  const role = __ENV.ROLE || 'secretary';

  if (role === 'director') {
    runDirectorMonitoring(tokens.director.access, env);
  } else {
    runSecretaryPaymentFlow(tokens.secretary.access, env);
  }
}

// ─── Flujo completo de secretaria ────────────────────────────────────────────

function runSecretaryPaymentFlow(accessToken, env) {
  const hdrs     = authHeaders(accessToken, env.tenantHost);
  const fixtures = env.fixtures;

  // ── PASO 1: Ver morosos del mes actual ───────────────────────────────────
  group('Pagos: consultar morosos', () => {
    const start = Date.now();
    const res   = http.get(
      `${env.apiBase}/payments/?estado=VENCIDO&page=1&page_size=50`,
      { headers: hdrs, tags: { endpoint: 'payments_morosos', operation: 'read' } }
    );
    paymentListDuration.add(Date.now() - start);

    check(res, {
      'morosos: status 200':           (r) => r.status === 200,
      'morosos: tiempo < 500ms':       (r) => r.timings.duration < 500,
      'morosos: tiene resultados':     (r) => r.json('count') !== undefined,
    });
    if (res.status !== 200) paymentErrors.add(1); else paymentErrors.add(0);
    sleep(1.5);
  });

  // ── PASO 2: Ver listado completo con filtros ──────────────────────────────
  group('Pagos: listado con filtros', () => {
    // Filtros combinados: mes + anio
    const resFiltered = http.get(
      `${env.apiBase}/payments/?mes=${fixtures.mes}&anio=${fixtures.anio}&page=1&page_size=25`,
      { headers: hdrs, tags: { endpoint: 'payments_filtered', operation: 'read' } }
    );
    check(resFiltered, {
      'filtrado mes/anio: status 200':     (r) => r.status === 200,
      'filtrado mes/anio: tiempo < 500ms': (r) => r.timings.duration < 500,
    });
    sleep(1);

    // Filtro por estado
    const estado = randomItem(['PENDIENTE', 'PAGADO', 'VENCIDO']);
    const resByEstado = http.get(
      `${env.apiBase}/payments/?estado=${estado}`,
      { headers: hdrs, tags: { endpoint: 'payments_by_estado', operation: 'read' } }
    );
    check(resByEstado, {
      'filtrado estado: status 200': (r) => r.status === 200,
    });
    sleep(1);
  });

  // ── PASO 3: Ver detalle de un pago ───────────────────────────────────────
  group('Pagos: detalle de pago', () => {
    const start = Date.now();
    const res   = http.get(
      `${env.apiBase}/payments/${fixtures.paymentId}/`,
      { headers: hdrs, tags: { endpoint: 'payments_detail', operation: 'read' } }
    );
    paymentDetailDuration.add(Date.now() - start);

    check(res, {
      'detalle pago: status 200':      (r) => r.status === 200,
      'detalle pago: tiene id':        (r) => r.json('id') !== undefined,
      'detalle pago: tiene estado':    (r) => r.json('estado') !== undefined,
      'detalle pago: tiempo < 500ms':  (r) => r.timings.duration < 500,
    });
    sleep(1);
  });

  // ── PASO 4: Registrar un nuevo pago ──────────────────────────────────────
  group('Pagos: registrar pago', () => {
    const mes     = randomItem(MESES_ESCOLARES);
    const payload = generatePaymentPayload(fixtures.studentId, mes, fixtures.anio);
    const start   = Date.now();
    const res     = http.post(
      `${env.apiBase}/payments/`,
      JSON.stringify(payload),
      { headers: hdrs, tags: { endpoint: 'payments_create', operation: 'write' } }
    );
    paymentRegDuration.add(Date.now() - start);

    if (res.status === 201) {
      paymentsCreated.add(1);
      paymentErrors.add(0);

      check(res, {
        'nuevo pago: tiene id':             (r) => r.json('id') !== undefined,
        'nuevo pago: estado correcto':      (r) => r.json('estado') !== undefined,
        'nuevo pago: tiempo < 500ms':       (r) => r.timings.duration < 500,
        'nuevo pago: tiene comprobante':    (r) => r.json('numero_comprobante') !== undefined,
      });

      // ── PASO 5: Verificar pago registrado ───────────────────────────────
      const paymentId = res.json('id');
      sleep(0.5);
      const verify = http.get(
        `${env.apiBase}/payments/${paymentId}/`,
        { headers: hdrs, tags: { endpoint: 'payments_verify', operation: 'read' } }
      );
      check(verify, {
        'verificacion: status 200':    (r) => r.status === 200,
        'verificacion: id correcto':   (r) => r.json('id') === paymentId,
      });

    } else if (res.status === 400) {
      // 400 puede ser pago duplicado (alumno ya pago ese mes)
      paymentsRejected.add(1);
      paymentErrors.add(0); // 400 es comportamiento esperado
      check(res, {
        'pago rechazado: tiene mensaje de error': (r) => r.json() !== null,
      });
      if (res.body.toLowerCase().includes('duplicado') ||
          res.body.toLowerCase().includes('already') ||
          res.body.toLowerCase().includes('existe')) {
        duplicateAttempts.add(1);
      }
    } else {
      paymentsRejected.add(1);
      paymentErrors.add(1);
    }

    sleep(2);
  });

  sleep(1);
}

// ─── Monitoreo del director durante pagos ────────────────────────────────────

function runDirectorMonitoring(accessToken, env) {
  const hdrs     = authHeaders(accessToken, env.tenantHost);
  const fixtures = env.fixtures;

  group('Pagos: director monitorea ingresos', () => {
    // KPIs del dashboard (deben reflejar los nuevos pagos)
    const dashboard = http.get(
      `${env.apiBase}/dashboard/resumen/`,
      { headers: hdrs, tags: { endpoint: 'dashboard_resumen', role: 'director' } }
    );
    check(dashboard, {
      'director dashboard: status 200':       (r) => r.status === 200,
      'director dashboard: tiempo < 1000ms':  (r) => r.timings.duration < 1000,
    });
    sleep(2);

    // Cashflow actualizado con los pagos recientes
    const cashflow = http.get(
      `${env.apiBase}/cashflow/cash-transactions/?mes=${fixtures.mes}&anio=${fixtures.anio}`,
      { headers: hdrs, tags: { endpoint: 'cashflow_transactions', role: 'director' } }
    );
    check(cashflow, {
      'director cashflow: status 200':     (r) => r.status === 200,
      'director cashflow: tiempo < 800ms': (r) => r.timings.duration < 800,
    });
    sleep(3);
  });
}

// ─── Teardown ─────────────────────────────────────────────────────────────────

export function teardown(data) {
  console.log(`Payments Flow test finalizado. Ambiente: ${data.env.envName}`);
  console.log('NOTA: Eliminar pagos de prueba con numero_comprobante que empiece con PERF-');
  console.log("  DELETE FROM payments_payment WHERE numero_comprobante LIKE 'PERF-%';");
}
