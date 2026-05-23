#!/bin/sh
# Entry point del servicio web en Railway.
#
# Por que un script .sh en vez de poner el comando directo en railway.json:
# Railway ejecuta el startCommand via execve syscall SIN shell, asi que las
# variables como $PORT no se expanden (gunicorn las recibe literal como string).
# Envolverlo en `sh start.sh` fuerza shell expansion correcta de $PORT y demas.
#
# preDeployCommand (migrations + createcachetable + ensure_superuser) sigue
# corriendo aparte, en railway.json. Este script solo arranca gunicorn.
exec python -u -m gunicorn config.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
