import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="dashboard.calculate_daily_metrics")
def task_calculate_daily_metrics():
    """
    Calcula las métricas diarias del dashboard.
    Ejecutar diariamente (ej: a las 6:00 AM).
    """
    from apps.dashboard.services import calculate_daily_metrics

    try:
        metric = calculate_daily_metrics()
        logger.info(f"Métricas del dashboard calculadas para {metric.fecha}")
        return {"fecha": str(metric.fecha), "status": "ok"}
    except Exception as e:
        logger.error(f"Error calculando métricas del dashboard: {e}")
        raise
