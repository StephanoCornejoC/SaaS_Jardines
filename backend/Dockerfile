FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies:
# - build-essential, libpq-dev: psycopg2 build
# - libcairo2-dev, pkg-config: pycairo (transitive de xhtml2pdf → svglib → rlpycairo).
#   pycairo NO tiene wheel para Python 3.12 en PyPI, pip lo compila desde C
#   source y requiere headers de cairo + pkg-config para que meson lo encuentre.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libcairo2-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copiar el directorio requirements/ completo (prod.txt referencia base.txt
# con `-r base.txt`, ambos archivos deben estar presentes para que pip resuelva)
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/prod.txt

COPY . .

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
