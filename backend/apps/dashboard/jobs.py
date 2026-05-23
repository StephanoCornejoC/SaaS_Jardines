"""
Job de cálculo de métricas del dashboard. Función plana invocable desde el
cron consolidado `daily_saas_run` o desde tests. No usa Celery.
"""
import logging

logger = logging.getLogger(__name__)


def run_daily_metrics_job():
    """Calcula las métricas diarias del dashboard."""
    from apps.dashboard.services import calculate_daily_metrics

    try:
        metric = calculate_daily_metrics()
        logger.info(f"Métricas del dashboard calculadas para {metric.fecha}")
        return {"fecha": str(metric.fecha), "status": "ok"}
    except Exception as e:
        logger.error(f"Error calculando métricas del dashboard: {e}")
        raise
