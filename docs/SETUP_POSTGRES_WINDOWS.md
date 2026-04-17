# Setup PostgreSQL nativo en Windows

Guia para instalar PostgreSQL 16 nativo (sin Docker) y configurar la DB de desarrollo y tests.

## 1. Instalacion

### Opcion A: Instalador oficial EDB

1. Descarga el instalador: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
2. Elige "Windows x86-64" version 16.x
3. Ejecuta el `.exe` como administrador
4. **Password del superuser postgres**: anota la que elijas (ejemplo: `PostgresDev123!`)
5. **Puerto**: deja el default `5432`
6. **Locale**: Spanish, Peru
7. Desmarca "Stack Builder" al final (no se necesita)

### Opcion B: Via Chocolatey (mas rapido si ya lo tienes)

```powershell
choco install postgresql16 --params '/Password:PostgresDev123!'
```

## 2. Verificar instalacion

Abre PowerShell y ejecuta:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "SELECT version();"
```

Pide la password que configuraste. Debe mostrar la version de Postgres.

## 3. Agregar psql al PATH (opcional pero util)

```powershell
[Environment]::SetEnvironmentVariable("Path", "$env:Path;C:\Program Files\PostgreSQL\16\bin", "User")
```

Cierra y reabre la terminal.

## 4. Crear las bases de datos para SAAS COREM

```powershell
# DB de desarrollo
psql -U postgres -c "CREATE DATABASE saas_corem_dev;"

# DB de tests (pytest la usa con prefijo test_)
psql -U postgres -c "CREATE DATABASE saas_corem_test;"
```

## 5. Configurar el backend

Crea `backend/.env` (copia de `backend/.env.example`) con:

```env
DEBUG=True
SECRET_KEY=django-insecure-dev-local-change-for-prod
ALLOWED_HOSTS=localhost,127.0.0.1,test.localhost

# PostgreSQL nativo
DB_HOST=localhost
DB_PORT=5432
DB_NAME=saas_corem_dev
DB_USER=postgres
DB_PASSWORD=PostgresDev123!

# Redis desactivado en dev (Celery eager mode)
CELERY_TASK_ALWAYS_EAGER=True
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Email (console backend en dev)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## 6. Ejecutar migraciones y crear tenant

```powershell
cd backend
venv\Scripts\activate
pip install -r requirements\dev.txt
python manage.py migrate_schemas --shared
python manage.py migrate_schemas --tenant
```

Crea el tenant publico y un tenant de prueba:

```powershell
python manage.py shell
```

```python
from apps.tenants.models import Tenant, Domain

# Tenant publico
public, _ = Tenant.objects.get_or_create(
    schema_name="public",
    defaults={"nombre": "Public", "ruc": "00000000000"},
)
Domain.objects.get_or_create(domain="localhost", tenant=public, defaults={"is_primary": True})

# Tenant de prueba (jardin garabato)
garabato, _ = Tenant.objects.get_or_create(
    schema_name="garabato",
    defaults={"nombre": "Jardin Garabato", "ruc": "20123456789"},
)
Domain.objects.get_or_create(domain="garabato.localhost", tenant=garabato, defaults={"is_primary": True})
exit()
```

## 7. Crear superadmin

```powershell
python manage.py createsuperuser
```

## 8. Ejecutar tests

```powershell
cd backend
pytest --ds=config.settings.test
```

Deberias ver los ~40 tests escritos pasar. Si alguno falla, lee el output y reportalo.

## 9. Levantar el servidor de desarrollo

```powershell
# Backend (puerto 8000)
cd backend
python manage.py runserver 0.0.0.0:8000

# Frontend (puerto 3000) -- en otra terminal
cd frontend
npm install
npm run dev
```

Abre http://garabato.localhost:3000 (el subdominio corresponde al tenant).

---

## Comandos utiles de PostgreSQL

```powershell
# Listar bases
psql -U postgres -l

# Entrar a una base
psql -U postgres -d saas_corem_dev

# Ver schemas (tenants)
psql -U postgres -d saas_corem_dev -c "SELECT schema_name FROM information_schema.schemata;"

# Dump de backup
pg_dump -U postgres saas_corem_dev > backup.sql

# Restore
psql -U postgres saas_corem_dev < backup.sql
```

## Troubleshooting

**"psql: connection refused"**
- Verifica que el servicio este corriendo: `Get-Service postgresql-x64-16`
- Si esta detenido: `Start-Service postgresql-x64-16`

**"FATAL: password authentication failed"**
- Usa `-W` para forzar prompt: `psql -U postgres -W`
- Reset password: edita `pg_hba.conf` temporalmente a `trust`, reinicia, cambia password, vuelve a `md5`

**"could not connect to server"**
- Abre el Windows Firewall para permitir puerto 5432 (o desactivalo para dev)
