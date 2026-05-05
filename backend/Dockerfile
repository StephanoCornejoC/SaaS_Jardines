FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

# System dependencies for psycopg2 (xhtml2pdf is pure Python)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias primero (mejor cache)
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/prod.txt

# Copiar el código
COPY . .

# collectstatic se ejecuta en deploy via railway.json startCommand;
# aquí lo dejamos para validación local del build
RUN python manage.py collectstatic --noinput || echo "collectstatic warning ignored at build time"

EXPOSE 8000

# Comando default — Railway lo override con startCommand de railway.json
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
