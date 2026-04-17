# PROMPT: Construir SAAS COREM - Sistema de Gestion para Jardines de Infancia

## Contexto del proyecto

Necesito que construyas un SaaS completo para gestion de jardines de infancia (kinders) en Peru. El primer cliente piloto es "Jardin Garabato". El sistema debe ser un diferencial competitivo en el mercado pero economico de operar.

**Stack obligatorio:**
- Backend: Django 5.x + django-tenants + Django REST Framework + SimpleJWT
- Frontend: React 18 + Vite + Ant Design + Zustand + Chart.js + dayjs
- DB: PostgreSQL 16 (requerido por django-tenants)
- Cache/Queue: Redis 7 + Celery
- Deploy target: Backend en Railway.app (~$5-7/mes), Frontend en Vercel (gratis)
- Admin theme: django-jazzmin (NO usar django-unfold, tiene bugs con Python 3.13+)
- PDF: xhtml2pdf (NO usar weasyprint, requiere dependencias de sistema pesadas para Railway)
- Excel: openpyxl
- QR: qrcode + Pillow

**Carpeta del proyecto:** `D:\PROYECTOS\SAAS_COREM\`

---

## Arquitectura Multi-Tenant

Usar django-tenants con schema isolation por PostgreSQL. Cada jardin tiene su propio schema.

```
PostgreSQL DB: saas_corem
├── public (schema)          <- Tenants, Domains, Users globales
├── jardin_garabato (schema) <- Datos operativos del jardin
└── (futuros jardines)
```

### CRITICO sobre SHARED_APPS vs TENANT_APPS:
- `apps.users` DEBE estar en SHARED_APPS Y en TENANT_APPS (para auth en schema publico)
- `rest_framework_simplejwt.token_blacklist` DEBE estar en ambos
- `auditlog` DEBE estar en ambos
- `axes` DEBE estar en ambos
- `django_otp` y `django_otp.plugins.otp_totp` DEBEN estar en ambos
- jazzmin y django.contrib.admin SOLO en SHARED_APPS

### CRITICO sobre dominios y tenants:
- En desarrollo local, el Domain del tenant debe ser `localhost` (sin puerto)
- El superuser de COREM debe existir tanto en el schema publico como en el schema del tenant
- django-tenants usa el header `Host` para resolver el tenant, asi que el frontend en dev DEBE usar el Vite proxy (no conexion directa al backend) para que el Host sea consistente

---

## Modulos del Sistema (12 apps Django)

### 1. tenants - Multi-tenancy
```
Tenant: schema_name, nombre, ruc(max 11), direccion, telefono, email, logo(ImageField null), plan(BASICO|PROFESIONAL|PREMIUM), activo, created_at, updated_at
Domain: domain, tenant(FK), is_primary
```

### 2. users - Autenticacion y Roles
```
User (extends AbstractUser, email como USERNAME_FIELD, sin username):
  email(unique), role(SUPERADMIN|ADMIN_JARDIN|DIRECTOR|SECRETARIA|PROFESOR), telefono(null), is_active
  
Necesita CustomUserManager con create_user/create_superuser sin username.
```

**Permisos custom:**
- IsSuperadmin
- IsAdminJardinOrAbove (permite SUPERADMIN, ADMIN_JARDIN)
- IsDirectorOrAbove (permite SUPERADMIN, ADMIN_JARDIN, DIRECTOR)

**Endpoints:**
- POST /api/v1/auth/token/ (login JWT)
- POST /api/v1/auth/token/refresh/
- GET /api/v1/auth/users/ (list, filtrado por rol)
- GET /api/v1/auth/users/me/ (perfil del usuario autenticado) <-- NO OLVIDAR ESTE ENDPOINT
- POST /api/v1/auth/users/change-password/

**Validaciones importantes:**
- Password min_length=10 (debe coincidir con AUTH_PASSWORD_VALIDATORS)
- Prevencion de escalacion de roles (ADMIN no puede crear SUPERADMIN)
- Cambio de password invalida todos los tokens JWT existentes
- No permitir auto-eliminacion
- Usuarios no-admin solo ven su propio perfil

### 3. students - Alumnos
```
Student: dni(max 8, unique), nombres, apellidos, fecha_nacimiento, genero(M|F), foto(null), classroom(FK null), estado(ACTIVO|RETIRADO|EGRESADO|ELIMINADO), fecha_ingreso, created_at, updated_at
  - Property: edad (calculada desde fecha_nacimiento)
  
Guardian: student(FK, related_name="apoderados"), dni(max 8), nombres, apellidos, telefono, email(null), parentesco(PADRE|MADRE|TUTOR|OTRO), es_principal
  - unique_together: student + dni

MedicalRecord: student(OneToOne, related_name="ficha_medica"), tipo_sangre(choices), alergias(text blank), seguro, hospital_referencia, contacto_emergencia_nombre, contacto_emergencia_telefono, observaciones
```

**Permisos:** PROFESOR solo lectura. ADMIN_JARDIN+ para crear/editar/eliminar.
**Serializers:** `student` en GuardianSerializer debe ser read_only (se setea por URL).

### 4. teachers - Profesores
```
Teacher: user(OneToOne null), dni(max 8, unique), nombres, apellidos, especialidad, telefono, email(null), fecha_ingreso, activo, created_at, updated_at

TeacherContract: teacher(FK), tipo(TIEMPO_COMPLETO|MEDIO_TIEMPO|POR_HORAS), sueldo(Decimal 10,2), fecha_inicio, fecha_fin(null), activo, created_at

TeacherPayment: contract(FK), mes(1-12), anio, monto(Decimal), fecha_pago, metodo_pago(TRANSFERENCIA|EFECTIVO|DEPOSITO), comprobante, observaciones, created_at
  - unique_together: contract + mes + anio
```

**Serializers:** `teacher` en ContractSerializer y `contract` en PaymentSerializer deben ser read_only.

### 5. classrooms - Aulas
```
Classroom: nombre, nivel_edad(IntegerChoices 2|3|4|5), capacidad(default 25), profesor_titular(FK Teacher null), profesor_auxiliar(FK Teacher null), anio_escolar, activo, created_at, updated_at
  - unique_together: nombre + anio_escolar
  - Properties: alumnos_count, disponible
```

### 6. enrollments - Matriculas
```
Enrollment: student(FK), classroom(FK), anio_escolar, costo_matricula(Decimal 10,2), estado(PENDIENTE|PAGADA|ANULADA), fecha_matricula(auto_now_add), observaciones, created_by(FK User null), created_at, updated_at
  - unique_together: student + anio_escolar
```
**Serializer:** `created_by` debe ser read_only.

### 7. payments - Pensiones (MODULO FINANCIERO CORE)
```
MonthlyFee: student(FK), anio_escolar, monto_mensual(Decimal), dia_vencimiento(default 15), created_at
  - unique_together: student + anio_escolar

Payment: student(FK), monthly_fee(FK), mes(1-12), anio, monto(Decimal), estado(PENDIENTE|PAGADO|VENCIDO|EXONERADO), fecha_vencimiento, fecha_pago(null), metodo_pago(EFECTIVO|YAPE|PLIN|TRANSFERENCIA|OTRO), comprobante, qr_code(ImageField null), observaciones, registrado_por(FK User null), created_at, updated_at
  - unique_together: student + mes + anio
  - Property: is_overdue
```

**CRITICO - Accion registrar_pago:**
- Debe ser metodo PATCH (no POST)
- Al marcar como PAGADO, DEBE crear automaticamente un CashTransaction de tipo INGRESO
- `registrado_por` debe ser read_only en serializer

**Servicios:**
- `generate_yape_qr(student, payment)`: genera QR con qrcode library
- `generate_monthly_payments(anio, mes)`: crea Payment records para todos los alumnos con MonthlyFee activo

**Reporte morosidad:** usar `queryset.aggregate(total=Sum("monto"))` (NO Python sum() en memoria)

### 8. cashflow - Flujo de Caja
```
CashCategory: nombre, tipo(INGRESO|EGRESO), es_sistema(bool, para categorias auto-generadas), activo, created_at

CashTransaction: categoria(FK), descripcion, monto(Decimal), tipo(INGRESO|EGRESO), fecha, referencia_pago(FK Payment null), referencia_teacher_payment(FK TeacherPayment null), creado_por(FK User), created_at, updated_at

MonthlyClosure: mes, anio, total_ingresos(Decimal), total_egresos(Decimal), balance(Decimal), cerrado_por(FK User), observaciones, fecha_cierre(auto_now_add)
  - unique_together: mes + anio
  - NO incluir campo created_at duplicado (fecha_cierre ya cumple esa funcion)
```

**Serializer:** `creado_por` debe ser read_only.
**Servicio get_cashflow_summary:** usar Django ORM aggregation con ExtractMonth + Sum + Q filters (NO loop mes por mes con N+1 queries).

### 9. migrations_academic - Migracion Academica
```
AcademicMigration: anio_origen, anio_destino, ejecutado_por(FK User), fecha(auto_now_add), total_migrados, status(PREVIEW|EJECUTADO|ROLLBACK), observaciones

MigrationDetail: migration(FK), student(FK), aula_origen(FK Classroom null), aula_destino(FK null), estado_anterior, estado_nuevo
```

**Servicios:**
- `preview_migration(anio)`: dry-run, retorna que pasaria
- `execute_migration(anio, user)`: promueve alumnos 2->3, 3->4, 4->5, 5->EGRESADO
- `cleanup_graduated(years_to_keep=2)`: anonimiza (NO elimina) egresados antiguos

**CRITICO sobre cleanup:**
- `years_to_keep` minimo 1 (rechazar 0)
- Soft-delete: cambiar estado a ELIMINADO y anonimizar datos (NO .delete())
- Limite de batch: max 500 registros
- Permisos: ejecutar y cleanup requieren IsSuperadmin

**CRITICO sobre preview/execute:**
- Debe manejar MULTIPLES aulas por nivel_edad (no asumir 1 aula por nivel)
- Distribuir alumnos respetando capacidad

### 10. attendance - Asistencia
```
Attendance: student(FK), classroom(FK, on_delete=PROTECT), fecha, estado(PRESENTE|AUSENTE|TARDANZA|JUSTIFICADO), observaciones, registrado_por(FK User), created_at
  - unique_together: student + fecha
  - IMPORTANTE: classroom on_delete=PROTECT (no CASCADE, preservar historial)
```

**Accion registro_masivo:** validar que cada student_id pertenece al classroom especificado antes de crear registros.
**Serializer:** `registrado_por` debe ser read_only.

### 11. communications - Comunicaciones
```
Communication: titulo, contenido(text), tipo(GENERAL|POR_AULA), classroom(FK null, solo si tipo=POR_AULA), enviado_por(FK User), fecha_envio(null), enviado(bool default False), created_at, updated_at
```

**Accion enviar:** solo marcar como `enviado=True` si al menos 1 email fue exitoso (no si todos fallan).
**Serializer:** `enviado_por`, `enviado`, `fecha_envio` deben ser read_only.

### 12. notifications - Notificaciones (sin API, solo servicio interno)
```
EmailLog: destinatario(email), asunto, contenido, tipo(RECORDATORIO_PAGO|COMUNICACION|ALERTA_ASISTENCIA|BIENVENIDA), enviado(bool), error(text blank), created_at
```

**Celery tasks:**
- `task_send_payment_reminders()`: pagos que vencen en 3 dias
- `task_check_attendance_alerts()`: alumnos con 3+ inasistencias consecutivas

### 13. dashboard - Metricas
```
DashboardMetric: fecha(unique), total_alumnos, total_profesores, alumnos_por_nivel(JSON), ingresos_mes(Decimal), egresos_mes(Decimal), balance_mes(Decimal), porcentaje_morosidad(Decimal), porcentaje_asistencia(Decimal), created_at
```

### 14. reports - Reportes Excel
ViewSet con 4 acciones que generan Excel con openpyxl:
- morosidad-excel, alumnos-excel, asistencia-excel, cashflow-excel
- Permisos: IsAdminJardinOrAbove (PROFESOR no puede descargar)
- CRITICO: usar Decimal directamente en openpyxl (NO float() que pierde precision)
- Usar `openpyxl.utils.get_column_letter()` para columnas (NO `chr(64+col)` que falla >26)

---

## Configuracion Django - Detalles criticos

### settings/base.py
```python
# SECRET_KEY: NO usar fallback hardcoded en produccion
def _get_secret_key():
    key = os.environ.get("DJANGO_SECRET_KEY")
    if key:
        return key
    import warnings
    warnings.warn("Using insecure SECRET_KEY. Set DJANGO_SECRET_KEY in environment.", stacklevel=2)
    return "django-insecure-dev-only-DO-NOT-USE-IN-PRODUCTION"

SECRET_KEY = _get_secret_key()

# STORAGES (no STATICFILES_STORAGE que esta deprecated desde Django 4.2)
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# LANGUAGE_CODE = "es" (NO "es-pe" que no tiene traducciones Django)

# JWT: ACCESS 30min, REFRESH 1 dia, ROTATE=True, BLACKLIST=True

# DRF: PAGE_SIZE=25, throttle anon 20/min, user 100/min

# AXES: 5 intentos, cooloff 15min, reset on success

# AUDITLOG_INCLUDE_ALL_MODELS = True
```

### settings/prod.py
```python
import os
from .base import *

# Fail fast si no hay SECRET_KEY
if not os.environ.get("DJANGO_SECRET_KEY"):
    raise ValueError("DJANGO_SECRET_KEY environment variable is required in production")

# Fix split empty string: usar list comprehension con filter
ALLOWED_HOSTS = [h for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h]
CORS_ALLOWED_ORIGINS = [o for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if o]
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o]

# NO incluir SECURE_BROWSER_XSS_FILTER (deprecated Django 4.0+)
```

### settings/dev.py
```python
import os  # EXPLICITO, no depender del wildcard import
from .base import *

# Puerto 5433 por si hay PostgreSQL nativo en 5432
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "PORT": os.environ.get("POSTGRES_PORT", "5433"),
        ...
    }
}
```

### URLs
```python
# config/urls.py - URL de admin ofuscada
path("corem-panel-x9k2/", admin.site.urls),

# Prefijos en config/urls.py + router.register("", ...) en cada app
# Resultado: /api/v1/students/ (NO /api/v1/students/students/)
path("api/v1/students/", include("apps.students.urls")),  # <- prefix aqui
# En apps/students/urls.py:
router.register(r"", StudentViewSet, basename="students")  # <- vacio aqui

# Media protegida con JWT (NO usar static() de Django)
path("media/<path:path>", protected_media),
```

### config/celery.py
```python
# Default PROD (no dev) para coincidir con wsgi.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
```

### config/__init__.py
```python
# OBLIGATORIO para que Celery funcione
from .celery import app as celery_app
__all__ = ("celery_app",)
```

---

## Permisos en TODOS los ViewSets

CRITICO: TODOS los ViewSets deben tener permission_classes explicito. Pattern:
```python
class MyViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminJardinOrAbove()]
        return [IsAuthenticated()]
```

Acciones destructivas (ejecutar migracion, cleanup, cerrar mes) requieren IsSuperadmin.
ReportViewSet requiere IsAdminJardinOrAbove (PROFESOR no puede descargar Excel con DNIs).

---

## Serializers - read_only_fields obligatorios

TODOS los campos que se setean automaticamente en perform_create/acciones deben ser read_only:
- `student` en GuardianSerializer
- `teacher` en TeacherContractSerializer
- `contract` en TeacherPaymentSerializer
- `created_by` en EnrollmentSerializer
- `creado_por` en CashTransactionSerializer
- `enviado_por`, `enviado`, `fecha_envio` en CommunicationSerializer
- `registrado_por` en AttendanceSerializer y PaymentSerializer

Usar `serializers.StringRelatedField(source="fk_field")` para mostrar nombres de FK (NO `source="fk.__str__"` que es fragil).

---

## Frontend React - Detalles criticos

### api.js - Usar Vite proxy, no URL directa
```javascript
// En dev: rutas relativas van por Vite proxy (/api -> localhost:8000)
// En prod: VITE_API_URL apunta al backend de Railway
const API_BASE = import.meta.env.VITE_API_URL || "";

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
});
```

### vite.config.js - Proxy
```javascript
server: {
    port: 3000,
    proxy: {
        "/api": { target: "http://localhost:8000", changeOrigin: true },
    },
},
```

### main.jsx - Wrapper de Ant Design App
```jsx
import { App as AntApp } from "antd";
// OBLIGATORIO para que App.useApp() funcione en todas las paginas
<ConfigProvider ...>
  <AntApp>
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  </AntApp>
</ConfigProvider>
```

### MainLayout.jsx - selectedKeys con path split
```jsx
// Para que rutas anidadas como /alumnos/123 resalten "Alumnos" en el menu
selectedKeys={[`/${location.pathname.split("/")[1]}`]}
```

### App.jsx - Ruta 404 catch-all
```jsx
<Route path="*" element={<Navigate to="/dashboard" replace />} />
```

### Endpoints del frontend que deben coincidir con el backend:
```
/students/                      -> GET, POST
/students/{id}/                 -> GET, PUT, DELETE
/students/{id}/guardians/       -> GET, POST (NO "apoderados")
/students/{id}/medical-record/  -> GET, PUT (NO "ficha-medica")
/teachers/{id}/contracts/       -> GET, POST
/cashflow/cash-transactions/    -> GET, POST (NO "transactions")
/cashflow/monthly-closures/     -> GET (NO "closures")
/cashflow/cash-categories/      -> GET (NO "categories")
/payments/{id}/registrar-pago/  -> PATCH (NO POST)
/reports/morosidad-excel/       -> GET (NO "morosidad")
/reports/alumnos-excel/         -> GET
/reports/asistencia-excel/      -> GET
/reports/cashflow-excel/        -> GET
/dashboard/resumen/             -> GET
/dashboard/historico/           -> GET
/migrations/preview/            -> GET
/migrations/ejecutar/           -> POST
```

### Paginas (13):
Login, Dashboard (KPIs + Chart.js), Students (tabla CRUD), StudentDetail (tabs: apoderados, ficha medica), Teachers, Classrooms, Enrollments, Payments (registrar pago PATCH, QR, tags color por estado), Cashflow (2 tabs: transacciones + cierres), Attendance (seleccionar aula + fecha, registro masivo), Communications (crear + enviar con Popconfirm), Reports (4 cards descarga Excel), Migrations (preview + ejecutar con Popconfirm)

---

## Docker y Deploy

### docker-compose.yml
```yaml
# SIN "version:" (deprecated)
services:
  db:
    image: postgres:16-alpine
    ports:
      - "5433:5432"    # Puerto 5433 para evitar conflicto con PostgreSQL nativo
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
  redis:
    image: redis:7-alpine
  backend:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
```

### Dockerfile backend
```dockerfile
FROM python:3.12-slim
# Solo libpq-dev para psycopg2 (xhtml2pdf es puro Python, sin deps de sistema)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
```

### vercel.json
```json
{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
```

---

## Setup inicial despues de construir

```bash
# 1. Levantar DB y Redis
docker compose up -d db redis

# 2. Instalar backend
cd backend && python -m venv venv && source venv/Scripts/activate
pip install -r requirements/dev.txt

# 3. Generar y aplicar migraciones
python manage.py makemigrations
python manage.py migrate_schemas --shared

# 4. Crear tenant y usuarios (con auditlog desconectado para evitar error de cross-schema)
# El superuser debe existir en AMBOS schemas (publico y tenant)

# 5. Instalar frontend
cd frontend && npm install

# 6. Levantar
# Backend: DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py runserver 0.0.0.0:8000
# Frontend: npm run dev (puerto 3000, proxy a 8000)
```

---

## Testing (crear despues del scaffolding)

- pytest + factory-boy + pytest-django
- settings/test.py con: locmem email, eager celery, MD5 hasher, throttle desactivado
- conftest.py con fixtures tenant-aware (crear schema test, set_tenant)
- ~170 tests unitarios + API
- E2E: Playwright TypeScript (24 TCs, 7 Page Objects)
- Performance: k6 (8 scripts: smoke, load, stress, spike, soak + especificos)

---

## Resumen de lo que NO hacer (lecciones aprendidas)

1. NO usar django-unfold (incompatible con Python 3.13+)
2. NO usar weasyprint (dependencias de sistema pesadas)
3. NO usar `STATICFILES_STORAGE` (deprecated, usar `STORAGES`)
4. NO usar `LANGUAGE_CODE = "es-pe"` (no hay traducciones, usar `"es"`)
5. NO usar `SECURE_BROWSER_XSS_FILTER` (deprecated)
6. NO usar `source="fk.__str__"` en serializers (usar StringRelatedField)
7. NO usar `float()` en Decimal de reportes financieros
8. NO usar `sum()` Python en querysets (usar `aggregate(Sum())`)
9. NO usar `chr(64+col)` para columnas Excel (usar `get_column_letter()`)
10. NO hacer loop mes por mes en cashflow summary (usar ExtractMonth + annotate)
11. NO olvidar endpoint /users/me/ (el frontend lo necesita post-login)
12. NO usar URL directa al backend desde React (usar Vite proxy por tema de Host header con django-tenants)
13. NO hardcodear SECRET_KEY con fallback en produccion
14. NO usar on_delete=CASCADE en attendance.classroom (usar PROTECT)
15. NO dejar ViewSets sin permission_classes explicito
16. NO dejar campos auto-asignados como writables en serializers
17. NO hacer .delete() fisico en cleanup de egresados (usar soft-delete/anonimizacion)
18. NO permitir cleanup con years_to_keep=0
19. NO olvidar crear superuser en AMBOS schemas (publico y tenant)
20. NO duplicar prefijos en URLs (config/urls.py prefix + router.register prefix)
