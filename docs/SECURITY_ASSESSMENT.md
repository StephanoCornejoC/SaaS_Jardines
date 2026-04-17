# SECURITY ASSESSMENT REPORT - SAAS COREM
**Clasificacion:** CONFIDENCIAL - Solo uso interno
**Fecha:** 2026-04-08
**Analista:** Security Tester Sub-Agent (ISTQB Security / OWASP Testing Guide v4)
**Version del sistema:** Django 5.1 + django-tenants + DRF + SimpleJWT + React 18
**Deploy objetivo:** Railway.app (backend) + Vercel (frontend)
**Contexto de datos:** PII de menores de edad (DNI, fichas medicas, fotos, apoderados)

---

## RESUMEN EJECUTIVO

El sistema SAAS COREM procesa datos **altamente sensibles de menores de edad** (DNI, fichas medicas, fotografias, contactos de emergencia) bajo un modelo multi-tenant SaaS. El analisis manual del codigo fuente identifica **4 vulnerabilidades criticas**, **7 altas**, **6 medias** y **4 bajas**. El sistema cuenta con una base de seguridad sólida (Axes, AuditLog, HSTS, JWT con blacklist), pero presenta brechas importantes en control de acceso a PII, gestion de secretos, y falta de controles especificos para datos de menores.

### Distribucion de Hallazgos

| Severidad | Cantidad | CVSS Aprox. | Estado Pre-Deploy |
|-----------|----------|-------------|-------------------|
| CRITICO   | 4        | 9.0 - 10.0  | BLOQUEA RELEASE   |
| ALTO      | 7        | 7.0 - 8.9   | Remediar urgente  |
| MEDIO     | 6        | 4.0 - 6.9   | Proximo sprint    |
| BAJO      | 4        | < 4.0       | Backlog           |

---

## PARTE 1 - OWASP TOP 10 ASSESSMENT (2021)

### A01 - Broken Access Control

#### VULN-001 [CRITICO] - IDOR en endpoints de PII de menores sin restriccion de rol
**Archivo:** `backend/apps/students/views.py` - `StudentViewSet`, `GuardianViewSet`, `MedicalRecordViewSet`
**CVSS:** 9.1 (AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N)

```python
# PROBLEMA: Todo usuario autenticado puede leer, crear, actualizar y eliminar
# fichas medicas, apoderados y datos de cualquier alumno del tenant.
class StudentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]   # <-- sin restriccion de rol

class GuardianViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]   # <-- sin restriccion de rol

class MedicalRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]   # <-- sin restriccion de rol
    http_method_names = ["get", "post", "put", "patch"]  # permite escritura
```

**Impacto:** Un PROFESOR puede modificar fichas medicas (alergias, tipo de sangre), eliminar apoderados, o cambiar estado de cualquier alumno. En un contexto de datos de menores, esto es una violacion grave de privacidad y potencialmente de la normativa peruana de proteccion de datos (Ley 29733).

**Remediacion:**
```python
# students/views.py - Aplicar control granular por accion
class StudentViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsAdminJardinOrAbove()]
        # list/retrieve: cualquier autenticado del tenant
        return [IsAuthenticated()]

class MedicalRecordViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        # Ficha medica: lectura para PROFESOR/SECRETARIA, escritura solo DIRECTOR o superior
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsDirectorOrAbove()]
        return [IsAuthenticated()]
```

---

#### VULN-002 [CRITICO] - Ausencia de verificacion de ownership en GuardianViewSet
**Archivo:** `backend/apps/students/views.py` linea 38-39
**CVSS:** 9.1

```python
class GuardianViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # Filtra por student_pk del URL, pero NO verifica que ese student
        # pertenezca al tenant actual. En un escenario de misconfiguracion
        # del middleware de tenants, se puede acceder a apoderados de otro jardin.
        return Guardian.objects.filter(student_id=self.kwargs["student_pk"])
```

**Remediacion:** Agregar validacion explícita del tenant en el queryset:
```python
def get_queryset(self):
    # Verificar que el alumno existe en el schema actual (django-tenants lo garantiza
    # si el middleware funciona, pero defensivamente:)
    student = get_object_or_404(Student, pk=self.kwargs["student_pk"])
    return Guardian.objects.filter(student=student)
```

---

#### VULN-003 [ALTO] - Falta de object-level permission en UserViewSet
**Archivo:** `backend/apps/users/views.py` lineas 27-31
**CVSS:** 7.5

```python
def get_queryset(self):
    user = self.request.user
    if user.role in ['SUPERADMIN', 'ADMIN_JARDIN', 'DIRECTOR']:
        return User.objects.all()
    return User.objects.filter(pk=user.pk)
```

**Problema:** El DIRECTOR puede ver TODOS los usuarios del tenant. Aunque el endpoint de retrieve esta disponible para `IsAuthenticated`, un usuario normal puede enumerar IDs y intentar acceder directamente a `/api/v1/auth/users/{id}/`. No hay `has_object_permission` que restrinja esto.

**Remediacion:** Implementar `has_object_permission` en el permission class o en `get_object`.

---

#### VULN-004 [ALTO] - ReportViewSet expone PII masiva sin restriccion de rol
**Archivo:** `backend/apps/reports/views.py`
**CVSS:** 7.5

```python
class ReportViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]  # <-- cualquier PROFESOR descarga todo
```

Los reportes Excel contienen: DNI de todos los alumnos, datos financieros (morosidad), flujo de caja completo del jardin. Un PROFESOR no deberia tener acceso a datos financieros ni al listado masivo de DNIs.

**Remediacion:**
```python
@action(detail=False, methods=["get"], url_path="morosidad-excel",
        permission_classes=[IsAdminJardinOrAbove])
def morosidad_excel(self, request): ...

@action(detail=False, methods=["get"], url_path="cashflow-excel",
        permission_classes=[IsAdminJardinOrAbove])
def cashflow_excel(self, request): ...
```

---

#### VULN-005 [ALTO] - CashCategory y CashTransaction con permisos insuficientes
**Archivo:** `backend/apps/cashflow/views.py` lineas 22, 31
**CVSS:** 7.2

```python
class CashCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]   # cualquier rol puede crear/eliminar categorias

class CashTransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]   # cualquier rol puede crear transacciones financieras
```

**Impacto:** Un PROFESOR o SECRETARIA podria crear transacciones ficticias o eliminar categorias del sistema.

---

### A02 - Cryptographic Failures

#### VULN-006 [CRITICO] - Secret key inseguro en base.py con fallback hardcoded
**Archivo:** `backend/config/settings/base.py` lineas 11-14
**CVSS:** 9.8

```python
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-in-production-!@#$%^&*()",  # FALLBACK HARDCODED
)
```

**Impacto critico:** Si la variable de entorno `DJANGO_SECRET_KEY` no esta configurada en Railway, Django usara este valor conocido publicamente (esta en el repositorio). Esto compromete la firma de cookies de sesion, tokens CSRF y cualquier dato firmado criptograficamente. En combinacion con el codigo fuente, un atacante puede forjar sessions.

**Remediacion:**
```python
import sys

secret_key = os.environ.get("DJANGO_SECRET_KEY")
if not secret_key:
    if 'test' not in sys.argv:
        raise ValueError(
            "La variable de entorno DJANGO_SECRET_KEY no esta configurada. "
            "El sistema no puede iniciar sin una clave secreta valida."
        )
    secret_key = "test-only-insecure-key"
SECRET_KEY = secret_key
```

---

#### VULN-007 [MEDIO] - JWT lifetime en .env.example no coincide con base.py
**Archivo:** `backend/.env.example` lineas 22-23 vs `base.py` lineas 132-138

```
# .env.example:
ACCESS_TOKEN_LIFETIME_MINUTES=60   # 60 minutos
REFRESH_TOKEN_LIFETIME_DAYS=7      # 7 dias

# base.py (valores hardcoded, no leen el .env.example):
"ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
"REFRESH_TOKEN_LIFETIME": timedelta(days=1),
```

Las variables de `.env.example` `ACCESS_TOKEN_LIFETIME_MINUTES` y `REFRESH_TOKEN_LIFETIME_DAYS` NO son leidas en `base.py`. Los tiempos de vida del JWT estan hardcoded. Si un operador configura esas variables creyendo que aplican, no tendra efecto. Ademas, 30 minutos de access token es razonable, pero el refresh de 1 dia es muy corto para una app de uso diario. El `.env.example` sugeria 7 dias, lo que indica la intencion original.

**Remediacion:** Hacer los lifetimes configurables via env o documentar que las variables del `.env.example` no aplican.

---

#### VULN-008 [MEDIO] - Fotos de menores servidas por whitenoise sin autenticacion
**Archivo:** `backend/config/settings/base.py` lineas 181-190, `config/urls.py` linea 26

```python
# En DEBUG=True, los archivos /media/ se sirven directamente via urlpatterns
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# En produccion, whitenoise sirve /static/ pero no /media/
# Sin embargo, si MEDIA_ROOT esta en el mismo servidor, podria ser accesible
```

Las fotos de alumnos se guardan en `students/fotos/{archivo}`. Si la URL de media es predecible (ej: `/media/students/fotos/foto_juan.jpg`), cualquier persona con el link puede acceder sin autenticacion. Esto aplica a los QR codes de pagos tambien (`qr_payment_{dni}_{mes}_{anio}.png`), que exponen DNI del alumno en el nombre de archivo.

**Remediacion:**
- Usar nombres de archivo UUID, no basados en DNI: `qr_payment_{uuid4()}.png`
- En produccion, servir media files a traves de Django con verificacion de autenticacion, o usar URLs firmadas (ej: S3 presigned URLs con Railway Volumes)

---

### A03 - Injection

#### VULN-009 [BAJO] - Filtros de fecha sin validacion de tipo en CashTransactionViewSet
**Archivo:** `backend/apps/cashflow/views.py` lineas 45-59

```python
fecha_desde = self.request.query_params.get("fecha_desde")
fecha_hasta = self.request.query_params.get("fecha_hasta")
if fecha_desde:
    queryset = queryset.filter(fecha__gte=fecha_desde)  # sin validar formato
if fecha_hasta:
    queryset = queryset.filter(fecha__lte=fecha_hasta)  # sin validar formato
```

Django ORM protege contra SQL injection, pero un valor malformado (`fecha_desde=not-a-date`) generara una excepcion no controlada que devuelve un 500. Aunque no es explotable como injection gracias al ORM, expone stack traces si `DEBUG=True` queda activo accidentalmente.

**Remediacion:** Validar formato de fecha antes de filtrar:
```python
from datetime import datetime
try:
    if fecha_desde:
        datetime.strptime(fecha_desde, "%Y-%m-%d")
        queryset = queryset.filter(fecha__gte=fecha_desde)
except ValueError:
    return Response({"error": "Formato de fecha invalido. Use YYYY-MM-DD."}, status=400)
```

**Nota positiva:** El uso del Django ORM en todo el proyecto previene SQL injection clasico. No se encontraron queries raw no sanitizadas.

---

### A04 - Insecure Design

#### VULN-010 [CRITICO] - cleanup_graduated sin confirmacion ni soft-delete: operacion irreversible
**Archivo:** `backend/apps/migrations_academic/services.py` lineas 173-203
**CVSS:** 9.1 (integridad de datos criticos)

```python
def cleanup_graduated(years_to_keep=2):
    # ...
    for student in old_graduated:
        student.nombres = "ANONIMIZADO"
        student.apellidos = "ANONIMIZADO"
        student.dni = f"XXXX{student.id:04d}"
        student.foto = None
        student.save(...)
        student.apoderados.all().delete()   # ELIMINACION FISICA PERMANENTE
        if hasattr(student, "ficha_medica"):
            student.ficha_medica.delete()   # ELIMINACION FISICA PERMANENTE
```

**Problemas identificados:**

1. **Sin auditoria previa:** No hay registro de cuantos registros seran afectados antes de ejecutar.
2. **Eliminacion fisica irreversible:** `apoderados.all().delete()` y `ficha_medica.delete()` son DELETE SQL permanentes. No hay soft-delete ni backup point.
3. **El endpoint acepta `years_to_keep` desde el request body:** Un atacante con rol SUPERADMIN podria enviar `years_to_keep=0` y anonimizar TODOS los alumnos egresados inmediatamente.
4. **Sin doble confirmacion:** La operacion destructiva masiva no requiere token de confirmacion, 2FA adicional, ni confirmacion explicita.

```python
# views.py linea 69:
years_to_keep = request.data.get("years_to_keep", 2)
count = cleanup_graduated(int(years_to_keep))   # sin validacion de minimo
```

**Remediacion:**
```python
# Validar minimo de anios
years_to_keep = int(request.data.get("years_to_keep", 2))
if years_to_keep < 1:
    return Response({"error": "years_to_keep debe ser al menos 1."}, status=400)

# Requerir campo de confirmacion explicito
if not request.data.get("confirmar") == "CONFIRMO_ANONIMIZACION":
    return Response({
        "error": "Debe incluir el campo confirmar='CONFIRMO_ANONIMIZACION'."
    }, status=400)

# Implementar soft-delete en lugar de .delete()
# student.apoderados.update(activo=False)  # en lugar de .delete()
```

---

#### VULN-011 [MEDIO] - execute_migration sin verificacion de idempotencia
**Archivo:** `backend/apps/migrations_academic/services.py` lineas 94-170

La funcion `execute_migration` no verifica si ya existe una migracion para `anio_origen` antes de ejecutar. Si se llama dos veces, los alumnos promovidos en la primera ejecucion se promoverian nuevamente (de nivel 3 a 4, luego a 5 en llamadas sucesivas), o los ya egresados quedarian con `classroom=None` sin aula valida y se intentaria acceder a `student.classroom.nivel_edad` generando `AttributeError`.

**Remediacion:**
```python
if AcademicMigration.objects.filter(
    anio_origen=anio_origen,
    status=AcademicMigration.Status.EJECUTADO
).exists():
    raise ValueError(f"Ya existe una migracion ejecutada para el anio {anio_origen}.")
```

---

### A05 - Security Misconfiguration

#### VULN-012 [ALTO] - docker-compose expone credenciales default y ALLOWED_HOSTS=*
**Archivo:** `docker-compose.yml` lineas 6-8, 38, 45
**CVSS:** 7.8

```yaml
environment:
  POSTGRES_PASSWORD: postgres     # credencial trivial
  SECRET_KEY: dev-secret-key-change-in-production   # secreto en plaintext
  ALLOWED_HOSTS: "*"              # acepta cualquier host header
  DB_PASSWORD: postgres           # credencial trivial
```

**Riesgo:** Si este docker-compose se usa en staging/produccion (error comun), el sistema opera con credenciales conocidas. `ALLOWED_HOSTS=*` permite ataques de HTTP Host Header Injection.

**Remediacion:** Usar un archivo `.env` separado (gitignored) para docker-compose y nunca comitear credenciales:
```yaml
environment:
  - SECRET_KEY=${SECRET_KEY}
  - DB_PASSWORD=${DB_PASSWORD}
```

---

#### VULN-013 [MEDIO] - Admin panel accesible desde schema publico y tenant
**Archivo:** `config/urls_public.py` linea 13, `config/urls.py` linea 9

```python
# urls_public.py:
path("corem-panel-x9k2/", admin.site.urls),  # disponible en schema publico

# urls.py (tenant):
path("corem-panel-x9k2/", admin.site.urls),  # disponible en cada tenant
```

El panel admin esta disponible en DOS rutas distintas (publica y por tenant). Aunque la URL customizada es una medida de seguridad por oscuridad (buena practica), tener dos puntos de entrada duplica la superficie de ataque. Ademas, no hay restriccion de IP para acceder al admin.

**Remediacion:** Considerar restringir el admin solo al schema publico, o agregar restriccion de IP via middleware o configuracion de Railway.

---

#### VULN-014 [BAJO] - Dockerfile ejecuta collectstatic sin manejar el error correctamente
**Archivo:** `backend/Dockerfile` linea 27

```dockerfile
RUN python manage.py collectstatic --noinput || true
```

El `|| true` silencia cualquier error en collectstatic, incluyendo errores de configuracion criticos (SECRET_KEY faltante, DB no disponible). Un build roto puede desplegarse silenciosamente.

**Remediacion:** Manejar el error explicitamente o documentar por que se acepta el fallo.

---

### A06 - Vulnerable Components

#### Analisis de requirements/base.txt

| Dependencia | Version Especificada | Estado (Abr 2026) | Riesgo |
|-------------|---------------------|-------------------|--------|
| Django | >=5.1,<5.2 | Django 5.2 lanzado. Rama 5.1 en mantenimiento de seguridad | MEDIO |
| djangorestframework | >=3.15,<4.0 | DRF 3.15.x activo | OK |
| djangorestframework-simplejwt | >=5.3,<6.0 | 5.3.x activo | OK |
| django-axes | >=7.0,<8.0 | 7.x activo | OK |
| django-tenants | >=3.7,<4.0 | Verificar CVEs en schema isolation | REVISAR |
| Pillow | >=11.0,<12.0 | Verificar CVEs de procesamiento de imagenes | REVISAR |
| weasyprint | >=63.0,<64.0 | WeasyPrint tiene historial de SSRF via CSS | ALTO |
| psycopg2-binary | >=2.9,<3.0 | binary variant no recomendado en produccion | BAJO |
| qrcode | >=8.0,<9.0 | Sin CVEs conocidos relevantes | OK |

**VULN-015 [ALTO] - WeasyPrint: riesgo de SSRF via CSS/HTML**

WeasyPrint renderiza HTML a PDF y puede seguir URLs externas si el HTML contiene `@import url(...)`, `background-image: url(...)`, o `<img src="...">`. Si el contenido HTML que se pasa a WeasyPrint incluye datos controlados por el usuario (ej: nombres de alumnos en reportes), un atacante podria inyectar CSS malicioso para provocar SSRF hacia la red interna de Railway.

**Remediacion:**
- Sanitizar todo HTML antes de pasarlo a WeasyPrint
- Configurar WeasyPrint para deshabilitar carga de recursos externos
- Revisar `backend/apps/reports/` por uso de WeasyPrint con datos de usuario

**VULN-016 [BAJO] - psycopg2-binary no recomendado en produccion**

`psycopg2-binary` incluye OpenSSL y libpq compilados estaticamente. En produccion, se recomienda `psycopg2` compilado contra las librerias del sistema para recibir parches de seguridad del OS. Con el binary, las vulnerabilidades de OpenSSL no se parchean con `apt-get upgrade`.

---

### A07 - Authentication and Session Failures

#### VULN-017 [BAJO] - JWT config no lee variables de entorno definidas en .env.example
**Ya documentado en VULN-007.** Adicionalmente:

La configuracion JWT en `base.py` no incluye `ALGORITHM` explicitamente (usa el default HS256, que es correcto) ni `SIGNING_KEY` separada del `SECRET_KEY`. Si el `SECRET_KEY` se rota, todos los tokens existentes se invalidan automaticamente, lo cual puede ser deseable o no dependiendo del caso de uso.

**Positivo:** La configuracion incluye correctamente:
- `ROTATE_REFRESH_TOKENS: True` - Previene reutilizacion de refresh tokens
- `BLACKLIST_AFTER_ROTATION: True` - Invalida tokens antiguos
- `rest_framework_simplejwt.token_blacklist` en TENANT_APPS

**Recomendacion:** Documentar el comportamiento esperado ante rotacion de SECRET_KEY.

---

#### VULN-018 [MEDIO] - Ausencia de invalidacion de tokens activos al cambiar password
**Archivo:** `backend/apps/users/serializers.py` lineas 66-69

```python
def save(self, **kwargs):
    user = self.context["request"].user
    user.set_password(self.validated_data["new_password"])
    user.save()
    return user
    # NO invalida tokens JWT activos del usuario
```

Cuando un usuario cambia su contrasena, los tokens JWT previamente emitidos siguen siendo validos hasta su expiracion (30 minutos). Si un atacante robó un token, el usuario no puede invalidarlo cambiando su contrasena.

**Remediacion:**
```python
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

def save(self, **kwargs):
    user = self.context["request"].user
    user.set_password(self.validated_data["new_password"])
    user.save()
    # Invalidar todos los tokens activos del usuario
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)
    return user
```

---

### A08 - Software and Data Integrity

#### VULN-019 [BAJO] - Sin validacion de integridad en archivos de imagen subidos
**Archivos:** `students/models.py` linea 22, `tenants/models.py` linea 20

```python
foto = models.ImageField(upload_to="students/fotos/", null=True, blank=True)
logo = models.ImageField(upload_to="tenants/logos/", null=True, blank=True)
```

Django valida que el archivo sea una imagen valida (via Pillow), pero no:
- Limita el tamanio maximo del archivo
- Valida el tipo MIME explicitamente (solo extension)
- Verifica que la imagen no contiene metadatos EXIF con ubicacion GPS (fotos de menores)

**Remediacion:**
```python
# Agregar validador de tamanio
from django.core.exceptions import ValidationError

def validate_image_size(image):
    if image.size > 5 * 1024 * 1024:  # 5 MB
        raise ValidationError("La imagen no puede superar 5 MB.")

foto = models.ImageField(
    upload_to="students/fotos/",
    validators=[validate_image_size],
    null=True, blank=True
)
```

Para EXIF, usar Pillow para strip metadata al guardar.

---

### A09 - Security Logging and Monitoring Failures

**Estado:** POSITIVO con observaciones.

El sistema cuenta con:
- `django-auditlog` con `AUDITLOG_INCLUDE_ALL_MODELS = True`: todos los modelos se auditan
- `django-axes` con `AXES_FAILURE_LIMIT = 5` y `AXES_COOLOFF_TIME = 15 minutos`
- `AuditlogMiddleware` en MIDDLEWARE
- `AxesMiddleware` en MIDDLEWARE

**Observaciones:**

1. **VULN-020 [MEDIO] - Errores en envio de email exponen direcciones en response**
   **Archivo:** `backend/apps/communications/views.py` lineas 82-83

   ```python
   except Exception as e:
       errores.append({"email": email, "error": str(e)})
   # ...
   return Response({..., "errores": errores})
   ```

   El response incluye las direcciones de email de los apoderados donde fallo el envio. Esto expone PII (emails de apoderados) en la respuesta de la API, que podria loggearse en proxies, herramientas de monitoring, o ser capturada por el cliente.

   **Remediacion:** Loggear los errores internamente y devolver solo el conteo, no las direcciones.

2. **Sin configuracion de Sentry en prod.py:** El `.env.example` menciona `SENTRY_DSN` pero `prod.py` no lo configura. Sin monitoring de errores en produccion, las excepciones criticas pueden pasar desapercibidas.

---

### A10 - Server Side Request Forgery

#### VULN-021 [ALTO] - WeasyPrint con contenido HTML potencialmente controlado por usuario
**Ya documentado en VULN-015.** Ver seccion de Vulnerable Components.

---

## PARTE 2 - STRIDE THREAT MODELING

### Componente 1: Flujo de Autenticacion (JWT Tokens)
**Data Flow:** Cliente React -> POST /api/v1/auth/token/ -> SimpleJWT -> PostgreSQL (blacklist)

| Amenaza | Categoria | Prob. | Impacto | Riesgo | Mitigacion |
|---------|-----------|-------|---------|--------|-----------|
| Suplantacion de identidad via brute force | Spoofing | Baja | Critico | Alto | django-axes configurado (5 intentos, 15 min) - OK |
| Token JWT robado por XSS en frontend | Spoofing | Media | Critico | Critico | Mitigar XSS en React, considerar httpOnly cookie para tokens |
| JWT algorithm confusion ("none" alg) | Tampering | Baja | Critico | Alto | SimpleJWT rechaza "none" por defecto - OK |
| Token activo post-cambio de contrasena | Spoofing | Media | Alto | Alto | **VULN-018** - Sin mitigacion actual |
| Secret key comprometida forja tokens | Tampering | Media | Critico | Critico | **VULN-006** - Fallback hardcoded |
| Enumeracion de usuarios via timing | Info Disclosure | Alta | Medio | Alto | Verificar que login devuelve mismo tiempo para email valido/invalido |
| Repudio de operaciones criticas | Repudiation | Media | Alto | Alto | AuditLog registra cambios de modelo, pero no requests fallidos |
| Flood de tokens refresh agota blacklist DB | Denial of Service | Media | Alto | Alto | Rate limiting configurado (100/min) - parcialmente mitigado |

### Componente 2: Aislamiento Multi-Tenant (Schema Isolation)
**Data Flow:** HTTP Request -> TenantMainMiddleware -> Schema routing -> PostgreSQL schema

| Amenaza | Categoria | Prob. | Impacto | Riesgo | Mitigacion |
|---------|-----------|-------|---------|--------|-----------|
| Cross-tenant data access via raw SQL | Tampering | Baja | Critico | Alto | Django ORM + django-tenants previene esto por schema routing |
| Tenant spoofing via Host header manipulation | Spoofing | Media | Critico | Critico | ALLOWED_HOSTS en prod limita esto; verificar que Railway enforce el header |
| Schema enumeration via error messages | Info Disclosure | Media | Medio | Medio | Verificar que errores de tenant no exponen nombre de schema |
| SUPERADMIN accede a datos de todos los tenants | Elev. Privilege | Baja | Critico | Alto | Por diseno, SUPERADMIN opera en schema publico; validar que no puede acceder a schemas de tenant directamente |
| Creacion de tenant malicioso (schema injection) | Tampering | Baja | Critico | Alto | django-tenants sanitiza schema_name; verificar validacion en Tenant.schema_name |

**Observacion critica sobre tenant isolation:** La arquitectura de django-tenants con PostgreSQL schemas es robusta. Sin embargo, la tabla de `User` existe tanto en el schema publico (SHARED_APPS) como en cada tenant (TENANT_APPS). Esto puede generar confusion sobre donde se autentican los usuarios y si un SUPERADMIN del schema publico puede hacer queries en schemas de tenant.

---

### Componente 3: Datos Sensibles de Menores (GDPR/Ley 29733)
**Data Flow:** Formulario -> API -> PostgreSQL (schema tenant) + FileSystem (fotos/QR)

| Amenaza | Categoria | Prob. | Impacto | Riesgo | Mitigacion |
|---------|-----------|-------|---------|--------|-----------|
| Acceso no autorizado a ficha medica | Info Disclosure | Alta | Critico | **Critico** | **VULN-001** - Sin restriccion de rol actual |
| Descarga masiva de DNIs via reporte Excel | Info Disclosure | Media | Critico | **Critico** | **VULN-004** - Sin restriccion en ReportViewSet |
| Foto de menor accesible sin autenticacion | Info Disclosure | Media | Alto | **Alto** | **VULN-008** - Media files sin auth |
| QR con DNI en nombre de archivo predecible | Info Disclosure | Alta | Alto | **Alto** | `qr_payment_{dni}_{mes}_{anio}.png` - nombre expone DNI |
| Datos PII en logs de error (email apoderados) | Info Disclosure | Alta | Medio | Alto | **VULN-020** |
| Retención indefinida de datos post-egreso | Info Disclosure | Alta | Alto | Alto | cleanup_graduated existe, pero es manual y destructivo |
| Metadatos EXIF en fotos con ubicacion GPS | Info Disclosure | Media | Medio | Medio | **VULN-019** - Sin strip de EXIF |

**Consideraciones Ley 29733 (Peru) y principios GDPR:**
- El sistema maneja datos de menores de edad, categoria especialmente protegida.
- Se requiere consentimiento explicito de los apoderados para tratamiento de datos.
- Se debe implementar el derecho de acceso, rectificacion y supresion (ya existe `cleanup_graduated`).
- Los datos de salud (ficha medica) son datos sensibles con proteccion reforzada.
- **RECOMENDACION:** Documentar en la aplicacion la politica de privacidad y la base legal del tratamiento.

---

### Componente 4: Operaciones Financieras (Payments, Cashflow)
**Data Flow:** Usuario -> PaymentViewSet -> Payment model -> CashTransaction (trigger interno)

| Amenaza | Categoria | Prob. | Impacto | Riesgo | Mitigacion |
|---------|-----------|-------|---------|--------|-----------|
| Cualquier usuario autenticado crea transacciones | Elev. Privilege | Media | Alto | **Alto** | **VULN-005** - CashTransactionViewSet permiso insuficiente |
| Modificacion retroactiva de pagos registrados | Tampering | Media | Alto | Alto | PaymentViewSet permite PATCH sin restriccion de estado |
| registrar_pago sin idempotencia (doble cobro) | Tampering | Media | Alto | Alto | No hay verificacion de estado previo antes de registrar |
| QR de pago con monto manipulado | Tampering | Baja | Alto | Medio | QR es imagen local, el monto viene del modelo |
| Acceso a reporte cashflow por usuarios no autorizados | Info Disclosure | Alta | Alto | **Alto** | **VULN-004** - ReportViewSet sin restriccion |
| Cierre de mes no autorizado | Tampering | Baja | Alto | Medio | `cerrar_mes` requiere IsAdminJardinOrAbove - OK |

---

### Componente 5: Migracion Academica (Operaciones Destructivas)
**Data Flow:** SUPERADMIN -> execute_migration / cleanup_graduated -> bulk UPDATE/DELETE

| Amenaza | Categoria | Prob. | Impacto | Riesgo | Mitigacion |
|---------|-----------|-------|---------|--------|-----------|
| Migracion doble (ejecucion idempotente) | Tampering | Media | Critico | Critico | **VULN-011** - Sin verificacion |
| cleanup_graduated con years_to_keep=0 | Tampering | Baja | Critico | Alto | **VULN-010** - Sin validacion de minimo |
| Perdida de datos por cleanup sin backup | Data Loss | Media | Critico | Critico | **VULN-010** - Eliminacion fisica sin soft-delete |
| Repudio de ejecucion de migracion | Repudiation | Baja | Alto | Medio | AcademicMigration registra ejecutado_por - OK |
| anio_origen manipulado (injection de entero) | Tampering | Baja | Alto | Medio | Se hace `int(anio_origen)`, ValueError capturado - OK |

---

## PARTE 3 - ANALISIS DE DEPENDENCIAS

### Dependencias con Riesgo Identificado (analisis manual)

| Dependencia | Version | Vulnerabilidad Potencial | Accion |
|-------------|---------|--------------------------|--------|
| weasyprint | >=63.0,<64.0 | SSRF via CSS url() en HTML renderizado | Auditar uso, sanitizar input HTML |
| Pillow | >=11.0,<12.0 | Historial de buffer overflow en parsing de imagenes | Validar tamanio y tipo antes de procesar |
| psycopg2-binary | >=2.9,<3.0 | OpenSSL estatico no se actualiza con el OS | Considerar psycopg2 (no binary) o psycopg3 |
| django-tenants | >=3.7,<4.0 | Verificar CVE database; schema isolation critica | Monitorear CVEs activamente |
| Django | >=5.1,<5.2 | Django 5.2 disponible con mejoras de seguridad | Plan de actualizacion a 5.2 |

### Dependencias sin Vulnerabilidades Conocidas Relevantes
- djangorestframework 3.15.x - OK
- djangorestframework-simplejwt 5.3.x - OK
- django-axes 7.x - OK
- django-auditlog 3.x - OK
- django-cors-headers 4.4.x - OK
- django-otp 1.5.x - OK
- celery 5.4.x - OK
- redis 5.x - OK

### Recomendacion de Proceso
```
1. Implementar OWASP Dependency Check en CI/CD:
   pip install safety
   safety check -r requirements/base.txt

2. Configurar Snyk o Dependabot en el repositorio GitHub para alertas automaticas

3. Pin de versiones exactas en prod.txt (no rangos):
   # En lugar de: Django>=5.1,<5.2
   # Usar: Django==5.1.x  (version exacta validada)
```

---

## PARTE 4 - CONFIGURACION DE SEGURIDAD

### Evaluacion de Security Headers (prod.py)

| Header | Estado | Valor |
|--------|--------|-------|
| SECURE_CONTENT_TYPE_NOSNIFF | OK | True |
| SECURE_SSL_REDIRECT | OK | True |
| SESSION_COOKIE_SECURE | OK | True |
| CSRF_COOKIE_SECURE | OK | True |
| X_FRAME_OPTIONS | OK | DENY |
| SECURE_HSTS_SECONDS | OK | 31536000 (1 año) |
| SECURE_HSTS_INCLUDE_SUBDOMAINS | OK | True |
| SECURE_HSTS_PRELOAD | OK | True |
| Content-Security-Policy | FALTANTE | No configurado |
| Permissions-Policy | FALTANTE | No configurado |
| Referrer-Policy | FALTANTE | No configurado |

**VULN-022 [MEDIO] - Content-Security-Policy no configurado**

Sin CSP, el frontend React es mas vulnerable a XSS. Aunque el backend es una API (JSON), las vistas del admin Django pueden ser atacadas via XSS stored en campos de texto.

**Remediacion:**
```python
# prod.py
SECURE_BROWSER_XSS_FILTER = True
# Para el admin Django, agregar CSP via django-csp:
# pip install django-csp
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")  # unfold requiere inline styles
```

---

### Evaluacion de Configuracion CORS

```python
# prod.py
CORS_ALLOWED_ORIGINS = [o for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if o]
CORS_ALLOW_CREDENTIALS = True
```

**Estado:** Correcto. En produccion se leen origenes desde variable de entorno. Si `CORS_ALLOWED_ORIGINS` esta vacia, no se permite ningun origen (behavior seguro).

**Atencion:** `CORS_ALLOW_CREDENTIALS = True` combinado con origenes dinamicos requiere que NUNCA se configure `CORS_ALLOW_ALL_ORIGINS = True`. Verificar que esto no ocurra en ninguna configuracion.

---

## PARTE 5 - REPORTE DE VULNERABILIDADES CONSOLIDADO

### Vulnerabilidades Criticas (Bloquean Release)

| ID | Tipo OWASP | CVSS | Descripcion | Archivo | Remediacion |
|----|-----------|------|-------------|---------|-------------|
| VULN-001 | A01 - Broken Access Control | 9.1 | IDOR: Todo usuario lee/modifica PII de menores (fichas medicas, apoderados) | students/views.py | Aplicar IsDirectorOrAbove en MedicalRecord, IsAdminJardinOrAbove en mutaciones |
| VULN-006 | A02 - Crypto Failure | 9.8 | SECRET_KEY con fallback hardcoded en repositorio | settings/base.py | Raise ValueError si env var ausente |
| VULN-010 | A04 - Insecure Design | 9.1 | cleanup_graduated: eliminacion fisica sin confirmacion, acepta years=0 | migrations_academic/services.py | Soft-delete, validar minimo, token de confirmacion |
| VULN-002 | A01 - Broken Access Control | 9.1 | IDOR: GuardianViewSet sin verificacion de tenant ownership | students/views.py | Verificacion defensiva de pertenencia |

### Vulnerabilidades Altas (Remediar Antes de Deploy)

| ID | Tipo OWASP | CVSS | Descripcion | Archivo |
|----|-----------|------|-------------|---------|
| VULN-003 | A01 | 7.5 | Falta object-level permission en UserViewSet | users/views.py |
| VULN-004 | A01 | 7.5 | ReportViewSet expone PII masiva y datos financieros a cualquier rol | reports/views.py |
| VULN-005 | A01 | 7.2 | CashCategory/CashTransaction CRUD sin restriccion de rol | cashflow/views.py |
| VULN-012 | A05 | 7.8 | docker-compose con credenciales default y ALLOWED_HOSTS=* | docker-compose.yml |
| VULN-015 | A06/A10 | 7.5 | WeasyPrint: riesgo de SSRF con HTML controlado por usuario | reports/ (auditar) |
| VULN-018 | A07 | 7.5 | Cambio de contrasena no invalida tokens JWT activos | users/serializers.py |
| VULN-021 | A10 | 7.5 | SSRF via WeasyPrint (duplicado de VULN-015, mayor contexto) | reports/ |

### Vulnerabilidades Medias

| ID | Tipo OWASP | CVSS | Descripcion |
|----|-----------|------|-------------|
| VULN-007 | A02 | 5.3 | JWT lifetime variables en .env.example no son leidas por base.py |
| VULN-008 | A02 | 6.5 | Fotos de menores y QR con DNI servidos sin autenticacion |
| VULN-011 | A04 | 6.5 | execute_migration sin verificacion de idempotencia |
| VULN-013 | A05 | 5.0 | Admin panel accesible desde dos URLs (publica y tenant) |
| VULN-020 | A09 | 5.3 | Emails de apoderados expuestos en response de error de comunicaciones |
| VULN-022 | A05 | 5.3 | Content-Security-Policy no configurado |

### Vulnerabilidades Bajas

| ID | Tipo OWASP | CVSS | Descripcion |
|----|-----------|------|-------------|
| VULN-009 | A03 | 3.5 | Filtros de fecha sin validacion de formato (500 sin traza) |
| VULN-014 | A05 | 2.5 | Dockerfile silencia errores de collectstatic |
| VULN-016 | A06 | 3.1 | psycopg2-binary con OpenSSL estatico |
| VULN-019 | A08 | 3.8 | Sin validacion de tamanio de imagen ni strip de metadatos EXIF |

---

## PARTE 6 - CHECKLIST DE SEGURIDAD PRE-DEPLOY

### BLOQUEO DE RELEASE - Debe estar en verde antes del primer deploy a produccion

- [ ] **[VULN-006]** Verificar que `DJANGO_SECRET_KEY` esta configurada en Railway con un valor aleatorio de 50+ caracteres. Eliminar el fallback hardcoded de `base.py` o agregar el raise ValueError.
- [ ] **[VULN-001]** Aplicar restricciones de rol en `StudentViewSet`, `GuardianViewSet` y `MedicalRecordViewSet`. Minimo: mutaciones requieren `IsAdminJardinOrAbove`.
- [ ] **[VULN-010]** Agregar validacion `years_to_keep >= 1` y campo de confirmacion explicito en `cleanup_egresados`. Cambiar `apoderados.all().delete()` por soft-delete o al menos agregar transaccion con posibilidad de rollback documentada.
- [ ] **[VULN-004]** Restringir `morosidad-excel`, `cashflow-excel` y `alumnos-excel` a `IsAdminJardinOrAbove` como minimo.
- [ ] **[VULN-012]** Asegurar que el docker-compose de desarrollo NO se use en produccion. Crear `.env.prod.example` con instrucciones claras. Verificar que Railway usa las variables de entorno del panel, no el compose.

### Alta Prioridad - Resolver en el sprint de hardening

- [ ] **[VULN-018]** Invalidar tokens JWT al cambiar contrasena.
- [ ] **[VULN-005]** Restringir `CashCategoryViewSet` y `CashTransactionViewSet` mutaciones a `IsAdminJardinOrAbove`.
- [ ] **[VULN-008]** Cambiar nombres de archivo QR para no incluir DNI (`uuid4()` en lugar de `{dni}`). Evaluar serving autenticado de media files.
- [ ] **[VULN-015]** Auditar todos los usos de WeasyPrint. Si el HTML incluye datos de usuario, sanitizar antes del render.
- [ ] **[VULN-011]** Agregar verificacion de idempotencia en `execute_migration`.
- [ ] **[VULN-020]** No devolver emails de apoderados en responses de error. Loggear internamente.

### Configuracion de Produccion - Railway/Vercel

- [ ] Verificar que `DEBUG=False` en produccion (prod.py ya lo fuerza, pero confirmar).
- [ ] Confirmar que `ALLOWED_HOSTS` solo contiene el dominio de Railway, no `*`.
- [ ] Confirmar que `CORS_ALLOWED_ORIGINS` solo contiene el dominio de Vercel.
- [ ] Configurar `SENTRY_DSN` en Railway para monitoring de errores en produccion.
- [ ] Verificar que Redis esta autenticado (password) en Railway, no abierto.
- [ ] Confirmar que el volumen de PostgreSQL en Railway tiene backups automaticos habilitados.
- [ ] Revisar que los media files (fotos de alumnos) no estan en el filesystem del contenedor Railway (ephemeral); configurar almacenamiento persistente o S3-compatible.

### Controles de Datos de Menores (Ley 29733 / principios GDPR)

- [ ] Implementar y publicar Politica de Privacidad accesible desde la aplicacion.
- [ ] Documentar la base legal para el tratamiento de datos de menores (consentimiento de apoderados).
- [ ] Verificar que `cleanup_graduated` se ejecuta periodicamente (tarea Celery schedulada) y no solo manualmente.
- [ ] Agregar validacion que impida subir imagenes con metadatos EXIF de GPS (strip automatico via Pillow al guardar).
- [ ] Considerar cifrado de columnas sensibles en base de datos (tipo_sangre, alergias, contacto_emergencia) usando django-pgcrypto o similar.

### Testing de Seguridad Recomendado

- [ ] Ejecutar `safety check -r requirements/base.txt` en CI/CD.
- [ ] Ejecutar OWASP ZAP baseline scan contra staging antes de cada release.
- [ ] Ejecutar pruebas de IDOR manuales: intentar acceder a recursos de un tenant desde otro tenant con token valido.
- [ ] Verificar que las pruebas de rate limiting funcionan (Axes bloquea correctamente).
- [ ] Ejecutar pruebas de JWT algorithm confusion ("none" alg, RS256 cuando se espera HS256).

---

## PARTE 7 - CONTROLES DE SEGURIDAD POSITIVOS IDENTIFICADOS

El sistema ya implementa correctamente los siguientes controles, que deben mantenerse:

| Control | Implementacion | Evaluacion |
|---------|---------------|------------|
| Brute force protection | django-axes, 5 intentos, 15 min lockout | Excelente |
| JWT blacklist | rest_framework_simplejwt.token_blacklist, ROTATE+BLACKLIST | Excelente |
| Audit trail completo | django-auditlog en todos los modelos | Excelente |
| Password validation | 10 chars minimo, similarity, common, numeric | Bueno |
| HSTS configurado | 1 año, incluye subdomains, preload | Excelente |
| SSL redirect | SECURE_SSL_REDIRECT=True | Excelente |
| Admin URL ofuscada | `/corem-panel-x9k2/` en lugar de `/admin/` | Bueno |
| CORS restrictivo | Solo origenes de env var, no wildcard | Excelente |
| Rate limiting DRF | 20/min anon, 100/min usuario | Bueno |
| Multi-tenant schema isolation | PostgreSQL schemas via django-tenants | Excelente |
| OTP preparado | django-otp instalado y en middleware | Bueno (pendiente activar) |
| Password no en serializer response | write_only=True en todos los campos password | Excelente |
| Escalacion de privilegios bloqueada | validate_role en UserCreateSerializer | Bueno |

---

## NOTAS PARA EL QA LEAD

### Riesgos Residuales que Requieren Atencion Especial

1. **El riesgo mayor del sistema es la combinacion VULN-001 + VULN-004:** Un PROFESOR con credenciales comprometidas (o simplemente curiosidad) puede descargar el listado completo de DNIs, fichas medicas y datos financieros del jardin. Con datos de menores de edad, esto es una exposicion de alto impacto legal y reputacional.

2. **VULN-010 es una bomba de tiempo operacional:** No es necesario un atacante externo. Un SUPERADMIN legitimo que cometa un error (o un atacante que comprometa esa cuenta) puede ejecutar `cleanup_graduated(years_to_keep=0)` y destruir permanentemente los datos personales de todos los alumnos egresados. La operacion es irreversible sin backup.

3. **El modelo multi-tenant es solido a nivel de arquitectura**, pero requiere un pentest especifico de cross-tenant access antes del lanzamiento con multiples jardines. Las pruebas manuales deben incluir: obtener un token de Tenant A e intentar acceder a endpoints de Tenant B manipulando el Host header.

4. **Media files en Railway:** El contenedor de Railway es efimero. Si los archivos de imagen (fotos de alumnos, QR) se guardan en el filesystem local del contenedor, se perderan en cada redeploy. Verificar la configuracion de volumenes persistentes o migrar a almacenamiento externo (AWS S3, Cloudflare R2) antes de ir a produccion.

5. **OTP (2FA) esta instalado pero no activado:** `django-otp` esta en INSTALLED_APPS y `OTPMiddleware` en MIDDLEWARE, pero no se encontro en el flujo de login que se requiera el segundo factor. Para cuentas SUPERADMIN y ADMIN_JARDIN que manejan datos de menores, activar 2FA obligatorio es una medida de seguridad prioritaria.

### Pendiente de Analisis Manual (no incluido en este reporte)

- `backend/apps/reports/views.py`: Verificar si WeasyPrint se usa para PDF y con que datos.
- `backend/apps/communications/models.py`: Verificar si el campo `contenido` sanitiza HTML antes de enviar por email.
- Configuracion de Celery: verificar que las tareas scheduladas no ejecutan operaciones privilegiadas sin autenticacion.
- Frontend React: analisis de XSS, almacenamiento de tokens (localStorage vs httpOnly cookie), y validacion de inputs del lado cliente.

---

*Reporte generado por Security Tester Sub-Agent - SAAS COREM v1.0*
*Framework: OWASP Top 10 2021 + STRIDE + NIST CSF*
*Fecha: 2026-04-08*
