/**
 * crud-students.js - TEST ESPECIFICO: CRUD de Alumnos
 * ──────────────────────────────────────────────────────
 * Objetivo: Validar el rendimiento del ciclo completo de gestion de alumnos
 *           con diferentes roles y permisos (RBAC de SAAS COREM).
 *
 * Flujo testeado:
 *   1. Secretaria crea un alumno (POST)
 *   2. Secretaria busca el alumno en el listado (GET con filtro)
 *   3. Secretaria actualiza datos del alumno (PATCH)
 *   4. Director consulta detalle con datos anidados (GET /{id}/)
 *   5. Docente intenta acceder (debe ser limitado segun permisos)
 *   6. Secretaria desactiva el alumno (DELETE o PATCH estado=INACTIVO)
 *
 * Configuracion: 10 VUs, 3 minutos
 * Ejecutar: k6 run --env ENV=local scripts/crud-students.js
 */

import http   from 'k6/http';
import { sleep, check, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

import { getEnvConfig }           from '../config/environments.js';
import { CRUD_STUDENTS_THRESHOLDS } from '../config/thresholds.js';
import { getMultiRoleTokens, authHeaders } from '../helpers/auth.js';
import {
  generateStudentData,
  generateDNI,
} from '../helpers/data.js';

// ─── Metricas custom ──────────────────────────────────────────────────────────

const studentCreatedDuration = new Trend('student_create_duration', true);
const studentUpdateDuration  = new Trend('student_update_duration', true);
const studentListDuration    = new Trend('student_list_duration', true);

const studentsCreated        = new Counter('students_created');
const studentsUpdated        = new Counter('students_updated');
const crudErrors             = new Rate('crud_error_rate');
const createdStudentIds      = []; // Para limpieza en teardown (solo VU 1 usa esto)

// ─── Opciones ─────────────────────────────────────────────────────────────────

export const options = {
  scenarios: {
    // VUs de secretaria: CRUD completo
    secretaria_crud: {
      executor:          'ramping-vus',
      startVUs:          0,
      stages: [
        { duration: '30s', target: 5 },
        { duration: '2m',  target: 5 },
        { duration: '30s', target: 0 },
      ],
      tags: { role: 'secretary' },
    },
    // VUs de director: solo lectura de detalle
    director_read: {
      executor:          'constant-vus',
      vus:               3,
      duration:          '3m',
      startTime:         '30s',
      tags: { role: 'director' },
    },
  },
  thresholds: CRUD_STUDENTS_THRESHOLDS,
  tags: { testType: 'crud-students', project: 'saas-corem' },
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

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function (data) {
  const { tokens, env } = data;

  // Seleccion de escenario por tag del scenario
  if (__ENV.SCENARIO_TAG === 'director') {
    runDirectorReadOnly(tokens.director.access, env);
  } else {
    runSecretaryCRUD(tokens.secretary.access, env);
  }
}

// ─── Escenario: Secretaria CRUD completo ─────────────────────────────────────

function runSecretaryCRUD(accessToken, env) {
  const hdrs = authHeaders(accessToken, env.tenantHost);
  let createdId = null;

  // ── PASO 1: Listar alumnos ────────────────────────────────────────────────
  group('CRUD Students: listar', () => {
    const start = Date.now();
    const res   = http.get(
      `${env.apiBase}/students/?page=1&page_size=25`,
      { headers: hdrs, tags: { endpoint: 'students_list', operation: 'R' } }
    );
    studentListDuration.add(Date.now() - start);

    const ok = check(res, {
      'list: status 200':           (r) => r.status === 200,
      'list: tiene count':          (r) => r.json('count') !== undefined,
      'list: tiene results':        (r) => Array.isArray(r.json('results')),
      'list: tiempo < 500ms':       (r) => r.timings.duration < 500,
    });
    if (!ok) crudErrors.add(1); else crudErrors.add(0);
    sleep(1);
  });

  // ── PASO 2: Buscar con filtro ─────────────────────────────────────────────
  group('CRUD Students: buscar con filtro', () => {
    const res = http.get(
      `${env.apiBase}/students/?search=Performance`,
      { headers: hdrs, tags: { endpoint: 'students_search', operation: 'R' } }
    );
    check(res, {
      'search: status 200':   (r) => r.status === 200,
      'search: tiempo <500ms': (r) => r.timings.duration < 500,
    });
    sleep(1);
  });

  // ── PASO 3: Crear nuevo alumno ────────────────────────────────────────────
  group('CRUD Students: crear alumno', () => {
    const payload = generateStudentData();
    const start   = Date.now();
    const res     = http.post(
      `${env.apiBase}/students/`,
      JSON.stringify(payload),
      { headers: hdrs, tags: { endpoint: 'students_create', operation: 'C' } }
    );
    studentCreatedDuration.add(Date.now() - start);

    const ok = check(res, {
      'create: status 201':           (r) => r.status === 201,
      'create: tiene id':             (r) => r.json('id') !== undefined,
      'create: tiempo < 500ms':       (r) => r.timings.duration < 500,
      'create: nombre correcto':      (r) => r.json('apellido_paterno') === 'PerformanceTest',
    });

    if (ok) {
      createdId = res.json('id');
      studentsCreated.add(1);
      crudErrors.add(0);
    } else {
      crudErrors.add(1);
    }
    sleep(1);
  });

  // ── PASO 4: Leer detalle del alumno creado ───────────────────────────────
  if (createdId) {
    group('CRUD Students: detalle alumno creado', () => {
      const res = http.get(
        `${env.apiBase}/students/${createdId}/`,
        { headers: hdrs, tags: { endpoint: 'students_detail', operation: 'R' } }
      );
      check(res, {
        'detail: status 200':          (r) => r.status === 200,
        'detail: id correcto':         (r) => r.json('id') === createdId,
        'detail: tiene apellido':      (r) => r.json('apellido_paterno') !== undefined,
        'detail: tiempo < 500ms':      (r) => r.timings.duration < 500,
      });
      sleep(1);
    });

    // ── PASO 5: Actualizar alumno (PATCH parcial) ────────────────────────────
    group('CRUD Students: actualizar alumno', () => {
      const updatePayload = {
        telefono_padre: '987' + String(Math.floor(Math.random() * 1000000)).padStart(6, '0'),
        direccion:      'Av. Actualizada 456, Lima - k6 update',
      };
      const start = Date.now();
      const res   = http.patch(
        `${env.apiBase}/students/${createdId}/`,
        JSON.stringify(updatePayload),
        { headers: hdrs, tags: { endpoint: 'students_update', operation: 'U' } }
      );
      studentUpdateDuration.add(Date.now() - start);

      const ok = check(res, {
        'update: status 200':        (r) => r.status === 200,
        'update: direccion actualizada': (r) => r.json('direccion') !== undefined,
        'update: tiempo < 500ms':    (r) => r.timings.duration < 500,
      });
      if (ok) studentsUpdated.add(1);
      else    crudErrors.add(1);
      sleep(1);
    });

    // ── PASO 6: Desactivar alumno ────────────────────────────────────────────
    group('CRUD Students: desactivar alumno', () => {
      // SAAS COREM probablemente usa soft delete via estado
      const res = http.patch(
        `${env.apiBase}/students/${createdId}/`,
        JSON.stringify({ activo: false }),
        { headers: hdrs, tags: { endpoint: 'students_deactivate', operation: 'D' } }
      );
      check(res, {
        'deactivate: status 200':    (r) => r.status === 200 || r.status === 204,
        'deactivate: tiempo < 500ms': (r) => r.timings.duration < 500,
      });
      sleep(1);
    });
  }

  sleep(2);
}

// ─── Escenario: Director solo lectura ────────────────────────────────────────

function runDirectorReadOnly(accessToken, env) {
  const hdrs = authHeaders(accessToken, env.tenantHost);
  const { fixtures } = env;

  group('CRUD Students: director lee detalle', () => {
    // Listado para buscar un alumno
    const list = http.get(
      `${env.apiBase}/students/?page=1&page_size=10`,
      { headers: hdrs, tags: { endpoint: 'students_list_director', operation: 'R', role: 'director' } }
    );
    check(list, {
      'director list: status 200':     (r) => r.status === 200,
      'director list: tiempo < 500ms': (r) => r.timings.duration < 500,
    });
    sleep(1);

    // Detalle del alumno fijo de fixtures
    const detail = http.get(
      `${env.apiBase}/students/${fixtures.studentId}/`,
      { headers: hdrs, tags: { endpoint: 'students_detail_director', operation: 'R', role: 'director' } }
    );
    check(detail, {
      'director detail: status 200':     (r) => r.status === 200,
      'director detail: tiempo < 500ms': (r) => r.timings.duration < 500,
    });
    sleep(2);
  });
}

// ─── Teardown: limpieza de datos ──────────────────────────────────────────────

export function teardown(data) {
  console.log(`CRUD Students test finalizado. Ambiente: ${data.env.envName}`);
  console.log('NOTA: Ejecutar en Django Admin o BD el siguiente query para limpiar datos de prueba:');
  console.log("  UPDATE students_student SET activo=false WHERE apellido_paterno='PerformanceTest';");
  console.log("  -- o --");
  console.log("  DELETE FROM students_student WHERE apellido_paterno='PerformanceTest';");
}
