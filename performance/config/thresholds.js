/**
 * thresholds.js
 * SLAs y thresholds de k6 para SAAS COREM.
 *
 * Contexto de infraestructura Railway (plan Starter):
 *   - RAM:   ~512 MB
 *   - vCPU:  ~0.5-1 vCPU compartido
 *   - DB:    PostgreSQL Railway (latencia de red adicional ~5-15ms)
 *   - Redis: Railway Redis (cache de sesiones / Django cache)
 *
 * Los thresholds se definen conservadoramente para Railway.
 * En infraestructura dedicada (VPS/ECS) se pueden reducir en ~30%.
 */

// ─── SLAs por categoria de endpoint ─────────────────────────────────────────

export const SLA = {
  // Endpoints CRUD basicos (GET con paginacion, POST simple)
  crud: {
    p95: 500,    // ms
    p99: 1000,   // ms
  },
  // Dashboard y KPIs (queries a multiples tablas, posible cache)
  dashboard: {
    p95: 1000,   // ms
    p99: 2000,   // ms
  },
  // Reportes Excel (genera archivo en memoria con openpyxl)
  reports: {
    p95: 3000,   // ms
    p99: 6000,   // ms
  },
  // Registro masivo de asistencia (bulk create/update ~25 records)
  bulkOps: {
    p95: 2000,   // ms
    p99: 4000,   // ms
  },
  // Cashflow con filtros de fecha
  cashflow: {
    p95: 800,    // ms
    p99: 1500,   // ms
  },
  // Auth (login, refresh)
  auth: {
    p95: 300,    // ms
    p99: 600,    // ms
  },
};

// ─── Thresholds por tipo de test ─────────────────────────────────────────────

/**
 * SMOKE: 1 VU, 30s - solo valida que el sistema responde correctamente.
 * Thresholds muy estrictos porque no hay carga concurrente.
 */
export const SMOKE_THRESHOLDS = {
  http_req_duration:               ['p(95)<500',  'p(99)<1000'],
  http_req_failed:                 ['rate<0.01'],
  http_reqs:                       ['rate>1'],
  // Custom metrics
  auth_duration:                   ['p(95)<300'],
  dashboard_duration:              ['p(95)<1000'],
};

/**
 * LOAD: 20 VUs, 5min - carga normal de un dia escolar.
 * Simula secretaria + docentes + director trabajando simultaneamente.
 */
export const LOAD_THRESHOLDS = {
  http_req_duration:               ['p(95)<500',  'p(99)<1000'],
  http_req_failed:                 ['rate<0.01'],
  http_reqs:                       ['rate>50'],
  // Custom metrics de negocio
  auth_duration:                   ['p(95)<300'],
  dashboard_duration:              ['p(95)<1000'],
  report_generation_duration:      ['p(95)<3000'],
  bulk_attendance_duration:        ['p(95)<2000'],
  payment_registration_duration:   ['p(95)<500'],
};

/**
 * STRESS: ramp hasta 100 VUs - encontrar el punto de quiebre de Railway.
 * Thresholds mas permisivos porque el objetivo es encontrar el limite,
 * no validar la calidad. El test pasa si el sistema no colapsa completamente.
 */
export const STRESS_THRESHOLDS = {
  http_req_duration:               ['p(95)<2000', 'p(99)<5000'],
  http_req_failed:                 ['rate<0.15'],   // hasta 15% de errores aceptable en stress
  http_reqs:                       ['rate>20'],
};

/**
 * SPIKE: pico subito de 5 a 80 VUs.
 * El sistema debe recuperarse despues del pico.
 */
export const SPIKE_THRESHOLDS = {
  http_req_duration:               ['p(95)<3000'],
  http_req_failed:                 ['rate<0.20'],   // el spike puede causar errores temporales
};

/**
 * SOAK: 15 VUs, 30min - buscar memory leaks y degradacion gradual.
 * Los thresholds son iguales al load test: si el sistema se degrada
 * con el tiempo, los thresholds lo detectaran.
 */
export const SOAK_THRESHOLDS = {
  http_req_duration:               ['p(95)<500',  'p(99)<1000'],
  http_req_failed:                 ['rate<0.01'],
  http_reqs:                       ['rate>30'],
  dashboard_duration:              ['p(95)<1000'],
};

/**
 * REPORTES PESADOS: concurrencia en descarga de Excel.
 * Thresholds especificos para endpoints costosos.
 */
export const REPORTS_THRESHOLDS = {
  http_req_duration:               ['p(95)<3000', 'p(99)<6000'],
  http_req_failed:                 ['rate<0.05'],
  report_generation_duration:      ['p(95)<3000'],
};

/**
 * CRUD ESTUDIANTES: operaciones CRUD con diferentes roles.
 */
export const CRUD_STUDENTS_THRESHOLDS = {
  http_req_duration:               ['p(95)<500', 'p(99)<1000'],
  http_req_failed:                 ['rate<0.01'],
  http_reqs:                       ['rate>50'],
};

/**
 * FLUJO PAGOS: registro y consulta de pensiones.
 */
export const PAYMENTS_THRESHOLDS = {
  http_req_duration:               ['p(95)<500',  'p(99)<1000'],
  http_req_failed:                 ['rate<0.01'],
  payment_registration_duration:   ['p(95)<500'],
};

/**
 * ESCENARIO MIXTO REALISTA.
 */
export const MIXED_THRESHOLDS = {
  http_req_duration:               ['p(95)<800',  'p(99)<2000'],
  http_req_failed:                 ['rate<0.01'],
  http_reqs:                       ['rate>50'],
  dashboard_duration:              ['p(95)<1000'],
  report_generation_duration:      ['p(95)<3000'],
  bulk_attendance_duration:        ['p(95)<2000'],
  payment_registration_duration:   ['p(95)<500'],
};
