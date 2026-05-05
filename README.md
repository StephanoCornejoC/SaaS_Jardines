# SAAS COREM — Jardín Garabato

Sistema SaaS multi-tenant para gestión integral de jardines de infancia (Perú).

**Piloto**: Jardín Garabato
**Stack**: Django 5.2 + DRF + React 18 + Vite + PostgreSQL 16 + (Redis/Celery opcional)
**Deploy**: Railway (backend) · Vercel (frontend) · monorepo único

---

## 📁 Estructura del monorepo

```
SAAS_COREM/                    ← raíz del repo (root del git)
├── backend/                   ← deploy a Railway (root: backend/)
│   ├── apps/                  13 apps Django
│   ├── config/
│   │   ├── settings/          base.py · dev.py · test.py · prod.py
│   │   └── admin_site.py      CoremAdminSite custom
│   ├── shared/
│   ├── static/                ← editable (corem.css, etc.)
│   ├── staticfiles/           ← gitignored (output de collectstatic)
│   ├── templates/admin/       overrides del admin (drawer, jardín, etc.)
│   ├── Dockerfile             ← Railway lo usa
│   ├── railway.json           ← config Railway
│   ├── requirements/          base.txt · dev.txt · prod.txt
│   ├── manage.py
│   └── .env.production.example
│
├── frontend/                  ← deploy a Vercel (root: frontend/)
│   ├── src/                   13 páginas React
│   ├── public/
│   ├── vite.config.js
│   ├── vercel.json            ← SPA rewrites + cache de assets
│   ├── package.json
│   └── .env.production.example
│
├── e2e/                       Playwright tests (24 TCs)
├── serenity/                  Serenity BDD + Screenplay
├── performance/               k6 scripts
├── docs/                      Documentación
├── .gitignore
└── README.md                  ← este archivo
```

---

## 🚀 Deploy a producción

### Backend en Railway

1. Crea un nuevo proyecto en Railway → **Deploy from GitHub repo** → selecciona este repo.
2. **Settings → General** del servicio:
   - **Root Directory**: `backend`
   - **Builder**: el repo trae `backend/Dockerfile` y `backend/railway.json`, Railway los detecta solo
3. **Add plugin → PostgreSQL** (Railway inyecta `PGHOST`, `PGUSER`, `PGPASSWORD`, `PGPORT`, `PGDATABASE` automáticamente)
4. (opcional) **Add plugin → Redis** si vas a correr Celery worker
5. **Variables → Raw editor**, pega esto y reemplaza valores:
   ```
   DJANGO_SETTINGS_MODULE=config.settings.prod
   DJANGO_SECRET_KEY=<genera con: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
   DEBUG=False
   ALLOWED_HOSTS=.railway.app,api.corem.pe,admin.corem.pe
   CORS_ALLOWED_ORIGINS=https://app.corem.pe,https://corem-frontend.vercel.app
   CSRF_TRUSTED_ORIGINS=https://app.corem.pe,https://corem-frontend.vercel.app,https://admin.corem.pe
   EMAIL_HOST=smtp.gmail.com
   EMAIL_HOST_USER=tunotificador@gmail.com
   EMAIL_HOST_PASSWORD=<app password de 16 caracteres>
   DEFAULT_FROM_EMAIL=noreply@corem.pe
   SUPERADMIN_EMAIL=tu_correo@corem.pe
   TENANT_BASE_DOMAIN=corem.pe
   ```
6. **Deploy** → Railway construye con el Dockerfile, ejecuta `migrate_schemas --shared && collectstatic && gunicorn ...` (definido en `railway.json`)
7. Cuando termine el primer deploy, abre el shell del servicio (`railway run bash` o desde la consola web) y ejecuta:
   ```bash
   python manage.py create_tenant_superuser --schema=public
   # email, password, etc.
   python manage.py fix_localhost_domain   # solo si vas a probar local también
   ```
8. (opcional) Configura un **Cron Job** en Railway:
   - Schedule: `0 8 * * *`
   - Command: `python manage.py notificar_vencimientos`

### Frontend en Vercel

1. Crea un nuevo proyecto en Vercel → **Import Git Repository** → selecciona este repo.
2. **Configure Project**:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. **Environment Variables**:
   ```
   VITE_API_URL=https://<tu-backend>.up.railway.app
   ```
4. **Deploy**.
5. (opcional) **Domains**: añade `app.corem.pe` y configura el CNAME.

---

## 💻 Desarrollo local

### Prerequisitos

- Python 3.12+ (Railway usa 3.12 en el Dockerfile)
- Node.js 18+
- PostgreSQL 16 nativo o vía Docker

### Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements\dev.txt
copy .env.example .env
# edita .env con credenciales locales (DB_HOST, DB_USER, etc.)
python manage.py migrate_schemas --shared --settings=config.settings.dev
python manage.py create_tenant_superuser --schema=public --settings=config.settings.dev
python manage.py fix_localhost_domain --settings=config.settings.dev   # solo primera vez
python manage.py runserver --settings=config.settings.dev
```

Admin del SuperAdmin: <http://localhost:8000/admin/>

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend del jardín: <http://127.0.0.1:3000>

> ⚠️ Usa `127.0.0.1`, no `localhost`. `localhost` apunta al schema `public` (admin) y `127.0.0.1` al schema `garabato` (frontend del jardín). Si necesitas resetear esto, corre `python manage.py fix_localhost_domain`.

### Tests

| Capa | Comando | Cantidad |
|---|---|---|
| Unit / Integration | `cd backend && pytest --ds=config.settings.test` | ~80 |
| E2E rápido | `cd e2e && npx playwright test` | 24 |
| E2E BDD | `cd serenity && mvn clean verify` | ~30 |
| Performance | `cd performance && k6 run scripts/load.js` | 8 escenarios |

---

## 🏗 Arquitectura

```
┌──────────────────┐       HTTPS        ┌────────────────────┐
│  Vercel (free)   │ ─────────────────► │  Railway ($5/mo)   │
│  React + Vite    │                    │  Django 5.2 + DRF  │
│  Ant Design      │ ◄───── /api/v1 ──── │  django-tenants    │
└──────────────────┘                    └─────────┬──────────┘
                                                  │
                                  ┌───────────────┴────────────────┐
                                  ▼                                ▼
                          ┌───────────────┐                ┌───────────────┐
                          │  PostgreSQL   │                │    Redis      │
                          │  (Railway)    │                │  (opcional)   │
                          └───────────────┘                └───────────────┘

  Multi-tenant schemas en una sola BD:
  ├── public        ← shared: Tenant, Domain, User, Plan, TenantSubscription, etc.
  ├── garabato      ← cliente piloto (alumnos, pagos, caja, etc.)
  ├── cliente2      ← otro jardín
  └── ...
```

### Routing por dominio (django-tenants)

| Dominio | Schema |
|---|---|
| `localhost`, `admin.corem.pe` | `public` (panel SuperAdmin) |
| `127.0.0.1`, `garabato.corem.pe` | `garabato` |
| `<nuevo>.corem.pe` | `<nuevo>` |

---

## 🗂 Documentación

| Documento | Descripción |
|---|---|
| [`docs/DEPLOY_RAILWAY_VERCEL.md`](docs/DEPLOY_RAILWAY_VERCEL.md) | Deploy paso a paso |
| [`docs/USER_CAPABILITIES.md`](docs/USER_CAPABILITIES.md) | Lo que puede hacer cada usuario |
| [`docs/SETUP_POSTGRES_WINDOWS.md`](docs/SETUP_POSTGRES_WINDOWS.md) | PostgreSQL en Windows |
| [`docs/QA_STRATEGY_SAAS_COREM.md`](docs/QA_STRATEGY_SAAS_COREM.md) | Estrategia de testing |
| [`docs/SECURITY_ASSESSMENT.md`](docs/SECURITY_ASSESSMENT.md) | Auditoría OWASP Top 10 |

---

## 🛠 Comandos útiles

```powershell
# Backend
python manage.py migrate_schemas --shared --settings=config.settings.dev
python manage.py create_tenant_superuser --schema=public --settings=config.settings.dev
python manage.py fix_localhost_domain --settings=config.settings.dev
python manage.py generar_cobros_mes --settings=config.settings.dev
python manage.py revisar_morosidad --settings=config.settings.dev
python manage.py notificar_vencimientos --dry-run --settings=config.settings.dev
python manage.py collectstatic --settings=config.settings.dev
pytest --ds=config.settings.test -v

# Frontend
npm run dev
npm run build
npm run lint

# E2E
npx playwright test --ui
mvn clean verify -f serenity/pom.xml
```

---

## 📝 Decisiones clave

- **Multi-tenant** por schema PostgreSQL (django-tenants)
- **Auth**: JWT (simplejwt) con refresh queue + single session
- **Pagos del SaaS**: precio personalizado por jardín (no plan único), trial 30 días configurable, día de cobro configurable (1-28)
- **Planes**: principal + N planes promocionales/campaña paralelos
- **Notificaciones**: email automático al SuperAdmin de vencimientos próximos (cron diario)
- **Política de morosidad**: día 3 alerta, día 7 bloqueo automático (HTTP 402), desbloqueo manual
- **Frontend del jardín**: solo email + WhatsApp (vía `wa.me`, gratis), pagos manuales con QR Yape/Plin
- **Admin del SuperAdmin**: drill-down completo a cada tenant via `schema_context()` sin cambiar de host

---

## 📞 Contacto

- **COREM Labs SAC**
- **Email**: scornejoc@bsginstitute.com
- **Piloto**: Jardín Garabato (Lima, Perú)

## Licencia

Privado — © COREM Labs SAC
