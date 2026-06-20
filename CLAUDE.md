# Miniddo — SaaS de gestión para jardines de infancia

Producto de **COREM LABS S.A.C.** Django multi-tenant (django-tenants) + React. Este repo tiene `backend/`, `frontend/` y `e2e/`.

## 📚 Documentación viva (LEER PRIMERO)

El alcance completo y actualizado del proyecto vive como **documentación viva** en el segundo cerebro (Obsidian):

- `E:\SegundoCerebro\02-Proyectos\Miniddo.md` — hub / índice
- `Miniddo - Arquitectura backend.md` · `Miniddo - Frontend.md` · `Miniddo - Plataforma y negocio.md` · `Miniddo - Testing y QA.md`

**Regla de doc viva (OBLIGATORIA):** cada vez que cambies algo estructural del SaaS — un modelo, una app, un endpoint, una página, el pricing, una política de negocio — **actualizá la nota de dominio correspondiente** en Obsidian y bumpeá su campo `modificado`. La fuente de verdad es el código; si una nota discrepa, gana el código y se corrige la nota. (Memoria Engram: proyecto `saas-corem`, topic `miniddo/living-docs`.)

## Arranque rápido (dev)

**Backend** (desde `backend/`, con el venv activado):
- `python manage.py runserver --settings=config.settings.dev`
- Admin SuperAdmin: http://localhost:8000/admin/
- DB dev: vars `DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT` (puerto `5433`). **NO** usar `POSTGRES_*`.

**Frontend** (desde `frontend/`):
- `npm run dev` → http://localhost:3000
- El proxy de `/api` y `/media` usa `changeOrigin: false` — **no lo cambies**: preserva el `Host` para que django-tenants resuelva el schema.

**E2E** (desde `e2e/`):
- `npx playwright test`

## Multi-tenant — gotchas

- Schema de PostgreSQL por jardín (`TENANT_MODEL = tenants.Tenant`); el tenant se resuelve por dominio/subdominio.
- En dev, entrá por el host del tenant (subdominio), **no** por `localhost` pelado, o se rompe el routing.
- El frontend manda `X-Tenant: <slug>` (del subdominio) en cada request.
- Prod: dominio base `miniddo.com`; DB con vars `PG*` (Railway).

## Pricing (tiers por alumnos)

`mini` 1–30 → S/100 · `plus` 31–60 → S/180 · `pro` 61–90 → S/280 · `max` 91+ → S/380. En el admin: `precio_mensual` = lista, `precio_minimo` = piso negociable. Detalle en la nota *Plataforma y negocio*.

## Identidad visual

Producto COREM → usa la **paleta oficial de COREM** (`E:\COREM\COREM\MARCA_COREM\`). El tema de Ant Design (`colorPrimary`) y los estilos del admin deben seguir esa paleta.
