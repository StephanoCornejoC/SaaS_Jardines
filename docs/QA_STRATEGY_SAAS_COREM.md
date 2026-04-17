# Estrategia de QA - SAAS COREM
## Sistema de Gestion de Jardines de Infancia (Peru)

**Documento:** Test Strategy (ISO/IEC/IEEE 29119-3)
**Version:** 1.0
**Fecha:** 2026-04-08
**Autor:** QA Lead Master Agent
**Stack:** Django 5.1 + React 18 + Vite | PostgreSQL + django-tenants | Celery + Redis
**Deploy:** Railway.app (backend) + Vercel (frontend)

---

## 1. RESUMEN EJECUTIVO

SAAS COREM es un SaaS multi-tenant para gestion de jardines de infancia en Peru. El proyecto tiene **12 apps Django**, **18 modelos de dominio**, **3 servicios de negocio criticos**, **4 tareas Celery**, y un frontend React con **13 paginas**. Actualmente tiene **0 tests** implementados.

**Estado actual de testing: CERO cobertura.** Todo debe construirse desde cero.

**Dependencias de testing ya disponibles:** pytest, pytest-django, pytest-cov, factory-boy (en requirements/dev.txt).

---

## 2. ARQUITECTURA DEL SISTEMA ANALIZADA

### 2.1 Backend - 12 Apps Django

| App | Modelos | Views | Services | Tasks | Complejidad |
|-----|---------|-------|----------|-------|-------------|
| **tenants** | Tenant, Domain | - | - | - | Media |
| **users** | User (custom, email-based) | UserViewSet | - | - | Alta |
| **students** | Student, Guardian, MedicalRecord | StudentViewSet, GuardianViewSet, MedicalRecordViewSet | - | - | Media |
| **teachers** | Teacher, TeacherContract, TeacherPayment | TeacherViewSet, ContractViewSet, PaymentViewSet | - | - | Media |
| **classrooms** | Classroom | ClassroomViewSet | - | - | Baja |
| **enrollments** | Enrollment | EnrollmentViewSet | - | - | Media |
| **payments** | MonthlyFee, Payment | PaymentViewSet, MonthlyFeeViewSet | generate_yape_qr, generate_monthly_payments | - | **MUY ALTA** |
| **cashflow** | CashCategory, CashTransaction, MonthlyClosure | CashCategoryViewSet, CashTransactionViewSet, MonthlyClosureViewSet | get_balance, close_month, get_cashflow_summary | - | **ALTA** |
| **attendance** | Attendance | AttendanceViewSet (registro masivo, reporte mensual) | - | - | Alta |
| **communications** | Communication | CommunicationViewSet (envio email) | - | - | Media |
| **migrations_academic** | AcademicMigration, MigrationDetail | AcademicMigrationViewSet | preview_migration, execute_migration, cleanup_graduated | - | **MUY ALTA** |
| **notifications** | EmailLog | - | send_payment_reminder, send_attendance_alert, send_communication_email | task_send_payment_reminders, task_check_attendance_alerts | Alta |
| **dashboard** | DashboardMetric | DashboardViewSet | calculate_daily_metrics | task_calculate_daily_metrics | Media |
| **reports** | - | ReportViewSet (4 reportes Excel) | - | - | Media |

### 2.2 Frontend - React 18 + Vite

- **13 paginas** con lazy loading
- **Zustand** para estado de auth
- **Axios** con interceptor para JWT refresh
- **Ant Design 5** como UI framework
- **Chart.js** para graficos en Dashboard
- **Sin framework de testing** instalado (ni Jest ni Vitest)

### 2.3 Infraestructura

- PostgreSQL 16 con schemas por tenant (django-tenants)
- Redis 7 para Celery broker
- Celery para tareas asincronas (metricas diarias, notificaciones)
- Docker Compose para desarrollo local
- Railway.app (backend prod), Vercel (frontend prod)

---

## 3. ANALISIS DE RIESGO (Probabilidad x Impacto)

### 3.1 Riesgos P0 - CRITICOS (Impacto catastrofico)

| ID | Riesgo | Modulo | Probabilidad | Impacto | Score |
|----|--------|--------|-------------|---------|-------|
| R01 | **Pagos registrados incorrectamente** - Montos erroneos, estados inconsistentes, CashTransaction no creada al registrar pago | payments + cashflow | Alta | Catastrofico | **25** |
| R02 | **Migracion academica corrompe datos** - execute_migration modifica estado de TODOS los alumnos activos en una transaccion. Un error deja la BD inconsistente | migrations_academic | Media | Catastrofico | **20** |
| R03 | **Aislamiento multi-tenant roto** - Un tenant accede a datos de otro. Todos los ViewSets usan `objects.all()` sin filtro explicito de tenant (confian en django-tenants) | tenants + todos | Media | Catastrofico | **20** |
| R04 | **Autenticacion/Autorizacion bypass** - JWT expuesto, roles no validados correctamente, escalamiento de privilegios via role hierarchy en UserCreateSerializer | users | Media | Catastrofico | **20** |
| R05 | **cleanup_graduated borra datos irrecuperablemente** - Anonimiza alumnos y elimina apoderados/fichas medicas. Sin confirmacion, sin backup, sin undo | migrations_academic | Baja | Catastrofico | **15** |

### 3.2 Riesgos P1 - ALTOS (Impacto severo)

| ID | Riesgo | Modulo | Probabilidad | Impacto | Score |
|----|--------|--------|-------------|---------|-------|
| R06 | **Cierre de mes contable incorrecto** - close_month calcula totales erroneos, cierre duplicado | cashflow | Media | Alto | **12** |
| R07 | **Notificaciones email no enviadas o enviadas duplicadas** - Tasks Celery sin idempotencia | notifications | Alta | Alto | **15** |
| R08 | **Asistencia masiva con datos inconsistentes** - registro_masivo no valida que student pertenezca al classroom | attendance | Media | Alto | **12** |
| R09 | **Reportes Excel con datos erroneos** - Calculos financieros con float en lugar de Decimal (reports/views.py linea 98, 304) | reports | Media | Alto | **12** |
| R10 | **Dashboard muestra metricas desactualizadas o incorrectas** - calculate_daily_metrics es complejo con multiples queries | dashboard | Media | Medio | **9** |

### 3.3 Riesgos P2 - MEDIOS

| ID | Riesgo | Modulo | Probabilidad | Impacto | Score |
|----|--------|--------|-------------|---------|-------|
| R11 | Matricula duplicada (unique_together pero sin validacion en serializer) | enrollments | Baja | Medio | 6 |
| R12 | Comunicacion POR_AULA enviada sin classroom asignado | communications | Baja | Medio | 6 |
| R13 | QR code generado con datos incorrectos | payments | Baja | Medio | 6 |
| R14 | Capacidad de aula excedida sin validacion | classrooms | Media | Bajo | 4 |

### 3.4 Riesgos P3 - BAJOS

| ID | Riesgo | Modulo | Probabilidad | Impacto | Score |
|----|--------|--------|-------------|---------|-------|
| R15 | Paginacion incorrecta en listados | todos | Baja | Bajo | 2 |
| R16 | Filtros de busqueda no retornan resultados correctos | todos | Baja | Bajo | 2 |

---

## 4. HALLAZGOS CRITICOS DEL CODIGO (Pre-Testing Findings)

### 4.1 BUGS / VULNERABILIDADES detectados en el codigo

| ID | Severidad | Archivo | Hallazgo |
|----|-----------|---------|----------|
| **F01** | CRITICA | `config/settings/base.py:11` | SECRET_KEY tiene fallback inseguro hardcodeado. En produccion si no se configura la env var, usa la key de desarrollo |
| **F02** | ALTA | `reports/views.py:98,304` | Conversion `float(payment.monto)` pierde precision decimal. Deberia usar `Decimal` para calculos financieros |
| **F03** | ALTA | `payments/views.py:55` | `if request.user.is_authenticated` es redundante (ya tiene `permission_classes=[IsAuthenticated]`), pero el riesgo real es que `registrado_por` podria quedar `None` en edge cases |
| **F04** | ALTA | `attendance/views.py:56` | `registro_masivo` no valida que `student_id` pertenezca al `classroom`. Un alumno de aula A podria tener asistencia registrada en aula B |
| **F05** | MEDIA | `cashflow/views.py:48-50` | Filtros `fecha_desde`/`fecha_hasta` aceptan strings sin validacion. Inyeccion de query params malformados podria causar errores 500 |
| **F06** | MEDIA | `migrations_academic/services.py:192` | `cleanup_graduated` genera DNI `XXXX{id:04d}` que podria colisionar si hay >9999 alumnos |
| **F07** | MEDIA | `docker-compose.yml:38` | `SECRET_KEY=dev-secret-key-change-in-production` hardcodeado en docker-compose |
| **F08** | MEDIA | `notifications/tasks.py:63-84` | `task_check_attendance_alerts` itera TODOS los alumnos activos y hace N+1 queries. Problema de performance con muchos alumnos |
| **F09** | BAJA | `docker-compose.yml:47` | `ALLOWED_HOSTS=*` es inseguro incluso en desarrollo |
| **F10** | BAJA | `users/serializers.py:37` | Validacion de role hierarchy permite que ADMIN_JARDIN cree otro ADMIN_JARDIN (mismo nivel), pero no SUPERADMIN. Es comportamiento intencional? |

---

## 5. PIRAMIDE DE TESTING PROPUESTA

```
         /    E2E (Playwright)     \    ~10% ->  ~25 tests
        /   API Integration         \   ~20% ->  ~50 tests
       /  Service / Business Logic   \  ~25% ->  ~60 tests
      /    Unit Tests (Models +       \ ~45% -> ~110 tests
     /     Serializers + Permissions)   \
    -----------------------------------------
                                    Total: ~245 tests
```

### 5.1 Distribucion por Capa

| Capa | Framework | Cantidad Est. | Prioridad |
|------|-----------|---------------|-----------|
| **Unit** | pytest + pytest-django + factory-boy | ~110 | Sprint 1 |
| **Service** | pytest + mocks (email, QR) | ~60 | Sprint 1-2 |
| **API Integration** | pytest + DRF APIClient + django-tenants test utils | ~50 | Sprint 2 |
| **E2E** | Playwright (TypeScript) | ~25 | Sprint 3 |
| **Performance** | k6 (Grafana) | ~8 scripts | Sprint 3 |
| **Security** | Manual OWASP checklist + dependency scan | 1 audit | Sprint 2 |

---

## 6. PLAN DE TESTING POR MODULO (Priorizado por Riesgo)

### SPRINT 1 - Modulos P0 (Criticos)

#### 6.1 payments (Riesgo: MUY ALTO)

**Unit Tests (~20 tests):**
- Payment model: is_overdue con diferentes estados y fechas
- MonthlyFee model: unique_together, str representation
- PaymentRegisterSerializer: validacion de estados y metodos de pago
- PaymentListSerializer: is_overdue serializado correctamente

**Service Tests (~12 tests):**
- generate_monthly_payments: creacion correcta, idempotencia (get_or_create), fecha_vencimiento edge cases (31 feb), solo alumnos ACTIVO
- generate_yape_qr: genera QR con datos correctos, guarda imagen en payment

**API Tests (~10 tests):**
- CRUD Payment: permisos por rol
- registrar_pago: cambia estado, crea CashTransaction, valida metodo_pago
- morosidad: filtros correctos, calculo de monto_total_pendiente
- generar_qr: retorna URL valido

#### 6.2 migrations_academic (Riesgo: MUY ALTO)

**Unit Tests (~8 tests):**
- AcademicMigration model: status choices, str
- MigrationDetail model: relaciones

**Service Tests (~15 tests):**
- preview_migration: alumnos por nivel, egresados (5 anios), promueven, sin_aula_destino
- execute_migration: transaccion atomica, rollback en error, alumnos de 5 anios -> EGRESADO + classroom=None, alumnos <5 -> classroom actualizado
- cleanup_graduated: anonimizacion correcta, eliminacion de apoderados/fichas, years_to_keep respetado, DNI collision edge case

**API Tests (~6 tests):**
- preview: requiere anio_origen, retorna estructura correcta
- ejecutar: solo SUPERADMIN, crea migration record
- cleanup_egresados: solo SUPERADMIN, retorna count

#### 6.3 users (Riesgo: ALTO)

**Unit Tests (~15 tests):**
- User model: role properties (is_superadmin, etc.), email as USERNAME_FIELD
- CustomUserManager: create_user (email obligatorio, normalize), create_superuser (is_staff, is_superuser, role SUPERADMIN)
- UserCreateSerializer: validacion role hierarchy, password min_length
- ChangePasswordSerializer: old_password validation, save changes password
- Permissions: IsSuperadmin, IsAdminJardinOrAbove, IsDirectorOrAbove con diferentes roles

**API Tests (~10 tests):**
- JWT login: token pair generation
- Token refresh: rotation + blacklist
- UserViewSet: CRUD permisos por rol, no puede eliminarse a si mismo, queryset filtrado por rol
- Change password: validacion old password, min length new password

#### 6.4 cashflow (Riesgo: ALTO)

**Unit Tests (~8 tests):**
- CashCategory, CashTransaction, MonthlyClosure models
- Serializers: validacion de tipos

**Service Tests (~10 tests):**
- get_balance: calculo correcto ingresos - egresos, mes sin transacciones -> 0
- close_month: crea closure, error si ya existe, totales correctos
- get_cashflow_summary: resumen anual, indicador cerrado/abierto

**API Tests (~8 tests):**
- CashTransaction CRUD: filtros fecha_desde/fecha_hasta, mes/anio
- resumen_anual: retorna summary correcto
- cerrar_mes: solo ADMIN_JARDIN+, validacion mes/anio requeridos

### SPRINT 2 - Modulos P1 (Altos) + Security

#### 6.5 attendance (~15 tests)

**Service/API Tests:**
- registro_masivo: crea/actualiza correctamente, validacion classroom existe
- reporte_mensual: calculos porcentaje, parametros requeridos
- CRUD basico: filtros, ordenamiento

#### 6.6 notifications (~12 tests)

**Service Tests (con mock de email):**
- send_payment_reminder: busca apoderado principal con email, contenido correcto
- send_attendance_alert: threshold de inasistencias
- send_communication_email: GENERAL vs POR_AULA, distinct emails

**Task Tests:**
- task_send_payment_reminders: busca pagos con vencimiento en 3 dias
- task_check_attendance_alerts: detecta N ausencias consecutivas

#### 6.7 communications (~8 tests)

**API Tests:**
- CRUD Communication
- enviar: solo ADMIN_JARDIN+, no re-enviar, POR_AULA requiere classroom, emails enviados

#### 6.8 reports (~8 tests)

**API Tests:**
- morosidad_excel: genera Excel valido, datos correctos
- alumnos_excel: filtra por estado
- asistencia_excel: requiere classroom_id
- cashflow_excel: totales correctos (corregir float -> Decimal)

#### 6.9 Security Audit

- OWASP Top 10 checklist manual
- SECRET_KEY hardcoded (F01)
- ALLOWED_HOSTS=* (F09)
- JWT token storage en localStorage (XSS vector)
- CORS configuration review
- Rate limiting (ya configurado: 20/min anon, 100/min user)
- Axes brute force protection (ya configurado: 5 attempts, 15 min cooloff)
- django-otp configurado pero no enforced en views
- Dependency scan (pip-audit)

### SPRINT 3 - Modulos P2 + E2E + Performance

#### 6.10 Modulos P2 (students, teachers, classrooms, enrollments, dashboard)

**Unit + API Tests (~30 tests):**
- Students: CRUD, nested guardians/medical_record, edad property
- Teachers: CRUD, contracts, teacher payments
- Classrooms: CRUD, alumnos_count, disponible property, capacidad
- Enrollments: CRUD, unique_together
- Dashboard: resumen, historico, calculate_daily_metrics

#### 6.11 E2E Tests - Playwright (~25 tests)

| Flujo | Tests |
|-------|-------|
| Login / Logout | 3 |
| CRUD Alumnos + detalle | 4 |
| Registro de asistencia masiva | 3 |
| Flujo de pagos (registrar, QR) | 4 |
| Flujo de caja (transaccion, cierre mes) | 3 |
| Comunicaciones (crear, enviar) | 2 |
| Migracion academica (preview, ejecutar) | 3 |
| Reportes Excel (descargar) | 3 |

#### 6.12 Performance Tests - k6 (~8 scripts)

| Script | Tipo | SLA Target |
|--------|------|------------|
| smoke_api_health | Smoke | <200ms p95, 0% errors |
| load_student_list | Load (50 VUs, 5 min) | <500ms p95, <1% errors |
| load_payment_register | Load (30 VUs, 5 min) | <800ms p95, <1% errors |
| load_attendance_bulk | Load (20 VUs, 3 min) | <1s p95, <1% errors |
| load_dashboard_metrics | Load (50 VUs, 5 min) | <500ms p95, <1% errors |
| stress_concurrent_payments | Stress (ramp 10->100 VUs) | Degrada graceful, no 500s |
| spike_login | Spike (100 VUs burst) | Throttle responde 429, no crash |
| load_reports_excel | Load (10 VUs, 3 min) | <3s p95 (generacion Excel) |

---

## 7. ESTRUCTURA DE PROYECTO DE TESTING

```
backend/
  conftest.py                          <- Fixtures globales (tenant, users, factories)
  pytest.ini                           <- Configuracion pytest
  apps/
    users/
      tests/
        __init__.py
        factories.py                   <- UserFactory
        test_models.py
        test_serializers.py
        test_permissions.py
        test_views.py
    students/
      tests/
        __init__.py
        factories.py                   <- StudentFactory, GuardianFactory, MedicalRecordFactory
        test_models.py
        test_serializers.py
        test_views.py
    payments/
      tests/
        __init__.py
        factories.py                   <- MonthlyFeeFactory, PaymentFactory
        test_models.py
        test_serializers.py
        test_services.py
        test_views.py
    cashflow/
      tests/
        __init__.py
        factories.py
        test_models.py
        test_services.py
        test_views.py
    attendance/
      tests/
        __init__.py
        factories.py
        test_views.py
    communications/
      tests/
        __init__.py
        factories.py
        test_views.py
    migrations_academic/
      tests/
        __init__.py
        factories.py
        test_services.py
        test_views.py
    notifications/
      tests/
        __init__.py
        test_services.py
        test_tasks.py
    dashboard/
      tests/
        __init__.py
        test_services.py
        test_views.py
    reports/
      tests/
        __init__.py
        test_views.py
    teachers/
      tests/
        __init__.py
        factories.py
        test_views.py
    classrooms/
      tests/
        __init__.py
        factories.py
        test_views.py
    enrollments/
      tests/
        __init__.py
        factories.py
        test_views.py

testing/
  e2e/                                 <- Playwright E2E tests (TypeScript)
    package.json
    playwright.config.ts
    tests/
      auth.spec.ts
      students.spec.ts
      attendance.spec.ts
      payments.spec.ts
      cashflow.spec.ts
      communications.spec.ts
      migrations.spec.ts
      reports.spec.ts
  performance/                         <- k6 scripts
    scripts/
      smoke_api_health.js
      load_student_list.js
      load_payment_register.js
      load_attendance_bulk.js
      load_dashboard_metrics.js
      stress_concurrent_payments.js
      spike_login.js
      load_reports_excel.js
    config/
      thresholds.json
```

---

## 8. CONFIGURACION REQUERIDA

### 8.1 pytest.ini (backend)

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=apps --cov-report=html --cov-report=term-missing -v
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks integration tests
    tenant: marks tests that require tenant setup
```

### 8.2 Settings de Test (config/settings/test.py)

```python
from .base import *

DEBUG = False
SECRET_KEY = "test-secret-key-not-for-production"

DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": "test_saas_corem",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {"NAME": "test_saas_corem"},
    }
}

# Desactivar email real en tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Desactivar Celery en tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Desactivar throttling en tests
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
}

# Desactivar axes en tests
AXES_ENABLED = False

# Media en temp dir
import tempfile
MEDIA_ROOT = tempfile.mkdtemp()

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
```

---

## 9. DELEGACION A SUB-AGENTES

Dado que SAAS COREM es **Django + React (JS)**, la mayor parte del testing la ejecuto **YO DIRECTAMENTE** (stack Django/Python). Solo delego E2E a Playwright.

### 9.1 Ejecucion Directa (QA Lead Master)

| Area | Lo que hago | Herramientas |
|------|-------------|--------------|
| **Unit Tests (Python)** | Escribo tests para models, serializers, permissions, managers | pytest, pytest-django, factory-boy |
| **Service Tests (Python)** | Escribo tests para services/ con mocks de email y QR | pytest, unittest.mock |
| **API Tests (Python)** | Escribo tests para ViewSets con DRF APIClient | pytest, rest_framework.test |
| **BDD/Gherkin** | Escribo feature files para flujos criticos | Gherkin syntax |
| **Performance** | Escribo scripts k6 | k6 (Grafana) |
| **Security** | Ejecuto OWASP checklist, STRIDE threat model | Manual + pip-audit |

### 9.2 Delegacion a Sub-Agentes

| Sub-Agente | Tarea | Justificacion |
|------------|-------|---------------|
| `qa-e2e-playwright` | 25 tests E2E Playwright (TypeScript) | Especialista en cross-browser, POM, selectores |
| `qa-static-analyzer` | Configurar linters (ruff ya incluido), SonarQube quality gate | Especialista en quality gates |
| `qa-ci-cd-integrator` | Pipeline CI/CD (GitHub Actions o Railway) | Especialista en pipelines |

---

## 10. METRICAS Y KPIs TARGET

| Metrica | Target Sprint 1 | Target Sprint 2 | Target Sprint 3 |
|---------|-----------------|-----------------|-----------------|
| Code Coverage (backend) | >60% | >75% | >85% |
| Tests passing | 100% | 100% | 100% |
| Flaky tests | 0 | 0 | 0 |
| P0 bugs corregidos | 5/5 | 5/5 | 5/5 |
| API response p95 | - | - | <500ms |
| Mutation score (criticos) | - | >70% | >80% |

---

## 11. CRITERIOS DE ENTRADA Y SALIDA

### Criterios de Entrada
- Docker Compose funcional (PostgreSQL + Redis)
- requirements/dev.txt instalado
- Migraciones ejecutadas exitosamente
- Al menos 1 tenant + 1 user creados como seed

### Criterios de Salida
- Todos los tests PASS (0 failures)
- Coverage >= target del sprint
- 0 bugs P0 abiertos
- Reportes de testing generados
- Hallazgos documentados con severidad y prioridad

---

## 12. ORDEN DE EJECUCION RECOMENDADO

### Fase 1: Infraestructura de Testing (Dia 1)
1. Crear `config/settings/test.py`
2. Crear `pytest.ini`
3. Crear `conftest.py` global con fixtures de tenant, users, factories base
4. Verificar que `pytest` ejecuta sin errores

### Fase 2: Tests Criticos P0 (Dias 2-5)
1. `payments/` - Unit + Service + API tests (42 tests)
2. `migrations_academic/` - Unit + Service + API tests (29 tests)
3. `users/` - Unit + API tests (25 tests)
4. `cashflow/` - Unit + Service + API tests (26 tests)

### Fase 3: Tests P1 + Security (Dias 6-8)
5. `attendance/` - API tests (15 tests)
6. `notifications/` - Service + Task tests (12 tests)
7. `communications/` - API tests (8 tests)
8. `reports/` - API tests (8 tests)
9. Security audit (OWASP + dependency scan)

### Fase 4: Tests P2 + E2E + Performance (Dias 9-12)
10. `students/`, `teachers/`, `classrooms/`, `enrollments/`, `dashboard/` (30 tests)
11. E2E Playwright setup + 25 tests (delegar a `qa-e2e-playwright`)
12. k6 performance scripts (8 scripts)
13. Pipeline CI/CD (delegar a `qa-ci-cd-integrator`)

---

## 13. RIESGOS DEL PLAN DE TESTING

| Riesgo | Mitigacion |
|--------|-----------|
| django-tenants complica test setup | Usar `TenantTestCase` de django-tenants, crear fixture reutilizable |
| Celery tasks dificiles de testear | `CELERY_TASK_ALWAYS_EAGER=True` en settings de test |
| Email testing | `locmem.EmailBackend` + `django.core.mail.outbox` |
| QR code generation en tests | Mock de qrcode library, validar solo datos de input |
| Multi-tenant DB permissions | Test DB con permisos para CREATE SCHEMA |
| Reportes Excel | Leer BytesIO response con openpyxl para validar contenido |
