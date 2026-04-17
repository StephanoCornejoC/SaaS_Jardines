/**
 * data.js
 * Datos de prueba y generadores para SAAS COREM performance tests.
 *
 * IMPORTANTE: Los datos generados aqui son para pruebas de performance.
 * Los registros creados en la BD deben limpiarse despues de cada test run.
 * Usa el prefijo 'PERF_' en nombres para facilitar la limpieza.
 */

import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

// ─── Constantes de negocio COREM ─────────────────────────────────────────────

export const ESTADOS_PAGO = ['PENDIENTE', 'PAGADO', 'VENCIDO', 'EXONERADO'];
export const ESTADOS_ASISTENCIA = ['PRESENTE', 'AUSENTE', 'TARDANZA', 'JUSTIFICADO'];
export const TIPOS_TRANSACCION = ['INGRESO', 'EGRESO'];
export const METODOS_PAGO = ['EFECTIVO', 'YAPE', 'PLIN', 'TRANSFERENCIA', 'DEPOSITO'];
export const TIPOS_COMUNICACION = ['GENERAL', 'POR_AULA', 'INDIVIDUAL'];

// Meses del anio escolar (Peru: marzo a diciembre)
export const MESES_ESCOLARES = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

// ─── Generadores de datos ─────────────────────────────────────────────────────

/**
 * Genera datos para crear un nuevo alumno.
 * El prefijo PERF_ permite identificar y limpiar registros de prueba.
 */
export function generateStudentData() {
  const ts    = Date.now();
  const uuid  = uuidv4().substring(0, 8);
  return {
    nombre:          `PERF_${uuid}`,
    apellido_paterno: 'PerformanceTest',
    apellido_materno: 'k6',
    fecha_nacimiento: '2020-03-15',
    dni:             generateDNI(),
    direccion:       'Av. Prueba 123, Lima',
    telefono_padre:  '999' + String(Math.floor(Math.random() * 1000000)).padStart(6, '0'),
    email_padre:     `perf_${ts}_${uuid}@test-k6.corem`,
    nombre_padre:    'Padre PerformanceTest',
    nombre_madre:    'Madre PerformanceTest',
  };
}

/**
 * Genera un DNI peruano valido de 8 digitos.
 */
export function generateDNI() {
  return String(Math.floor(10000000 + Math.random() * 89999999));
}

/**
 * Genera el payload para registro masivo de asistencia (~25 alumnos).
 * Simula el caso real: un docente pasa asistencia a toda el aula.
 *
 * @param {number[]} studentIds - Array de IDs de alumnos del aula
 * @param {string}   fecha      - Formato YYYY-MM-DD
 * @returns {object} Payload para POST /api/v1/attendance/registro-masivo/
 */
export function generateBulkAttendancePayload(studentIds, fecha) {
  const registros = studentIds.map((studentId) => {
    const rand = Math.random();
    let estado;
    if (rand < 0.80)      estado = 'PRESENTE';
    else if (rand < 0.90) estado = 'TARDANZA';
    else if (rand < 0.95) estado = 'AUSENTE';
    else                  estado = 'JUSTIFICADO';

    return {
      alumno_id: studentId,
      estado,
      observacion: estado !== 'PRESENTE' ? `Registro k6 performance test` : null,
    };
  });

  return {
    fecha,
    registros,
  };
}

/**
 * Genera payload para registrar un pago de pension.
 *
 * @param {number} studentId
 * @param {number} mes       - 1-12
 * @param {number} anio
 * @returns {object} Payload para POST /api/v1/payments/
 */
export function generatePaymentPayload(studentId, mes, anio) {
  const metodoPago = METODOS_PAGO[Math.floor(Math.random() * METODOS_PAGO.length)];
  return {
    alumno:        studentId,
    mes,
    anio,
    monto:         350.00,
    metodo_pago:   metodoPago,
    fecha_pago:    new Date().toISOString().split('T')[0],
    observacion:   'Pago registrado por k6 performance test',
    numero_comprobante: `PERF-${Date.now()}`,
  };
}

/**
 * Genera payload para una nueva transaccion de cashflow.
 *
 * @param {string} tipo - 'INGRESO' | 'EGRESO'
 * @returns {object}
 */
export function generateCashflowTransaction(tipo = 'INGRESO') {
  return {
    tipo,
    descripcion:  `Transaccion PERF k6 ${Date.now()}`,
    monto:        Math.floor(Math.random() * 500) + 50,
    fecha:        new Date().toISOString().split('T')[0],
    categoria:    tipo === 'INGRESO' ? 'PENSION' : 'OPERATIVO',
    observacion:  'Generado por k6 performance test - eliminar',
  };
}

/**
 * Genera payload para preview de migracion academica.
 * Esta query es costosa: hace JOIN entre matrículas, pagos y aulas.
 */
export function generateMigrationPreviewPayload(academicYearId) {
  return {
    anio_academico_origen: academicYearId,
    anio_academico_destino: academicYearId + 1,
    incluir_morosos:        false,
    incluir_inactivos:      false,
  };
}

// ─── Seleccion aleatoria de datos ─────────────────────────────────────────────

/**
 * Selecciona un elemento aleatorio de un array.
 */
export function randomItem(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

/**
 * Genera una fecha de asistencia dentro del anio escolar actual.
 * Evita fines de semana (no hay clases).
 */
export function generateSchoolDate(anio = 2026) {
  const mes      = randomItem(MESES_ESCOLARES);
  const maxDia   = new Date(anio, mes, 0).getDate();
  let fecha;
  do {
    const dia = Math.floor(Math.random() * maxDia) + 1;
    fecha     = new Date(anio, mes - 1, dia);
  } while (fecha.getDay() === 0 || fecha.getDay() === 6); // skip sabado y domingo

  return fecha.toISOString().split('T')[0];
}

/**
 * Array simulado de IDs de alumnos para pruebas de asistencia masiva.
 * En produccion se obtendrían de un GET /api/v1/classrooms/{id}/students/
 * Aqui usamos IDs hardcodeados para el ambiente de prueba.
 */
export const MOCK_STUDENT_IDS = Array.from({ length: 25 }, (_, i) => i + 1);

/**
 * Parametros de paginacion variados para simular uso real.
 */
export const PAGINATION_PARAMS = [
  { page: 1, page_size: 25 },
  { page: 1, page_size: 10 },
  { page: 2, page_size: 25 },
  { page: 1, page_size: 50 },
];

export function randomPagination() {
  return randomItem(PAGINATION_PARAMS);
}
