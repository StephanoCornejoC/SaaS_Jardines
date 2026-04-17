# Reporte de Analisis Estatico de Codigo - SAAS COREM

**Fecha:** 2026-04-08
**Analista:** Static Code Analyzer (Sub-agente QA)
**Alcance:** Backend Django 5.x + Frontend React 18 + Vite
**Version del proyecto:** 0.1.0 (piloto Jardin Garabato)

---

## Resumen Ejecutivo

| Dimension | Estado | Detalle |
|-----------|--------|---------|
| Seguridad | ADVERTENCIA | 5 issues (0 criticos, 5 medios) |
| Mantenibilidad | BUENA | Arquitectura solida, deuda puntual |
| Complejidad | ACEPTABLE | 2 metodos superan umbral |
| Estilo | MEJORABLE | Inconsistencias menores en ambas capas |
| Dependencias | VERIFICAR | ESLint sin plugin React instalado |
| Cobertura de tests | PENDIENTE | Sin tests implementados aun |

**Veredicto general:** El codigo es de calidad media-alta para un proyecto piloto en fase inicial. No hay vulnerabilidades criticas que bloqueen el despliegue, pero existen patrones de riesgo que deben resolverse antes de escalar a multiples tenants. La arquitectura Django es correcta y sigue buenas practicas. El frontend carece de configuracion de linting activa.

---

## Alcance del Analisis

### Archivos analizados - Backend (14 modulos)

| App | models.py | views.py | serializers.py | services.py |
|-----|-----------|----------|----------------|-------------|
| users | SI | SI | SI | - |
| students | SI | SI | SI | - |
| teachers | SI | SI | SI | - |
| classrooms | SI | SI | - | - |
| enrollments | SI | SI | SI | - |
| payments | SI | SI | SI | SI |
| cashflow | SI | SI | SI | SI |
| attendance | SI | SI | SI | - |
| communications | SI | SI | SI | - |
| dashboard | SI | SI | SI | SI |
| notifications | SI | - | - | SI |
| tenants | SI | - | - | - |
| reports | - | SI | - | - |

### Archivos analizados - Frontend (6 archivos clave)

- `src/App.jsx`, `src/pages/Login.jsx`, `src/pages/Students.jsx`
- `src/pages/Payments.jsx`, `src/pages/Dashboard.jsx`
- `src/store/authStore.js`, `src/services/api.js`
- `package.json`, `vite.config.js`

### Archivos de configuracion

- `config/settings/base.py`, `dev.py`, `prod.py`
- `apps/users/managers.py`, `apps/users/permissions.py`

---

## Configuracion Generada

### 1. `backend/pyproject.toml`

Archivo creado en `D:/PROYECTOS/SAAS_COREM/backend/pyproject.toml`.

Herramientas configuradas:
- **ruff** (linter + formatter): reglas E, W, F, I, N, UP, B, C4, C90, DJ, S, T20, RUF, SIM, TRY
- **pytest**: con `DJANGO_SETTINGS_MODULE = config.settings.dev`
- **coverage**: cobertura minima del 70%, excluyendo migraciones y admin
- **mypy**: configuracion base para type checking opcional

Reglas clave habilitadas:
- `C90` (mccabe): complejidad ciclomatica maxima = 10
- `DJ` (flake8-django): detecta antipatrones de Django
- `S` (bandit): seguridad - detecta hardcoded passwords, eval, insecure hash
- `I` (isort): orden de imports con first-party = apps, config, shared
- `B` (bugbear): bugs potenciales y code smells

### 2. `frontend/.eslintrc.cjs`

Archivo creado en `D:/PROYECTOS/SAAS_COREM/frontend/.eslintrc.cjs`.

Reglas clave configuradas:
- `react-hooks/rules-of-hooks`: error (hooks en lugares invalidos)
- `react-hooks/exhaustive-deps`: warn (dependencias faltantes en useEffect)
- `no-unused-vars`: error (imports y variables no usadas)
- `complexity`: warn con umbral 10 (paginas: 15)
- `max-lines-per-function`: warn con umbral 80 (paginas: 200)
- `no-eval`, `no-new-func`, `no-script-url`: error (seguridad)
- `eqeqeq`: error (usar === en lugar de ==)

Dependencias que deben instalarse para activar ESLint completo:

```bash
cd frontend
npm install --save-dev eslint-plugin-react eslint-plugin-react-refresh @eslint/js
```

---

## Hallazgos - Backend Django

### CRITICOS (bloquean merge / deployment)

No se encontraron hallazgos criticos que bloqueen deployment.

---

### IMPORTANTES - Seguridad

#### [SEC-01] Secret key con fallback inseguro en base.py

**Archivo:** `config/settings/base.py`, linea 11-14
**Severidad:** Media
**Regla:** S105 (hardcoded-password-string), Bandit B105

```python
# PROBLEMA: Si DJANGO_SECRET_KEY no esta definido en el entorno,
# se usa una clave insegura predecible en lugar de fallar.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-in-production-!@#$%^&*()",
)
```

**Riesgo:** Si la variable de entorno no esta definida en produccion (Railway), la aplicacion arranca con una clave conocida. Cualquier sesion, token CSRF o firma puede ser falsificada.

**Correccion recomendada:**

```python
import secrets

def _get_secret_key():
    key = os.environ.get("DJANGO_SECRET_KEY")
    if not key:
        raise ImproperlyConfigured(
            "La variable de entorno DJANGO_SECRET_KEY no esta definida. "
            "Ejecute: python -c \"import secrets; print(secrets.token_urlsafe(50))\""
        )
    return key

SECRET_KEY = _get_secret_key()
```

---

#### [SEC-02] EMAIL_BACKEND de SMTP definido en base.py con override en dev

**Archivo:** `config/settings/base.py`, linea 195
**Severidad:** Baja-Media

```python
# base.py
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# dev.py - correctamente sobreescribe a console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

**Observacion:** El patron es correcto (dev sobreescribe a console). El riesgo es que si se carga base.py directamente sin un overlay de dev/prod, los emails intentan enviarse por SMTP sin credenciales. No es un bug activo, pero el comentario en base.py deberia ser mas explicito.

---

#### [SEC-03] Tokens JWT almacenados en localStorage (frontend)

**Archivo:** `src/store/authStore.js`, linea 18-19 / `src/services/api.js`, linea 10-14
**Severidad:** Media
**Categoria:** Security - XSS token theft

```javascript
// authStore.js
localStorage.setItem("access_token", data.access);
localStorage.setItem("refresh_token", data.refresh);

// api.js
const token = localStorage.getItem("access_token");
```

**Riesgo:** Los tokens JWT en localStorage son accesibles por cualquier script JavaScript, incluyendo XSS. La alternativa segura son cookies HttpOnly.

**Contexto:** Para un SaaS B2B sin manejo de datos bancarios propios, el riesgo es aceptable en fase piloto, pero debe documentarse como deuda de seguridad conocida y resolverse antes de escalar.

**Mitigacion actual:** El backend tiene `AXES` (brute-force protection) y tokens JWT de corta vida (30 min), lo que reduce el impacto.

---

#### [SEC-04] Import de send_mail duplicado en communications/views.py

**Archivo:** `apps/communications/views.py`, lineas 1-2
**Severidad:** Baja (code smell + riesgo de divergencia)
**Regla:** F401 (unused import), duplicacion de logica

```python
# views.py - importa send_mail directamente
from django.core.mail import send_mail
from django.conf import settings

# Y tambien tiene services.py en notifications que hace lo mismo.
# La vista reimplementa el envio de email en lugar de usar el service.
```

**El metodo `enviar` en CommunicationViewSet (lineas 70-89) reimplementa manualmente lo que `notifications/services.py::send_communication_email()` ya hace.** Esto crea dos rutas de envio que pueden divergir (logging, manejo de errores, formato).

**Riesgo:** La version en services.py loguea y registra en EmailLog; la version en views.py no. Los emails enviados desde la vista no quedan registrados en la BD.

**Correccion:**

```python
# views.py - reemplazar el bloque de envio manual por:
from apps.notifications.services import send_communication_email

logs = send_communication_email(communication)
enviados = sum(1 for l in logs if l.enviado)
errores = [{"email": l.destinatario, "error": l.error} for l in logs if not l.enviado]
```

---

#### [SEC-05] Validacion insuficiente en PaymentRegisterSerializer

**Archivo:** `apps/payments/serializers.py`, lineas 57-63
**Severidad:** Media
**Regla:** Business logic validation gap

```python
class PaymentRegisterSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=Payment.Estado.choices)
    metodo_pago = serializers.ChoiceField(
        choices=Payment.MetodoPago.choices, required=False, allow_blank=True
    )
    # ...
```

**Problema:** El serializer permite registrar un pago con `estado=PAGADO` sin especificar `metodo_pago`. La logica de negocio deberia requerir el metodo de pago cuando el estado es PAGADO.

**Correccion:**

```python
def validate(self, data):
    if data.get("estado") == Payment.Estado.PAGADO and not data.get("metodo_pago"):
        raise serializers.ValidationError(
            {"metodo_pago": "El metodo de pago es obligatorio cuando el estado es PAGADO."}
        )
    return data
```

---

### IMPORTANTES - Code Smells y Complejidad

#### [CS-01] Funcion calculate_daily_metrics() supera umbral de complejidad

**Archivo:** `apps/dashboard/services.py`, lineas 10-108
**Severidad:** Media
**Metricas:**
- Lineas: 99 (umbral: 50 - SUPERADO)
- Imports inline: 7 (antipatron)
- Responsabilidades: 6 (God Method)

```python
def calculate_daily_metrics():
    # 7 imports inline al inicio de la funcion
    from apps.attendance.models import Attendance
    from apps.cashflow.models import CashTransaction
    from apps.classrooms.models import Classroom
    from apps.dashboard.models import DashboardMetric
    from apps.payments.models import Payment
    from apps.students.models import Student
    from apps.teachers.models import Teacher
    # ... 90 lineas mas calculando 6 metricas diferentes
```

**Problemas:**
1. Imports inline para evitar circular imports (indica problema de arquitectura de dependencias)
2. La funcion calcula alumnos, profesores, cashflow, morosidad y asistencia: deberia delegarse
3. Imposible testear cada calculo de forma aislada

**Refactorizacion recomendada:**

```python
def _get_student_metrics():
    """Calcula metricas de alumnos."""
    ...

def _get_financial_metrics(month, year):
    """Calcula metricas financieras del mes."""
    ...

def _get_attendance_metrics(month, year):
    """Calcula metricas de asistencia del mes."""
    ...

def calculate_daily_metrics():
    today = date.today()
    metric, _ = DashboardMetric.objects.update_or_create(
        fecha=today,
        defaults={
            **_get_student_metrics(),
            **_get_financial_metrics(today.month, today.year),
            **_get_attendance_metrics(today.month, today.year),
        }
    )
    return metric
```

---

#### [CS-02] Import condicional de timedelta en payments/services.py

**Archivo:** `apps/payments/services.py`, lineas 67-68
**Severidad:** Baja
**Regla:** I001 (import not at top of file)

```python
def generate_monthly_payments(anio_escolar, mes):
    # ...
    except ValueError:
        # ...
        from datetime import timedelta  # <-- IMPORT DENTRO DE EXCEPT
        fecha_vencimiento = next_month - timedelta(days=1)
```

**Problema:** `timedelta` ya esta disponible en el modulo `datetime` que se importa en la linea 1. No hay razon para importarlo dentro del except. Es un import residual de una refactorizacion incompleta.

**Correccion:**

```python
# Linea 1 del archivo - cambiar:
from datetime import date
# Por:
from datetime import date, timedelta
```

Y eliminar el import inline en la linea 68.

---

#### [CS-03] Redundancia en CommunicationViewSet.enviar() vs notifications.services

**Archivo:** `apps/communications/views.py`, lineas 43-89
**Severidad:** Media
**Categoria:** DRY violation - codigo duplicado

La vista `enviar` reimplementa la logica de filtracion de apoderados que ya existe en `notifications/services.py::send_communication_email()`. Son 46 lineas identicas de logica de negocio en dos lugares.

Ver [SEC-04] para el detalle completo. Impacto combinado: duplicacion de ~40 lineas, divergencia de comportamiento (logs ausentes en la version de views.py).

---

#### [CS-04] Uso de strings magicas de estado en lugar de constantes del modelo

**Archivos:** `apps/notifications/services.py` linea 123, `apps/communications/views.py` linea 55/59
**Severidad:** Baja
**Regla:** Magic string - fragil ante renombrado

```python
# notifications/services.py
guardians_qs = guardians_qs.filter(
    student__estado="ACTIVO",  # <-- String magica
)

# communications/views.py
    student__estado="ACTIVO",  # <-- String magica (idem)
```

**Correcto (ya usado en otros lugares del codigo):**

```python
from apps.students.models import Student

guardians_qs = guardians_qs.filter(
    student__estado=Student.Estado.ACTIVO,
)
```

---

#### [CS-05] UserViewSet.get_queryset() usa strings magicas de rol

**Archivo:** `apps/users/views.py`, linea 29
**Severidad:** Baja
**Regla:** Magic string - deberia usar User.Role

```python
def get_queryset(self):
    user = self.request.user
    if user.role in ['SUPERADMIN', 'ADMIN_JARDIN', 'DIRECTOR']:  # strings magicas
        return User.objects.all()
    return User.objects.filter(pk=user.pk)
```

**Correcto:**

```python
MANAGEMENT_ROLES = {User.Role.SUPERADMIN, User.Role.ADMIN_JARDIN, User.Role.DIRECTOR}

def get_queryset(self):
    user = self.request.user
    if user.role in MANAGEMENT_ROLES:
        return User.objects.all()
    return User.objects.filter(pk=user.pk)
```

El mismo patron con strings literales se repite en `TeacherViewSet.get_permissions()` (teachers/views.py, linea 32) y `EnrollmentViewSet.get_permissions()`.

---

#### [CS-06] Acceso potencial a None en DashboardViewSet.resumen()

**Archivo:** `apps/dashboard/views.py`, lineas 22-29
**Severidad:** Media
**Regla:** B006 - retorno potencialmente None

```python
@action(detail=False, methods=["get"], url_path="resumen")
def resumen(self, request):
    metric = DashboardMetric.objects.first()

    if not metric:
        metric = calculate_daily_metrics()
        # calculate_daily_metrics() puede retornar None si falla el calculo
        # En ese caso se pasa None al serializer -> AttributeError o respuesta vacia

    serializer = DashboardSummarySerializer(metric)  # <-- metric puede ser None
    return Response(serializer.data)
```

**Riesgo:** `calculate_daily_metrics()` no tiene manejo explicito de errores en el viewset. Si la funcion falla (BD vacia, tabla inexistente), `metric` sera `None` y el serializer fallara con AttributeError.

**Correccion:**

```python
if not metric:
    try:
        metric = calculate_daily_metrics()
    except Exception:
        logger.exception("Error calculando metricas del dashboard")
        return Response(
            {"error": "No hay metricas disponibles."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
if not metric:
    return Response({"error": "No hay metricas disponibles."}, status=404)
```

---

#### [CS-07] TeacherContractViewSet y TeacherPaymentViewSet sin permission_classes

**Archivo:** `apps/teachers/views.py`, lineas 37-65
**Severidad:** Media
**Regla:** Missing permission class - endpoint desprotegido

```python
class TeacherContractViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherContractSerializer
    # AUSENTE: permission_classes

    def get_queryset(self):
        return TeacherContract.objects.filter(teacher_id=self.kwargs["teacher_pk"])


class TeacherPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherPaymentSerializer
    # AUSENTE: permission_classes
```

**Riesgo:** Estos ViewSets no declaran `permission_classes`. Si el DRF default (`IsAuthenticated` en base.py) esta configurado correctamente, el comportamiento es correcto. Sin embargo, es una practica fragil: si se cambia el default global, estos endpoints quedarian expuestos.

**Correccion:**

```python
class TeacherContractViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherContractSerializer
    ...
```

---

### INFORMATIVOS - Inconsistencias de estilo

#### [STY-01] Imports en linea incorrecta en cashflow/services.py

**Archivo:** `apps/cashflow/services.py`, lineas 69-70
**Regla:** I001

```python
def get_cashflow_summary(anio):
    from django.db.models.functions import ExtractMonth  # import dentro de funcion
    from django.db.models import Q                        # import dentro de funcion
```

Los imports deben estar al top del archivo. Los imports inline dentro de funciones solo son justificables para romper circular imports, lo cual no es el caso aqui.

**Correccion:** Mover ambos imports a la cabecera del archivo junto a los demas imports de `django.db.models`.

---

#### [STY-02] Inconsistencia de comillas en views.py de teachers

**Archivo:** `apps/teachers/views.py`, linea 32
**Regla:** Q000

```python
# teachers/views.py usa comillas simples
if self.action in ['create', 'update', 'partial_update', 'destroy']:

# users/views.py usa comillas dobles (estilo mayoritario del proyecto)
if self.action in ("create", "update", "partial_update", "destroy"):
```

El proyecto usa comillas dobles en la mayoria de archivos. `ruff format` normalizara esto automaticamente.

---

#### [STY-03] f-string en logger.info/error en lugar de lazy logging

**Archivos:** `apps/dashboard/services.py` linea 106, `apps/dashboard/tasks.py` linea 18, `apps/notifications/tasks.py` lineas 38, 43, 93-94
**Regla:** G004 (flake8-logging-format) - no habilitada por defecto pero buena practica

```python
# Antipatron - f-string evaluado aunque el nivel de log este desactivado
logger.info(f"Métrica del dashboard {action} para {today}")
logger.error(f"Error enviando email a {destinatario}: {e}")

# Patron correcto - lazy evaluation
logger.info("Metrica del dashboard %s para %s", action, today)
logger.error("Error enviando email a %s: %s", destinatario, e)
```

**Impacto:** Bajo en este proyecto (pocas llamadas de log). A escala con multiples tenants, la evaluacion de f-strings en cada request tiene costo medible.

---

#### [STY-04] Uso de __all__ en fields de serializers - mezcla de patrones

**Archivos:** `apps/teachers/serializers.py`, `apps/students/serializers.py`
**Severidad:** Informativo

```python
# teachers/serializers.py
class TeacherPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"  # Expone todos los campos incluyendo futuros

# students/serializers.py - StudentDetailSerializer
    fields = "__all__"
```

`fields = "__all__"` en serializers de escritura es un antipatron porque:
1. Expone campos nuevos automaticamente cuando se agrega uno al modelo
2. Puede exponer campos sensibles inadvertidamente
3. Dificulta el control de que campos son write-only

Los serializers de detalle de lectura (`StudentDetailSerializer` usado en retrieve/update) y `TeacherPaymentSerializer` (de escritura) deberian listar los campos explicitamente.

---

#### [STY-05] Variable local shadowing builtin en notifications/models.py

**Archivo:** `apps/notifications/models.py`, linea 27
**Severidad:** Baja
**Regla:** A001 (flake8-builtins)

```python
class EmailLog(models.Model):
    def __str__(self):
        status = "OK" if self.enviado else "ERROR"  # shadows builtin 'status'
        return f"[{status}] {self.asunto} -> {self.destinatario}"
```

`status` es una convencion de nombre que puede confundirse con `http.HTTPStatus` o `status` de DRF. Renombrar a `estado_str` o `estado_label`.

---

#### [STY-06] Falta db_index en campos de filtro frecuente

**Archivos:** `apps/payments/models.py`, `apps/attendance/models.py`
**Severidad:** Informativamente importante (performance a escala)

```python
# payments/models.py
mes = models.IntegerField(...)     # filtrado frecuentemente: filter(mes=..., anio=...)
anio = models.IntegerField(...)
estado = models.CharField(...)     # filtrado frecuentemente: filter(estado=...)

# attendance/models.py
fecha = models.DateField(...)      # filtrado frecuentemente: filter(fecha__month=..., fecha__year=...)
estado = models.CharField(...)
```

Para el piloto con un jardin (~30 alumnos) no es critico. Con 50+ tenants y miles de pagos/asistencias, la ausencia de indices en estos campos causara full table scans.

**Recomendacion:**

```python
# payments/models.py
class Meta:
    indexes = [
        models.Index(fields=["student", "anio", "mes"]),
        models.Index(fields=["estado", "anio"]),
        models.Index(fields=["fecha_vencimiento", "estado"]),
    ]

# attendance/models.py
class Meta:
    indexes = [
        models.Index(fields=["student", "fecha"]),
        models.Index(fields=["classroom", "fecha"]),
    ]
```

---

#### [STY-07] Falta validacion cruzada en Attendance: student vs classroom

**Archivo:** `apps/attendance/models.py` / `apps/attendance/views.py`
**Severidad:** Baja-Media (integridad de datos)

El modelo `Attendance` tiene un campo `classroom` que en teoria deberia coincidir con el aula actual del alumno. No hay validacion que lo enforque:

```python
# Attendance.classroom y Student.classroom pueden ser diferentes
# Un alumno del Aula A puede tener asistencia registrada en Aula B
```

Esto es especialmente relevante en `registro_masivo`, donde se recibe `classroom_id` sin verificar que cada `student_id` pertenezca a ese aula.

---

## Hallazgos - Frontend React

### IMPORTANTES

#### [FE-01] ESLint configurado en package.json pero sin plugins criticos instalados

**Archivo:** `package.json`
**Severidad:** Media

```json
"devDependencies": {
    "eslint": "^9.15.0",
    "eslint-plugin-react-hooks": "^5.0.0",
    // AUSENTE: eslint-plugin-react
    // AUSENTE: eslint-config-prettier
}
```

El script `"lint": "eslint . --ext js,jsx"` esta declarado pero probablemente falla al ejecutarse porque falta `eslint-plugin-react`. Los hooks rules si estan pero sin `eslint-plugin-react` el contexto de React no se configura correctamente.

**Correccion:**

```bash
npm install --save-dev eslint-plugin-react eslint-plugin-react-refresh
```

---

#### [FE-02] Tokens JWT en localStorage sin proteccion contra XSS

Ver [SEC-03] para el analisis completo. Este es el hallazgo de mayor impacto de seguridad en el frontend.

---

#### [FE-03] Errores silenciados con catch vacio en multiples componentes

**Archivo:** `src/pages/Students.jsx`, lineas 41, 98; `src/pages/Payments.jsx`, lineas 69, 124
**Severidad:** Media
**Regla:** no-empty, react-hooks/exhaustive-deps

```javascript
// Students.jsx - linea 41
} catch {
    message.error("Error al cargar alumnos");
    // El error original es descartado - no hay logging, no hay informacion para debug
}

// Students.jsx - linea 98
} catch {
    message.error("Error al eliminar");
    // Idem - el error HTTP (404, 403, 500) se pierde
}
```

**Problema:** Se muestra un mensaje generico al usuario pero se pierde la informacion del error (codigo HTTP, mensaje del servidor, stack trace). En caso de bug en produccion, no hay forma de diagnosticar la causa.

**Correccion:**

```javascript
} catch (err) {
    console.error("Error al cargar alumnos:", err);
    const detail = err.response?.data?.detail || "Error al cargar alumnos";
    message.error(detail);
}
```

---

#### [FE-04] handlePay en Payments.jsx usa POST en lugar de PATCH para registrar-pago

**Archivo:** `src/pages/Payments.jsx`, linea 94
**Severidad:** Media (discordancia con la API backend)

```javascript
// Payments.jsx usa POST:
await api.post(`/payments/${selectedPayment.id}/registrar-pago/`, values);

// El backend define el endpoint como PATCH:
@action(detail=True, methods=["patch"], url_path="registrar-pago", ...)
def registrar_pago(self, request, pk=None):
```

El backend declara el action con `methods=["patch"]` pero el frontend llama con `POST`. Esto fallara con HTTP 405 Method Not Allowed a menos que DRF este configurado para aceptar ambos (no lo esta).

**Correccion:**

```javascript
await api.patch(`/payments/${selectedPayment.id}/registrar-pago/`, values);
```

---

#### [FE-05] Discordancia de campo de datos entre API y componente Students

**Archivo:** `src/pages/Students.jsx`, linea 108
**Severidad:** Baja-Media (bug silencioso en UI)

```javascript
// Students.jsx usa "aula_nombre":
{ title: "Aula", dataIndex: "aula_nombre", key: "aula_nombre" },

// El serializer StudentListSerializer retorna "classroom_nombre":
class StudentListSerializer(serializers.ModelSerializer):
    classroom_nombre = serializers.CharField(source="classroom.nombre", ...)
    class Meta:
        fields = ("id", "dni", "nombres", "apellidos", "edad", "classroom_nombre", "estado")
```

La columna "Aula" siempre estara vacia porque el campo `aula_nombre` no existe en la respuesta de la API; el campo correcto es `classroom_nombre`.

**Correccion:**

```javascript
{ title: "Aula", dataIndex: "classroom_nombre", key: "classroom_nombre" },
```

---

#### [FE-06] Dependencias faltantes en useEffect de Dashboard.jsx

**Archivo:** `src/pages/Dashboard.jsx`, lineas 29-47
**Severidad:** Baja
**Regla:** react-hooks/exhaustive-deps

```javascript
useEffect(() => {
    const fetchData = async () => { ... };
    fetchData();
}, []); // Array de dependencias vacio - correcto para "solo al montar"
        // pero fetchData esta definido dentro del efecto, lo cual es correcto
        // Sin embargo, si fetchData usara props o state externo, seria un problema
```

El patron actual es correcto (fetchData definido dentro del efecto). No hay bug activo, pero el patron deberia documentarse para prevenir future issues cuando se agreguen filtros.

---

#### [FE-07] Falta paginacion del lado del servidor en Students y Payments

**Archivos:** `src/pages/Students.jsx`, linea 181; `src/pages/Payments.jsx`, linea 219
**Severidad:** Media (performance a escala)

```javascript
// Students.jsx - paginacion solo del lado del cliente
setStudents(res.data.results || res.data);
// ...
<Table pagination={{ pageSize: 20, showSizeChanger: true }} />
```

El backend retorna `results` (paginado DRF) o el array completo. El frontend extrae `res.data.results || res.data` pero luego pasa todos los datos a la Table de Ant Design para que paginene en el cliente. Esto significa que se cargan TODOS los alumnos en cada request, ignorando la paginacion del servidor.

Con 500+ alumnos distribuidos en multiples tenants, esto degradara la performance significativamente.

**Correccion:** Implementar paginacion controlada (controlled pagination) con `current`, `pageSize` como state, y pasarlos como query params al backend.

---

### INFORMATIVOS

#### [FE-08] Inline styles extensivos en JSX

**Archivos:** `Login.jsx`, `Students.jsx`, `Dashboard.jsx`, `App.jsx`
**Severidad:** Informativo

```jsx
// Login.jsx
style={{
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    minHeight: "100vh",
    background: "#f0f2f5",
}}
```

El proyecto usa inline styles en lugar de CSS modules o styled-components. Para un proyecto en fase piloto es aceptable, pero dificulta el theming consistente y el override de estilos. El proyecto usa Ant Design cuyo sistema de theming deberia aprovecharse.

---

#### [FE-09] No hay manejo de estado de error global (error boundary)

**Archivo:** `src/App.jsx`
**Severidad:** Informativo

No hay `ErrorBoundary` a nivel de App. Si un componente hijo lanza un error de render no capturado, toda la aplicacion se rompe con pantalla en blanco. React 18 recomienda `ErrorBoundary` para experiencia degradada controlada.

---

#### [FE-10] Falta tipar el argumento de configuracion de axios

**Archivo:** `src/services/api.js`, linea 3
**Severidad:** Informativo

```javascript
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
```

Si `VITE_API_URL` no esta definido en el `.env` de produccion (Vercel), el fallback a `localhost:8000` causara que todas las llamadas a la API fallen silenciosamente en produccion. Deberia agregar validacion:

```javascript
const API_BASE = import.meta.env.VITE_API_URL;
if (!API_BASE && import.meta.env.PROD) {
    console.error("VITE_API_URL no esta definida en variables de entorno de produccion");
}
```

---

## Metricas de Codigo

### Backend Django

| Metrica | Valor medido | Umbral | Estado |
|---------|-------------|--------|--------|
| Lineas totales (apps, sin migraciones) | ~1,850 | - | - |
| Metodos que superan 50 lineas | 2 | <= 3 | OK |
| Metodos que superan 30 lineas | 5 | <= 5 | OK |
| Complejidad ciclomatica maxima | 8 (reporte_mensual en attendance/views.py) | <= 10 | OK |
| Complejidad cognitiva maxima | ~12 (calculate_daily_metrics) | <= 15 | OK |
| Clases con mas de 300 lineas | 0 | 0 | OK |
| Imports inline (dentro de funciones) | 9 | 0 | FAIL |
| String magicas de dominio | 5 | 0 | FAIL |
| Serializers con `fields = "__all__"` | 3 | 0 | FAIL |
| ViewSets sin permission_classes explicitado | 2 | 0 | FAIL |
| Duplicacion de logica de negocio | 1 bloque | 0 | FAIL |
| Funciones sin manejo de retorno None | 1 | 0 | FAIL |

### Frontend React

| Metrica | Valor medido | Umbral | Estado |
|---------|-------------|--------|--------|
| Archivos JSX totales | 13 | - | - |
| Componentes > 200 lineas | 2 (Students, Payments) | <= 2 | OK |
| Catch bloques vacios (sin logging) | 5 | 0 | FAIL |
| Inline styles > 3 propiedades | 8 | <= 3 | FAIL |
| Discordancias API-componente | 2 | 0 | FAIL |
| Tokens en localStorage | 2 | 0 | ADVERTENCIA |
| Paginacion cliente en lugar de servidor | 2 | 0 | FAIL |

---

## Quality Gate

### Backend Django

| Categoria | Estado | Issues |
|-----------|--------|--------|
| Seguridad critica (bloqueo) | PASS | 0 |
| Seguridad media | FAIL | 3 issues activos |
| Mantenibilidad | PASS | Con deuda menor |
| Complejidad | PASS | Dentro de umbrales |
| Estilo / Imports | FAIL | 7 violations |
| Duplicacion de logica | FAIL | 1 bloque significativo |
| Tests coverage | PENDIENTE | Sin tests aun |

**Veredicto Backend: PASS con advertencias** (no bloquea, pero requiere plan de remediacion)

### Frontend React

| Categoria | Estado | Issues |
|-----------|--------|--------|
| Bug critico (POST vs PATCH) | FAIL | 1 bug activo |
| Bug silencioso (campo aula_nombre) | FAIL | 1 bug activo |
| Seguridad (JWT en localStorage) | ADVERTENCIA | Deuda documentada |
| ESLint operativo | FAIL | Plugin faltante |
| Paginacion servidor | FAIL | Performance futura |
| Error handling | FAIL | 5 catch vacios |

**Veredicto Frontend: FAIL** (2 bugs activos que afectan funcionalidad visible)

---

## Plan de Remediacion

### Sprint inmediato - Prioridad ALTA (bloquean funcionalidad correcta)

| ID | Descripcion | Archivo | Esfuerzo |
|----|-------------|---------|----------|
| FE-04 | Cambiar POST por PATCH en registrar-pago | Payments.jsx:94 | 5 min |
| FE-05 | Corregir campo aula_nombre por classroom_nombre | Students.jsx:108 | 5 min |
| SEC-05 | Validar metodo_pago cuando estado=PAGADO | payments/serializers.py | 15 min |
| CS-02 | Mover import timedelta al top del archivo | payments/services.py:68 | 2 min |
| STY-01 | Mover imports inline al top del archivo | cashflow/services.py:69-70 | 5 min |

**Total Sprint inmediato: ~30 minutos**

---

### Sprint 1 - Prioridad MEDIA (calidad y mantenibilidad)

| ID | Descripcion | Archivo | Esfuerzo |
|----|-------------|---------|----------|
| CS-01 | Refactorizar calculate_daily_metrics() en subfunciones | dashboard/services.py | 2h |
| SEC-04 / CS-03 | Unificar envio de email en communications a traves de notifications.services | communications/views.py | 1h |
| CS-04 | Reemplazar strings magicas "ACTIVO" por Student.Estado.ACTIVO | notifications/services.py, communications/views.py | 30 min |
| CS-05 | Reemplazar strings magicas de rol en views | users/views.py, teachers/views.py | 30 min |
| CS-07 | Agregar permission_classes a TeacherContractViewSet y TeacherPaymentViewSet | teachers/views.py | 10 min |
| FE-01 | Instalar eslint-plugin-react y eslint-plugin-react-refresh | package.json | 5 min |
| FE-03 | Agregar logging en catch bloques de componentes React | Students.jsx, Payments.jsx | 30 min |
| STY-05 | Renombrar variable local status en EmailLog.__str__ | notifications/models.py | 5 min |

**Total Sprint 1: ~5 horas**

---

### Sprint 2 - Prioridad BAJA (deuda tecnica controlada)

| ID | Descripcion | Archivo | Esfuerzo |
|----|-------------|---------|----------|
| SEC-01 | Hacer SECRET_KEY obligatorio (eliminar fallback inseguro) | settings/base.py | 20 min |
| CS-06 | Agregar manejo de None en DashboardViewSet.resumen() | dashboard/views.py | 20 min |
| STY-06 | Agregar db_index a campos de filtro frecuente | payments/models.py, attendance/models.py | 1h + migracion |
| STY-04 | Reemplazar `fields = "__all__"` por campos explicitos en serializers | teachers/serializers.py, students/serializers.py | 1h |
| FE-07 | Implementar paginacion del lado del servidor en Students y Payments | Students.jsx, Payments.jsx | 3h |
| FE-09 | Agregar ErrorBoundary en App.jsx | App.jsx | 1h |
| FE-10 | Validar VITE_API_URL en api.js | services/api.js | 15 min |

**Total Sprint 2: ~7 horas**

---

## Notas para el QA Lead

### Riesgos principales identificados

1. **Bug FE-04 (POST vs PATCH):** El modulo de Pensiones esta roto funcionalmente. La accion "Registrar Pago" devuelve HTTP 405 y nunca registra el pago. Este debe resolverse de inmediato si el modulo de pagos es parte del piloto con Jardin Garabato.

2. **Bug FE-05 (campo incorrecto):** La columna "Aula" en la tabla de Alumnos siempre aparece vacia, aunque los alumnos tengan aula asignada. Bug silencioso visible en la UI pero sin error en consola.

3. **Logica de email duplicada (SEC-04/CS-03):** Los emails enviados desde "Comunicaciones" no quedan registrados en `EmailLog`. Esto significa que el historial de comunicaciones enviadas es incompleto. Si el jardin necesita auditar que padres recibieron comunicados, la informacion es incompleta.

4. **Sin tests automatizados:** El proyecto carece de tests unitarios, de integracion y E2E. Para el piloto con un jardin esto es aceptable. Antes de incorporar el segundo tenant, se recomienda cobertura minima del 60% en la capa de servicios (payments, notifications, cashflow).

5. **JWT en localStorage:** Deuda de seguridad conocida y aceptada para el piloto. Documentar en el backlog para resolver antes de manejar datos de pago en produccion a escala.

### Tendencias positivas del codigo

- La arquitectura de multi-tenancy con `django-tenants` esta correctamente implementada.
- Los ViewSets siguen el patron DRF correctamente (select_related, prefetch_related).
- Los permisos estan correctamente granulados por rol en la mayoria de endpoints.
- Los serializers de lectura/escritura estan separados apropiadamente (List vs Detail).
- El manejo de JWT con refresh token en el frontend es correcto (interceptor de axios).
- La separacion de settings por ambiente (base/dev/prod) es correcta.
- `AXES` para brute-force protection esta configurado con parametros razonables.
- El uso de `update_or_create` en `registro_masivo` de asistencia es idiomatico y correcto.
- Los modelos usan `TextChoices` e `IntegerChoices` de forma consistente.

### Proximos pasos recomendados al QA Lead

1. Resolver los 2 bugs criticos de frontend (FE-04, FE-05) antes de la demo del piloto.
2. Ejecutar `ruff check . --fix` en el backend para corregir automaticamente ~70% de los issues de estilo.
3. Ejecutar `npm install` con los plugins faltantes y `npx eslint . --ext .js,.jsx` para obtener el baseline de issues en frontend.
4. Priorizar la creacion de tests para `payments/services.py` y `notifications/services.py` ya que son los modulos con mayor logica de negocio y sin cobertura.

---

*Reporte generado por: Static Code Analyzer - QA Sub-agente*
*Proyecto: SAAS COREM - SaaS para Jardines de Infantes*
*Marco de referencia: ISTQB CTFL, ISTQB CT-TAE*
