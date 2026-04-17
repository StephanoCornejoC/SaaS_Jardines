# SAAS COREM - Suite de Tests E2E (Playwright)

Tests End-to-End para el frontend React 18 + Ant Design de SAAS COREM.

## Requisitos

- Node.js 18+
- Backend Django corriendo en `http://localhost:8000`
- Frontend React/Vite corriendo en `http://localhost:3000`

## Instalacion

```bash
cd e2e
npm install
npm run install:browsers
```

## Configuracion

Copiar `.env.example` a `.env` y ajustar las credenciales:

```bash
cp .env.example .env
```

Variables requeridas:

| Variable                 | Descripcion                                          | Default                   |
|--------------------------|------------------------------------------------------|---------------------------|
| `BASE_URL`               | URL del frontend React                               | `http://localhost:3000`   |
| `API_URL`                | URL del backend Django                               | `http://localhost:8000`   |
| `TEST_EMAIL`             | Email del usuario de prueba (ADMIN_JARDIN o superior) | `admin@garabato.test`    |
| `TEST_PASSWORD`          | Password del usuario de prueba                       | `admin123`                |

## Ejecucion

```bash
# Todos los tests (Chromium + Firefox + WebKit)
npm test

# Solo Chromium (mas rapido para desarrollo)
npm run test:chromium

# Modo UI interactivo (recomendado para desarrollo de tests)
npm run test:ui

# Modo headed (ver el browser)
npm run test:headed

# Ver reporte HTML tras la ejecucion
npm run report

# Debug de un test especifico
npx playwright test tests/students.spec.ts --debug
```

## Estructura

```
e2e/
├── playwright.config.ts      # Configuracion: 3 browsers + mobile + webServer
├── fixtures/
│   └── auth.ts               # Custom fixtures: todas las Page Objects + ApiHelper
├── pages/                    # Page Object Models (POM)
│   ├── LoginPage.ts
│   ├── DashboardPage.ts
│   ├── StudentsPage.ts
│   ├── StudentDetailPage.ts
│   ├── PaymentsPage.ts
│   ├── AttendancePage.ts
│   └── CashflowPage.ts
├── tests/
│   ├── auth.setup.ts         # Setup de autenticacion (corre primero, una sola vez)
│   ├── auth.spec.ts          # Login, logout, credenciales invalidas
│   ├── students.spec.ts      # CRUD alumnos, busqueda, detalle
│   ├── payments.spec.ts      # Lista, filtros, registrar pago, QR
│   ├── attendance.spec.ts    # Seleccion aula, marcar asistencia, guardar
│   ├── cashflow.spec.ts      # KPIs financieros, nueva transaccion, cierres
│   ├── dashboard.spec.ts     # KPIs, grafico Chart.js
│   ├── communications.spec.ts # Crear, tipo condicional, enviar via Popconfirm
│   ├── reports.spec.ts       # Descarga Excel, estado loading
│   └── navigation.spec.ts    # Sidebar, rutas protegidas, catch-all
└── playwright/
    └── .auth/
        └── user.json         # Storage state (gitignored)
```

## Arquitectura

### Autenticacion reutilizable

`auth.setup.ts` obtiene el JWT via API (no via UI) y guarda el `storageState`
en `playwright/.auth/user.json`. Todos los proyectos de browser cargan este estado,
evitando un login por test.

Los tests de `auth.spec.ts` que prueban el flujo de login usan
`test.use({ storageState: { cookies: [], origins: [] } })` para arrancar sin sesion.

### Patron Page Object Model (POM)

Cada modulo tiene su Page Object con:
- Locators como propiedades de la clase (usando selectores semanticos de Playwright)
- Metodos de accion (`goto`, `fillForm`, `submit`, etc.)
- Metodos de asercion propios (`expectSuccessMessage`, `expectValidationError`)
- Sin assertions de negocio directas (esas van en los specs)

### Selectores de Ant Design

Ant Design no usa selectores semanticos estandar en todos los componentes.
Estrategia usada:

| Componente       | Estrategia de seleccion                                          |
|------------------|------------------------------------------------------------------|
| Form Input       | `getByLabel()` (Ant Design vincula labels con htmlFor)           |
| Button           | `getByRole('button', { name: ... })`                            |
| Select           | `.ant-select` filtrado por placeholder o label cercano          |
| Table rows       | `.ant-table-tbody tr.ant-table-row`                              |
| Modal            | `.ant-modal` filtrado por `hasText` del titulo                   |
| Message (toast)  | `.ant-message-notice-content` con `hasText`                     |
| Tags             | `.ant-tag`                                                       |
| Statistic        | `.ant-statistic` con `hasText` del titulo                       |
| Tabs             | `.ant-tabs-tab` con `hasText`                                   |
| Popconfirm       | `.ant-popconfirm`                                               |

### ApiHelper para setup/teardown de datos

Los tests que requieren datos predecibles usan `ApiHelper` para crear/eliminar
registros via la API de Django en lugar de la UI:

```typescript
const token = await apiHelper.getAuthToken();
const student = await apiHelper.createStudent(token, { ... });
// ... ejecutar test ...
await apiHelper.deleteStudent(token, student.id);
```

Esto hace los tests independientes del orden de ejecucion y del estado previo de la BD.

## data-testid pendientes de agregar al frontend

Para mejorar la robustez de los selectores, agregar estos atributos al frontend React:

### Login.jsx
```jsx
// En el Input de email:
<Input data-testid="login-email-input" ... />

// En el Input.Password:
<Input.Password data-testid="login-password-input" ... />

// En el Button de submit:
<Button data-testid="login-submit-btn" ... />
```

### Students.jsx
```jsx
// En el Button "Nuevo Alumno":
<Button data-testid="btn-nuevo-alumno" ... />

// En el Input de busqueda:
<Input data-testid="input-buscar-alumno" ... />

// En el Table:
<Table data-testid="students-table" ... />

// En el Modal:
<Modal data-testid="modal-alumno" ... />
```

### Payments.jsx
```jsx
<Table data-testid="payments-table" ... />
```

### Attendance.jsx
```jsx
<Button data-testid="btn-guardar-asistencia" ... />
<Table data-testid="attendance-table" ... />
```

### Dashboard.jsx
```jsx
// En cada Card de KPI:
<Card data-testid="kpi-total-alumnos">
<Card data-testid="kpi-total-profesores">
<Card data-testid="kpi-ingresos-mes">
<Card data-testid="kpi-morosidad">
// En el Card del grafico:
<Card data-testid="chart-ingresos">
```

## Riesgos de Flakiness

| Riesgo                          | Mitigacion                                                  |
|---------------------------------|-------------------------------------------------------------|
| Ant Design Modal con animation  | Usar `await expect(modal).toBeHidden()` (espera activa)     |
| DatePicker locale               | Configurar `locale: 'es-PE'` en playwright.config.ts        |
| Select dropdown portal en body  | Usar `.ant-select-dropdown:not(.ant-select-dropdown-hidden)` |
| Chart.js canvas async           | Usar `waitForLoadState('networkidle')` antes del screenshot  |
| Tests de pago con PENDIENTE     | Usar `test.skip()` si no hay datos disponibles              |
| Descarga de Excel en CI         | Capturar evento `download` antes del click                  |

## CI/CD

Para GitHub Actions agregar `.env` como secrets y usar:

```yaml
- name: Run E2E Tests
  run: |
    cd e2e
    npm ci
    npm run install:browsers
    npm test
  env:
    BASE_URL: ${{ secrets.BASE_URL }}
    API_URL: ${{ secrets.API_URL }}
    TEST_EMAIL: ${{ secrets.TEST_EMAIL }}
    TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
    CI: true
```
