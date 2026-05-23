# SAAS COREM - Jardin Garabato

Sistema SaaS multi-tenant para gestion integral de jardines de infancia (Peru).

**Piloto:** Jardin Garabato
**Stack:** Django 5.1 + React 18 + PostgreSQL 16 + Celery/Redis
**Deploy:** Railway (backend) + Vercel (frontend)

---

## Inicio rapido

### 1. Prerequisitos
- Python 3.12+
- Node.js 18+
- PostgreSQL 16 nativo (ver guia: [`docs/SETUP_POSTGRES_WINDOWS.md`](docs/SETUP_POSTGRES_WINDOWS.md))
- Java 17 + Maven (solo si vas a correr tests Serenity BDD)

### 2. Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements\dev.txt
copy .env.example .env
# edita .env con tus credenciales de PostgreSQL
python manage.py migrate_schemas --shared
python manage.py migrate_schemas --tenant
python manage.py createsuperuser
python manage.py runserver
```

### 3. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Abre http://localhost:3000

### 4. Tests

**Backend (pytest, ~80 tests):**
```powershell
cd backend
pytest --ds=config.settings.test
```

**E2E Playwright (24 tests):**
```powershell
cd e2e
npm install
npx playwright install
npx playwright test
```

**E2E Serenity BDD (living documentation):**
```powershell
cd serenity
mvn clean verify
# Reporte: target/site/serenity/index.html
```

---

## Documentacion

| Documento | Para que |
|-----------|----------|
| [`docs/USER_CAPABILITIES.md`](docs/USER_CAPABILITIES.md) | Que puede hacer un usuario del SaaS |
| [`docs/SETUP_POSTGRES_WINDOWS.md`](docs/SETUP_POSTGRES_WINDOWS.md) | Instalar PostgreSQL nativo |
| [`docs/DEPLOY_RAILWAY_VERCEL.md`](docs/DEPLOY_RAILWAY_VERCEL.md) | Deploy a produccion |
| [`docs/QA_STRATEGY_SAAS_COREM.md`](docs/QA_STRATEGY_SAAS_COREM.md) | Estrategia de testing |
| [`docs/SECURITY_ASSESSMENT.md`](docs/SECURITY_ASSESSMENT.md) | Auditoria OWASP Top 10 |
| [`docs/STATIC_ANALYSIS_REPORT.md`](docs/STATIC_ANALYSIS_REPORT.md) | Reporte analisis estatico |

---

## Arquitectura

```
+-------------------+           +--------------------+
|   Vercel (free)   |  HTTPS    |   Railway ($5/mo)  |
|   React + Vite    |---------->|   Django + DRF     |
|   Ant Design      |           |   Celery + Beat    |
+-------------------+           +----------+---------+
                                           |
                          +----------------+---------------+
                          |                                |
                   +------v------+                  +------v------+
                   | PostgreSQL  |                  |    Redis    |
                   | (Railway)   |                  | (Railway)   |
                   +-------------+                  +-------------+

   Multi-tenant schemas:
   - public (shared: tenants, users)
   - garabato (jardin cliente 1)
   - cliente2 (jardin cliente 2)
   ...
```

---

## Estructura del repositorio

```
SAAS_COREM/
|-- backend/              Django backend (13 apps, 27 modelos, ~80 tests)
|   |-- apps/
|   |-- config/settings/  base.py, dev.py, test.py, prod.py
|   |-- shared/           validators, mixins, utils
|   |-- Dockerfile        Para Railway deploy
|   |-- railway.json      Config de Railway
|   `-- .env.production.example
|-- frontend/             React + Vite (13 paginas)
|   |-- src/
|   |   |-- pages/
|   |   |-- components/
|   |   |-- services/     api.js con timeout + refresh queue
|   |   `-- store/        Zustand
|   `-- .env.production.example
|-- e2e/                  Playwright (24 tests)
|-- serenity/             Serenity BDD + Screenplay Pattern
|-- performance/          k6 (8 scenarios)
|-- docs/                 Toda la documentacion
`-- README.md             (este archivo)
```

---

## Stack de pruebas

| Capa | Framework | Archivos | Tests |
|------|-----------|----------|-------|
| Unit / Integration | pytest + pytest-django | 28 archivos | ~80 |
| E2E (rapido) | Playwright + TypeScript | 9 specs | 24 |
| E2E (BDD) | Serenity BDD + Cucumber Screenplay | 9 features | ~30 |
| Performance | k6 Grafana | 8 scripts | 5 tipos de carga |
| Security | Security audit manual (docs) | 1 doc | 10 findings |

---

## Estado del proyecto

- [x] Backend: 13 apps, 27 modelos, todas las migraciones
- [x] Frontend: 13 paginas funcionales con Ant Design
- [x] Security fixes: validacion inputs, N+1 optimizado, refresh queue
- [x] Error handling: ErrorBoundary, Popconfirm en deletes, mensajes claros
- [x] ~80 unit/integration tests
- [x] 24 E2E tests Playwright
- [x] Serenity BDD con Screenplay Pattern
- [x] Docs de deploy (Railway + Vercel)
- [x] Docs de capacidades de usuario
- [ ] Pytest ejecutado contra PostgreSQL real (esperando instalacion)
- [ ] Git init + primer commit
- [ ] Deploy a Railway/Vercel productivo

---

## Comandos utiles

```powershell
# Backend
pytest --ds=config.settings.test -v                     # Tests verbosos
pytest --ds=config.settings.test --cov=apps --cov-report=html  # Coverage
ruff check .                                            # Lint
ruff format .                                           # Format

# Frontend
npm run dev                                             # Dev server (port 3000)
npm run build                                           # Build production
npm run lint                                            # ESLint

# E2E
npx playwright test --ui                                # UI mode interactivo
mvn clean verify                                        # Serenity BDD

# Performance
npm run test:smoke                                      # k6 smoke test
npm run test:load                                       # k6 load test
```

---

## Contactos

- **COREM Labs SAC** - Dueno del SaaS
- **Email**: scornejoc@bsginstitute.com
- **Piloto**: Jardin Garabato (Lima, Peru)

---

## Licencia

Privado - COREM Labs SAC
