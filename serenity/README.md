# SAAS COREM - Serenity BDD E2E Test Suite

Suite de pruebas End-to-End con Serenity BDD y Screenplay Pattern para el sistema de gestion de jardines de infantes SAAS COREM.

## Arquitectura

```
Patron: Screenplay (Actor -> Task -> Question -> Ability)
Framework: Serenity BDD 4.x + Cucumber 7.x + JUnit 5
Browser: Chrome (via WebDriverManager - auto-descarga chromedriver)
API: Rest-Assured (setup de datos de prueba)
```

## Requisitos previos

| Herramienta | Version minima | Verificar con |
|-------------|---------------|---------------|
| Java JDK    | 17            | `java -version` |
| Maven       | 3.8+          | `mvn -version` |
| Chrome      | 90+           | Cualquier version reciente |
| Backend     | Django 5.1    | `http://localhost:8000` |
| Frontend    | React + Vite  | `http://localhost:3000` |

## Configuracion inicial

### 1. Credenciales de prueba (crear en Django)

```bash
cd D:\PROYECTOS\COREM\SAAS_COREM\backend

# Activar entorno virtual
.venv\Scripts\activate

# Crear usuario de prueba con Host header del tenant
python manage.py shell
```

```python
from django_tenants.utils import schema_context
with schema_context('test'):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    u = User.objects.create_user(
        email='admin@test.com',
        password='TestPass1234',
        nombre='Admin',
        apellido='Test',
        rol='ADMIN_JARDIN'
    )
    u.save()
    print("Usuario creado:", u.email)
```

### 2. Multi-tenant (Host header)

SAAS COREM usa django-tenants. Cada peticion de API necesita el header `Host: test.localhost` para que Django-tenants enrute al schema `test` correctamente.

El `CoremApiClient` ya configura este header automaticamente:
```java
.header("Host", tenantHost)  // "test.localhost"
```

Para el frontend React en `localhost:3000`, el tenant se detecta por el subdominio. Configura el archivo `hosts` de Windows si es necesario:

```
# C:\Windows\System32\drivers\etc\hosts (ejecutar como Administrador)
127.0.0.1   test.localhost
```

### 3. serenity.conf

El archivo `src/test/resources/serenity.conf` contiene la configuracion por ambiente:

```hocon
environments {
  local {
    webdriver.base.url = "http://localhost:3000"
    api.base.url = "http://localhost:8000"
    test.email = "admin@test.com"
    test.password = "TestPass1234"
  }
}
```

Para cambiar credenciales, editar directamente el archivo o pasar por sistema de propiedades.

## Ejecucion

### Suite completa (24 escenarios)

```bash
cd D:\PROYECTOS\COREM\SAAS_COREM\serenity

mvn verify
```

### Smoke tests (9 escenarios - uno por modulo)

```bash
mvn verify -Dcucumber.filter.tags="@tc-auth-01 or @tc-stu-01 or @tc-pay-01 or @tc-att-01 or @tc-cash-01 or @tc-dash-01 or @tc-comm-01 or @tc-rep-01 or @tc-nav-01"
```

### Por modulo

```bash
# Solo autenticacion
mvn verify -Dcucumber.filter.tags="@autenticacion"

# Solo alumnos
mvn verify -Dcucumber.filter.tags="@alumnos"

# Solo pensiones
mvn verify -Dcucumber.filter.tags="@pensiones"

# Solo navegacion
mvn verify -Dcucumber.filter.tags="@navegacion"
```

### Modo headless (CI)

```bash
mvn verify -Pci -Dheadless=true
```

### Por caso de prueba especifico

```bash
# Ejecutar solo TC-AUTH-01
mvn verify -Dcucumber.filter.tags="@tc-auth-01"

# Ejecutar solo TC-STU-02 (crear alumno)
mvn verify -Dcucumber.filter.tags="@tc-stu-02"
```

## Ver el reporte Serenity

Despues de ejecutar `mvn verify`, el reporte esta en:

```
target/site/serenity/index.html
```

Abrir en el browser:

```bash
# Windows
start target\site\serenity\index.html

# O con Maven
mvn serenity:aggregate
```

El reporte incluye:
- **Living Documentation**: los feature files como documentacion viva
- **Test Results**: resultados por escenario con screenshots de fallos
- **Requirements**: trazabilidad de requisitos a tests
- **Tendencias**: historico de ejecuciones (si se configura)

## Estructura del proyecto

```
serenity/
  src/test/
    java/com/corem/saas/
      abilities/          <- Abilities del Screenplay Pattern
        CallTheCoremApi   <- Llama a la API REST de COREM
      actors/             <- Factory de actores
        CoremActors       <- Crea actores con abilities configuradas
      helpers/            <- Utilidades
        CoremApiClient    <- Cliente HTTP para setup de datos via API
        TestDataStore     <- Datos compartidos entre steps del escenario
      interactions/       <- Interacciones especificas de Ant Design
        SelectFromAntdDropdown  <- Selecciona en dropdowns custom
        ConfirmPopconfirm       <- Confirma dialogs de Popconfirm
        WaitForSpinner          <- Espera que el spinner desaparezca
        TypeInAntdPicker        <- Escribe en DatePickers
      tasks/              <- Tasks del Screenplay Pattern
        Login             <- Flujo completo de login
        NavigateToModule  <- Navegar a un modulo via URL
        CreateStudent     <- Llena el formulario de alumno
        RegisterPayment   <- Registra un pago en el modal
        MarkAttendance    <- Marca estado de asistencia en tabla
        CreateTransaction <- Crea una transaccion de caja
        CreateCommunication <- Crea una comunicacion
      questions/          <- Questions del Screenplay Pattern
        TheToastMessage   <- Lee el texto del toast de Ant Design
        ThePageUrl        <- URL actual del browser
        TheTableRowCount  <- Cuenta filas de la tabla
        TheLocalStorageValue <- Lee localStorage
        TheElementText    <- Texto de un elemento
      ui/                 <- Targets (selectores)
        CoremTargets      <- Todos los locators del sistema
      runners/            <- Test runners de Cucumber
        CoremE2ETestRunner  <- Todos los tests
        CoremSmokeTestRunner <- Solo smoke tests
      stepdefinitions/    <- Glue code entre Gherkin y Screenplay
        ScenarioContext   <- Actor compartido por thread
        CucumberHooks     <- Before/After hooks globales
        AuthStepDefinitions
        StudentsStepDefinitions
        PaymentsStepDefinitions
        AttendanceStepDefinitions
        CashflowStepDefinitions
        DashboardStepDefinitions
        CommunicationsStepDefinitions
        ReportsStepDefinitions
        NavigationStepDefinitions
    resources/
      features/           <- Feature files en espanol
        auth/autenticacion.feature
        students/alumnos.feature
        payments/pensiones.feature
        attendance/asistencia.feature
        cashflow/flujo-de-caja.feature
        dashboard/dashboard.feature
        communications/comunicaciones.feature
        reports/reportes.feature
        navigation/navegacion.feature
      serenity.conf       <- Configuracion de Serenity
      logback-test.xml    <- Logging
      cucumber.properties <- Propiedades de Cucumber
```

## Cobertura de tests

| ID        | Modulo         | Descripcion                                   |
|-----------|----------------|-----------------------------------------------|
| TC-AUTH-01 | Auth          | Login exitoso redirige al dashboard           |
| TC-AUTH-02 | Auth          | Credenciales invalidas muestra error          |
| TC-AUTH-03 | Auth          | Validacion de campos vacios                   |
| TC-AUTH-04 | Auth          | Logout limpia sesion                          |
| TC-STU-01  | Alumnos       | Lista de alumnos con columnas correctas       |
| TC-STU-02  | Alumnos       | Crear alumno con datos validos                |
| TC-STU-03  | Alumnos       | Validacion de formulario vacio                |
| TC-STU-04  | Alumnos       | Editar alumno existente                       |
| TC-STU-05  | Alumnos       | Buscar por nombre filtra resultados           |
| TC-STU-06  | Alumnos       | Ver detalle navega a /alumnos/:id             |
| TC-PAY-01  | Pensiones     | Lista con columnas y filtros                  |
| TC-PAY-02  | Pensiones     | Filtrar por estado PAGADO                     |
| TC-PAY-03  | Pensiones     | Registrar pago cambia estado                  |
| TC-PAY-04  | Pensiones     | Generar QR abre modal                         |
| TC-ATT-01  | Asistencia    | Sin aula muestra mensaje de guia              |
| TC-ATT-02  | Asistencia    | Seleccionar aula carga alumnos                |
| TC-ATT-03  | Asistencia    | Guardar asistencia con estados mixtos         |
| TC-CASH-01 | Caja          | Cards de resumen muestran estadisticas        |
| TC-CASH-02 | Caja          | Crear transaccion INGRESO                     |
| TC-CASH-03 | Caja          | Validacion de formulario de transaccion       |
| TC-CASH-04 | Caja          | Tab de Cierres Mensuales                      |
| TC-DASH-01 | Dashboard     | Cuatro KPIs visibles con valores              |
| TC-DASH-02 | Dashboard     | Grafico de ingresos se renderiza              |
| TC-COMM-01 | Comunicaciones| Lista con columnas correctas                  |
| TC-COMM-02 | Comunicaciones| Crear comunicacion GENERAL                    |
| TC-COMM-03 | Comunicaciones| Selector aula condicional por tipo            |
| TC-COMM-04 | Comunicaciones| Enviar via Popconfirm                         |
| TC-REP-01  | Reportes      | Cuatro tarjetas de descarga visibles          |
| TC-REP-02  | Reportes      | Descargar Lista de Alumnos (.xlsx)            |
| TC-REP-03  | Reportes      | Estado loading durante descarga               |
| TC-NAV-01  | Navegacion    | Sidebar navega a cada modulo                  |
| TC-NAV-02  | Navegacion    | Item activo tiene clase selected              |
| TC-NAV-03  | Navegacion    | Colapsar/expandir sidebar                     |
| TC-NAV-04  | Navegacion    | Ruta privada sin sesion -> /login             |
| TC-NAV-05  | Navegacion    | /alumnos sin sesion -> /login                 |
| TC-NAV-06  | Navegacion    | Ruta desconocida sin sesion -> /login         |
| TC-NAV-07  | Navegacion    | Ruta desconocida con sesion -> /dashboard     |

**Total: 37 escenarios** (incluyendo variaciones de TC-COMM-03 y TC-NAV que tienen mas steps)

## Solucion de problemas

### ChromeDriver no encontrado
WebDriverManager descarga automaticamente el chromedriver compatible. Si falla la conexion a internet:
```bash
mvn verify -Dwdm.chromeDriverVersion=114.0.5735.90
```

### Tests que requieren datos previos
Los tests TC-ATT-02, TC-ATT-03, TC-PAY-03 y TC-COMM-04 necesitan datos previos en la BD.
Si no existen, los tests se omiten automaticamente con `assumeTrue()` (no fallan).

### Timeout en CI
En entornos lentos, aumentar los timeouts en serenity.conf:
```hocon
webdriver.timeouts.wait.for.element = 20000
webdriver.timeouts.page.load.timeout = 60000
```

### Error de tenant (404 o 403 en API)
Verificar que el schema `test` existe en PostgreSQL:
```sql
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'test';
```

## Paralelismo con la suite Playwright

Esta suite Serenity BDD coexiste con la suite Playwright en `../e2e/`.
Ambas cubren los mismos 24 escenarios de negocio con frameworks diferentes:

| Aspecto | Playwright (e2e/) | Serenity BDD (serenity/) |
|---------|-------------------|--------------------------|
| Lenguaje | TypeScript | Java 17 |
| Pattern | Page Object | Screenplay |
| Reporte | HTML Reporter | Living Documentation |
| BDD | No | Si (Gherkin en espanol) |
| Velocidad | Mas rapido | Mas documentacion |

Ejecutar ambas suites en CI es posible sin conflictos.
