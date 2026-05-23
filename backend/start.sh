#!/bin/sh
# Entry point del servicio web en Railway.
#
# Diseño:
#   - migrate_schemas vive en preDeployCommand (corre antes del container)
#     porque toca el schema de DB y queremos que falle deploy si falla.
#   - createcachetable y ensure_superuser viven aca en start.sh porque son
#     idempotentes (no rompen si la tabla/user ya existe) y porque
#     observamos que el preDeployCommand de Railway no ejecutaba consistentemente
#     todos los comandos encadenados con &&.
#
# Variables:
#   $PORT: Railway lo inyecta; necesitamos shell expansion (por eso el .sh).

set -e

echo "=== Step: createcachetable ==="
python -u manage.py createcachetable || echo "createcachetable: tabla ya existia (OK)"

echo "=== Step: ensure_superuser ==="
python -u manage.py ensure_superuser

echo "=== Step: starting gunicorn on port $PORT ==="
exec python -u -m gunicorn config.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --timeout 300 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
