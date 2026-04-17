/**
 * environments.js
 * Configuracion de ambientes para SAAS COREM performance tests.
 *
 * Uso:
 *   import { getEnvConfig } from '../config/environments.js';
 *   const ENV = getEnvConfig();
 *
 * Seleccion via variable de entorno:
 *   k6 run --env ENV=staging scripts/smoke.js
 */

// ─── Definicion de ambientes ────────────────────────────────────────────────

const ENVIRONMENTS = {
  /**
   * LOCAL: Docker Compose o servidor Django en la maquina del desarrollador.
   * El host Header se pasa como 'garabato.localhost' para que django-tenants
   * enrute al schema del tenant piloto.
   */
  local: {
    baseUrl:    'http://localhost:8000',
    apiBase:    'http://localhost:8000/api/v1',
    tenantHost: 'garabato.localhost',
    credentials: {
      admin:     { email: 'admin@garabato.corem.pe',     password: 'AdminPass123!' },
      secretary: { email: 'secretaria@garabato.corem.pe', password: 'SecPass123!' },
      teacher:   { email: 'docente@garabato.corem.pe',   password: 'DocPass123!' },
      director:  { email: 'director@garabato.corem.pe',  password: 'DirPass123!' },
    },
    // Datos fijos que deben existir en la BD de prueba
    fixtures: {
      classroomId:    1,
      studentId:      1,
      paymentId:      1,
      academicYearId: 1,
      mes:            3,
      anio:           2026,
    },
  },

  /**
   * STAGING: Ambiente de Railway apuntando al tenant piloto.
   * Variables sensibles se inyectan via CI (no hardcodear tokens reales).
   */
  staging: {
    baseUrl:    __ENV.STAGING_BASE_URL    || 'https://saas-corem-staging.up.railway.app',
    apiBase:    (__ENV.STAGING_BASE_URL   || 'https://saas-corem-staging.up.railway.app') + '/api/v1',
    tenantHost: __ENV.STAGING_TENANT_HOST || 'garabato.saascorem.com',
    credentials: {
      admin:     { email: __ENV.STAGING_ADMIN_EMAIL     || '', password: __ENV.STAGING_ADMIN_PASS     || '' },
      secretary: { email: __ENV.STAGING_SECRETARY_EMAIL || '', password: __ENV.STAGING_SECRETARY_PASS || '' },
      teacher:   { email: __ENV.STAGING_TEACHER_EMAIL   || '', password: __ENV.STAGING_TEACHER_PASS   || '' },
      director:  { email: __ENV.STAGING_DIRECTOR_EMAIL  || '', password: __ENV.STAGING_DIRECTOR_PASS  || '' },
    },
    fixtures: {
      classroomId:    parseInt(__ENV.STAGING_CLASSROOM_ID    || '1'),
      studentId:      parseInt(__ENV.STAGING_STUDENT_ID      || '1'),
      paymentId:      parseInt(__ENV.STAGING_PAYMENT_ID      || '1'),
      academicYearId: parseInt(__ENV.STAGING_ACADEMIC_YEAR   || '1'),
      mes:            3,
      anio:           2026,
    },
  },

  /**
   * PROD: Railway produccion.
   * PRECAUCION: solo ejecutar smoke test o tests de lectura con carga minima.
   * NUNCA ejecutar stress/soak en produccion sin aprobacion explicita.
   */
  prod: {
    baseUrl:    __ENV.PROD_BASE_URL    || 'https://saas-corem.up.railway.app',
    apiBase:    (__ENV.PROD_BASE_URL   || 'https://saas-corem.up.railway.app') + '/api/v1',
    tenantHost: __ENV.PROD_TENANT_HOST || 'garabato.saascorem.com',
    credentials: {
      // En prod solo usar credenciales de cuentas de test dedicadas
      admin:     { email: __ENV.PROD_PERF_EMAIL || '', password: __ENV.PROD_PERF_PASS || '' },
      secretary: { email: __ENV.PROD_PERF_EMAIL || '', password: __ENV.PROD_PERF_PASS || '' },
      teacher:   { email: __ENV.PROD_PERF_EMAIL || '', password: __ENV.PROD_PERF_PASS || '' },
      director:  { email: __ENV.PROD_PERF_EMAIL || '', password: __ENV.PROD_PERF_PASS || '' },
    },
    fixtures: {
      classroomId:    parseInt(__ENV.PROD_CLASSROOM_ID || '1'),
      studentId:      parseInt(__ENV.PROD_STUDENT_ID   || '1'),
      paymentId:      parseInt(__ENV.PROD_PAYMENT_ID   || '1'),
      academicYearId: parseInt(__ENV.PROD_ACADEMIC_YEAR|| '1'),
      mes:            3,
      anio:           2026,
    },
  },
};

// ─── Selector de ambiente ────────────────────────────────────────────────────

/**
 * Retorna la configuracion del ambiente activo.
 * El ambiente se selecciona via --env ENV=<nombre> al invocar k6.
 * Default: local
 */
export function getEnvConfig() {
  const envName = (__ENV.ENV || 'local').toLowerCase();
  const config  = ENVIRONMENTS[envName];

  if (!config) {
    throw new Error(
      `Ambiente desconocido: "${envName}". Valores validos: ${Object.keys(ENVIRONMENTS).join(', ')}`
    );
  }

  return { ...config, envName };
}

/**
 * Headers base requeridos por todas las requests a SAAS COREM.
 * El header Host es critico para que django-tenants enrute al schema correcto.
 */
export function baseHeaders(tenantHost) {
  return {
    'Content-Type': 'application/json',
    'Accept':       'application/json',
    'Host':         tenantHost,
  };
}
