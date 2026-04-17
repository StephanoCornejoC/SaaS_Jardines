# SAAS COREM - Performance Tests (k6)

Suite de pruebas de rendimiento para SAAS COREM usando [k6 de Grafana](https://k6.io/).

## Stack

- **Runtime**: k6 (binario Go, no Node.js)
- **Backend**: Django 5.x + DRF + PostgreSQL + Redis
- **Auth**: JWT via SimpleJWT (POST /api/v1/auth/token/)
- **Multi-tenant**: django-tenants (header `Host` obligatorio en cada request)
- **Deploy target**: Railway.app (~512MB RAM, ~0.5-1 vCPU compartido)

---

## Instalacion de k6

```bash
# Windows (winget)
winget install k6 --source winget

# Windows (Chocolatey)
choco install k6

# Linux (apt)
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \
  | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update && sudo apt-get install k6

# macOS
brew install k6

# Docker
docker run --rm -i grafana/k6 version
```

Verificar instalacion: `k6 version`

---

## Estructura

```
performance/
├── config/
│   ├── environments.js     # URLs, credenciales y fixtures por ambiente
│   └── thresholds.js       # SLAs y thresholds por tipo de test
├── helpers/
│   ├── auth.js             # JWT login, refresh, headers con Host multi-tenant
│   └── data.js             # Generadores de datos de prueba (prefijo PERF_)
├── scripts/
│   ├── smoke.js            # 1 VU / 30s - validacion basica
│   ├── load.js             # 20 VUs / 8min - dia normal del jardin
│   ├── stress.js           # ramp 10->100 VUs - punto de quiebre Railway
│   ├── spike.js            # 5->80->5 VUs - picos subitos
│   ├── soak.js             # 15 VUs / 37min - memory leaks
│   ├── crud-students.js    # CRUD completo de alumnos con RBAC
│   ├── payments-flow.js    # Flujo completo de registro de pensiones
│   └── reports-heavy.js    # Generacion concurrente de Excel
└── scenarios/
    └── mixed-realistic.js  # 70% lectura / 20% escritura / 10% reportes
```

---

## SLAs (Railway 512MB)

| Categoria | p95 | p99 | Error rate |
|-----------|-----|-----|------------|
| CRUD (alumnos, pagos, aulas) | < 500ms | < 1000ms | < 1% |
| Dashboard / KPIs | < 1000ms | < 2000ms | < 1% |
| Cashflow con filtros | < 800ms | < 1500ms | < 1% |
| Auth (login, refresh) | < 300ms | < 600ms | < 1% |
| Registro masivo asistencia | < 2000ms | < 4000ms | < 1% |
| Reportes Excel | < 3000ms | < 6000ms | < 5% |
| Throughput minimo | 50 req/s | - | - |

---

## Configuracion de ambientes

Seleccionar el ambiente con `--env ENV=<nombre>`:

| Ambiente | URL por defecto | Uso |
|----------|----------------|-----|
| `local`   | http://localhost:8000 | Desarrollo local / Docker Compose |
| `staging` | Configurar via `STAGING_BASE_URL` | Railway staging |
| `prod`    | Configurar via `PROD_BASE_URL` | NUNCA stress/soak |

### Variables de entorno para staging

```bash
export STAGING_BASE_URL="https://saas-corem-staging.up.railway.app"
export STAGING_TENANT_HOST="garabato.saascorem.com"
export STAGING_ADMIN_EMAIL="admin@garabato.corem.pe"
export STAGING_ADMIN_PASS="..."
export STAGING_SECRETARY_EMAIL="secretaria@garabato.corem.pe"
export STAGING_SECRETARY_PASS="..."
export STAGING_TEACHER_EMAIL="docente@garabato.corem.pe"
export STAGING_TEACHER_PASS="..."
export STAGING_DIRECTOR_EMAIL="director@garabato.corem.pe"
export STAGING_DIRECTOR_PASS="..."
```

### Header Host (django-tenants)

Todos los scripts incluyen automaticamente el header `Host: <tenantHost>` en cada request. Sin este header, django-tenants enruta al schema publico y los endpoints devuelven 404.

---

## Ejecutar los tests

### Orden recomendado (siempre empezar por smoke)

```bash
# 1. Smoke: validar que todo responde antes de ejecutar los demas
k6 run --env ENV=local scripts/smoke.js

# 2. CRUD especificos
k6 run --env ENV=local scripts/crud-students.js
k6 run --env ENV=local scripts/payments-flow.js

# 3. Load: carga normal
k6 run --env ENV=local scripts/load.js

# 4. Reports: endpoints pesados
k6 run --env ENV=local scripts/reports-heavy.js

# 5. Spike: picos
k6 run --env ENV=staging scripts/spike.js

# 6. Stress: encontrar limite (solo en staging)
k6 run --env ENV=staging scripts/stress.js

# 7. Soak: memory leaks (solo en staging)
k6 run --env ENV=staging scripts/soak.js

# 8. Escenario mixto realista
k6 run --env ENV=staging scenarios/mixed-realistic.js
```

### Con salida a JSON para analisis posterior

```bash
k6 run --env ENV=local \
  --out json=results/load-results.json \
  scripts/load.js
```

### Con InfluxDB + Grafana (metricas en tiempo real)

```bash
k6 run --env ENV=staging \
  --out influxdb=http://localhost:8086/k6 \
  scripts/load.js
```

### Con Grafana Cloud

```bash
K6_CLOUD_TOKEN=<token> k6 run --out cloud scripts/load.js
```

---

## Interpretacion de resultados

### Metricas clave de k6

| Metrica | Descripcion |
|---------|-------------|
| `http_req_duration` | Tiempo total de la request (incluye conexion + espera + respuesta) |
| `http_req_failed` | Rate de requests fallidas (status >= 400 o error de red) |
| `http_reqs` | Throughput (requests por segundo) |
| `http_req_waiting` | Tiempo que el servidor tarda en empezar a responder (TTFB) |
| `vus` | Usuarios virtuales activos en cada momento |
| `dashboard_duration` | Custom: tiempo del endpoint /dashboard/resumen/ |
| `report_generation_duration` | Custom: tiempo de generacion de Excel |
| `bulk_attendance_duration` | Custom: tiempo del registro masivo de asistencia |
| `payment_registration_duration` | Custom: tiempo de POST /payments/ |

### Señales de problemas en Railway

| Sintoma | Causa probable | Accion |
|---------|---------------|--------|
| Errores 502 en stress | Railway reinicio el dyno (OOM o CPU) | Revisar RAM en Railway dashboard |
| Errores 503 en reports | Django no responde, Railway proxy timeout | Generar Excel de forma asincrona |
| p95 crece en soak | Memory leak en Django o PostgreSQL | Revisar connection pool, query sin cerrar |
| `http_req_waiting` alto | Cola de requests en Django (workers saturados) | Aumentar workers de gunicorn o usar async |
| Degradacion post-spike | El sistema no se recupera correctamente | Revisar limites de conexiones DB |

---

## Limpieza de datos de prueba

Los scripts generan datos con prefijos identificables:

```sql
-- Alumnos de prueba
DELETE FROM students_student WHERE apellido_paterno = 'PerformanceTest';

-- Pagos de prueba
DELETE FROM payments_payment WHERE numero_comprobante LIKE 'PERF-%';

-- Emails de prueba
DELETE FROM users_user WHERE email LIKE '%@test-k6.corem';
```

O via Django management command (si existe):
```bash
python manage.py cleanup_perf_data
```

---

## Integracion con CI/CD (GitHub Actions)

```yaml
# .github/workflows/performance.yml
name: Performance Tests (Smoke)
on:
  push:
    branches: [main, develop]

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install k6
        run: |
          sudo gpg --no-default-keyring \
            --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
            --keyserver hkp://keyserver.ubuntu.com:80 \
            --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] \
            https://dl.k6.io/deb stable main" \
            | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update && sudo apt-get install k6

      - name: Run Smoke Test
        run: |
          k6 run \
            --env ENV=staging \
            --env STAGING_BASE_URL=${{ secrets.STAGING_BASE_URL }} \
            --env STAGING_TENANT_HOST=${{ secrets.STAGING_TENANT_HOST }} \
            --env STAGING_SECRETARY_EMAIL=${{ secrets.STAGING_SECRETARY_EMAIL }} \
            --env STAGING_SECRETARY_PASS=${{ secrets.STAGING_SECRETARY_PASS }} \
            --env STAGING_DIRECTOR_EMAIL=${{ secrets.STAGING_DIRECTOR_EMAIL }} \
            --env STAGING_DIRECTOR_PASS=${{ secrets.STAGING_DIRECTOR_PASS }} \
            --env STAGING_TEACHER_EMAIL=${{ secrets.STAGING_TEACHER_EMAIL }} \
            --env STAGING_TEACHER_PASS=${{ secrets.STAGING_TEACHER_PASS }} \
            performance/scripts/smoke.js
```

---

## Notas importantes

1. **Siempre ejecutar smoke primero**: Si el smoke falla, los demas tests no tienen sentido.
2. **NUNCA ejecutar stress/soak en produccion**: Railway reinicia el dyno y afecta a usuarios reales.
3. **El header Host es obligatorio**: Sin el header correcto, django-tenants no enruta al tenant.
4. **Think times realistas**: Los scripts incluyen `sleep()` para simular comportamiento humano real.
5. **Datos de limpieza**: Todos los registros de prueba usan prefijo `PERF_` o `@test-k6.corem`.
6. **Correlacionar con Railway**: Los errores 502/503 deben correlacionarse con las metricas de RAM/CPU en el dashboard de Railway durante el mismo periodo.
