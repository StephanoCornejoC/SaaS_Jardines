# Deploy a Produccion: Railway (backend) + Vercel (frontend)

Guia paso a paso para deployar SAAS COREM sin Docker local.

---

## 1. Pre-requisitos

- Cuenta en https://railway.app (gratis primer mes $5 de credito, luego ~$5-7/mes)
- Cuenta en https://vercel.com (gratis para personal/hobby)
- Cuenta en https://github.com (gratis)
- Repositorio git del proyecto en GitHub

---

## 2. Variables de entorno necesarias

### Backend (Railway)

| Variable | Valor | Notas |
|----------|-------|-------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` | Usa settings de produccion |
| `DJANGO_SECRET_KEY` | *generada con comando* | Ver abajo |
| `DEBUG` | `False` | NUNCA True en prod |
| `ALLOWED_HOSTS` | `.railway.app,tudominio.com` | Dominio de Railway + custom |
| `DATABASE_URL` | *auto-inyectada por Railway* | Al agregar Postgres plugin |
| `REDIS_URL` | *auto-inyectada por Railway* | Al agregar Redis plugin |
| `CORS_ALLOWED_ORIGINS` | `https://tuapp.vercel.app` | Dominio del frontend |
| `CSRF_TRUSTED_ORIGINS` | `https://tuapp.vercel.app` | Mismo que CORS |
| `EMAIL_HOST` | `smtp.gmail.com` | Para notificaciones email |
| `EMAIL_PORT` | `587` | |
| `EMAIL_USE_TLS` | `True` | |
| `EMAIL_HOST_USER` | `tuemail@gmail.com` | Gmail con app password |
| `EMAIL_HOST_PASSWORD` | *app password gmail* | NO la password normal |
| `DEFAULT_FROM_EMAIL` | `noreply@corem.pe` | |
| `SENTRY_DSN` | *opcional* | Para monitoring de errores |

### Generar SECRET_KEY

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Gmail app password

1. Ve a https://myaccount.google.com/apppasswords
2. Activa 2FA primero
3. Crea una "App password" para "Mail"
4. Copia el codigo de 16 caracteres como `EMAIL_HOST_PASSWORD`

### Frontend (Vercel)

| Variable | Valor |
|----------|-------|
| `VITE_API_URL` | `https://tubackend.railway.app` |

---

## 3. Deploy Backend en Railway

### 3.1. Crear proyecto

1. Login en https://railway.app
2. "New Project" > "Deploy from GitHub repo"
3. Selecciona el repo `SAAS_COREM`
4. Railway detecta el Dockerfile en `/backend/Dockerfile`
5. En "Settings" > "Root Directory" pon `/backend`

### 3.2. Agregar PostgreSQL

1. En el proyecto Railway, click "+ New"
2. "Database" > "Add PostgreSQL"
3. Railway crea una variable `DATABASE_URL` automaticamente
4. Conecta el servicio de Django a la DB (right-click > "Connect")

### 3.3. Agregar Redis (para Celery)

1. "+ New" > "Database" > "Add Redis"
2. Se crea `REDIS_URL` automaticamente

### 3.4. Configurar variables de entorno

En tu servicio de Django > "Variables":
- Copia todas las variables de la tabla anterior
- Railway inyecta `PORT` automaticamente
- NO copies `DATABASE_URL` ni `REDIS_URL` (ya estan)

### 3.5. Verificar deploy

Railway hace deploy automatico al hacer push a main. Verifica:

```
https://tubackend.railway.app/health/
```

Debe responder `{"status": "ok"}` o similar.

### 3.6. Crear tenants iniciales

Desde Railway dashboard > "Service" > "Shell":

```python
python manage.py shell
```

```python
from apps.tenants.models import Tenant, Domain

# Tenant publico
public, _ = Tenant.objects.get_or_create(
    schema_name="public",
    defaults={"nombre": "Public", "ruc": "00000000000"},
)
Domain.objects.get_or_create(
    domain="tubackend.railway.app",
    tenant=public,
    defaults={"is_primary": True},
)

# Cliente Jardin Garabato
garabato, _ = Tenant.objects.get_or_create(
    schema_name="garabato",
    defaults={"nombre": "Jardin Garabato", "ruc": "20123456789"},
)
Domain.objects.get_or_create(
    domain="garabato.tubackend.railway.app",
    tenant=garabato,
    defaults={"is_primary": True},
)
exit()
```

```bash
python manage.py createsuperuser
```

---

## 4. Deploy Frontend en Vercel

### 4.1. Importar proyecto

1. https://vercel.com/new
2. Conecta tu repositorio GitHub
3. Selecciona `SAAS_COREM`
4. Framework: **Vite**
5. Root Directory: `frontend`
6. Build Command: `npm run build` (auto detectado)
7. Output Directory: `dist` (auto detectado)

### 4.2. Variables de entorno

Settings > Environment Variables:

```
VITE_API_URL = https://tubackend.railway.app
```

Aplicar a: Production, Preview, Development

### 4.3. Deploy

Click "Deploy". Vercel construye y publica en ~2 minutos.

URL resultante: `https://tuapp.vercel.app`

### 4.4. Actualizar CORS en backend

Regresa a Railway y actualiza `CORS_ALLOWED_ORIGINS` y `CSRF_TRUSTED_ORIGINS` con el dominio real de Vercel.

---

## 5. Dominio custom (opcional)

### Railway (backend)

Settings > "Networking" > "Custom Domain":
- `api.corem.pe`
- Agrega el CNAME en tu DNS apuntando a `tubackend.railway.app`

### Vercel (frontend)

Settings > "Domains":
- `app.corem.pe`
- Agrega el A record o CNAME en tu DNS

### Actualizar variables

- Backend: `ALLOWED_HOSTS=api.corem.pe,.railway.app`
- Backend: `CORS_ALLOWED_ORIGINS=https://app.corem.pe`
- Frontend: `VITE_API_URL=https://api.corem.pe`

---

## 6. Post-deploy checklist

- [ ] Healthcheck `/health/` responde 200
- [ ] Admin `/corem-panel-x9k2/` accesible (con HTTPS)
- [ ] Frontend carga sin errores en consola
- [ ] Login funciona con superadmin
- [ ] Migraciones aplicadas (verificar en shell)
- [ ] Tenant public y tenants de clientes existen
- [ ] Celery beat corriendo (schedule de tareas)
- [ ] Sentry recibiendo eventos (si configurado)
- [ ] SSL/HTTPS activo en ambos

---

## 7. Monitoreo gratuito

### Sentry (errores)
- https://sentry.io (free: 5k eventos/mes)
- Crea proyecto "Django"
- Copia el DSN al env var `SENTRY_DSN`

### UptimeRobot (uptime)
- https://uptimerobot.com (free: 50 monitores)
- Monitor HTTP al endpoint `/health/` cada 5 min
- Email alert si cae

---

## 8. Costos estimados mensuales

| Servicio | Plan | Costo |
|----------|------|-------|
| Railway Backend | Starter | $5 |
| Railway PostgreSQL | Incluido | $0 |
| Railway Redis | Incluido | $0 |
| Vercel Frontend | Hobby | $0 |
| Sentry | Developer | $0 |
| UptimeRobot | Free | $0 |
| Gmail SMTP | - | $0 |
| **Total** | | **~$5-7/mes** |

---

## 9. Backups

Railway ofrece backups automaticos del Postgres (daily). Para backups manuales:

```bash
# Desde Railway shell
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

Guarda copia externa mensualmente en Google Drive o S3 gratuito.

---

## 10. Rollback

Si un deploy falla:

**Railway**: Deployments > selecciona uno anterior > "Rollback to this deployment"

**Vercel**: Deployments > selecciona uno anterior > "Promote to Production"
