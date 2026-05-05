try:
    from .celery import app as celery_app
    __all__ = ("celery_app",)
except ImportError:
    # celery no instalado (entorno dev sin worker, management commands, etc.)
    pass
