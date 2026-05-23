"""
Endpoints para disparar el cron diario del SaaS.

Hay 2 entry points:

1. `daily_cron_token_view` — POST /api/v1/cron/daily/
   - Disparado por GitHub Actions (.github/workflows/daily-cron.yml) todos
     los dias a las 13:00 UTC (8:00 AM Lima).
   - Auth: header `Authorization: Bearer <CRON_SECRET_TOKEN>`.
   - CSRF exempt (lo llama un agente externo sin sesion ni cookie).
   - Devuelve JSON con stdout/stderr del management command.

2. `daily_cron_manual_view` — POST /admin/cron/daily/
   - Boton "Ejecutar tareas diarias ahora" en el index del admin Kiddo.
   - Auth: sesion + is_superuser=True.
   - CSRF habilitado (request viene del form del admin).
   - Redirige al index del admin con un messages.success/error.

Ambos ejecutan el mismo management command `daily_saas_run` (en
apps/platform/management/commands/) capturando su stdout/stderr para
visibilidad. Ese command es idempotente: si corre dos veces el mismo dia
no duplica cobros ni emails.
"""
import logging
import os
from io import StringIO

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


def _run_daily_cron():
    """
    Ejecuta `daily_saas_run` capturando stdout/stderr.

    Returns:
        tuple (ok: bool, stdout: str, stderr: str)
    """
    out = StringIO()
    err = StringIO()
    try:
        call_command("daily_saas_run", stdout=out, stderr=err)
        return True, out.getvalue(), err.getvalue()
    except Exception as e:
        logger.exception("daily_saas_run failed")
        # Combinar lo que alcanzo a imprimir + el error que rompio
        return False, out.getvalue(), f"{err.getvalue()}\n\nException: {e}"


@csrf_exempt
@require_POST
def daily_cron_token_view(request):
    """Endpoint disparado por GitHub Actions. Auth: Bearer token."""
    expected = os.environ.get("CRON_SECRET_TOKEN", "").strip()
    if not expected:
        return JsonResponse(
            {"ok": False, "error": "CRON_SECRET_TOKEN not configured"},
            status=503,
        )

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JsonResponse(
            {"ok": False, "error": "missing or malformed Authorization header"},
            status=401,
        )

    provided = auth_header[len("Bearer "):].strip()
    if provided != expected:
        logger.warning("daily_cron: invalid token attempt from %s", request.META.get("REMOTE_ADDR"))
        return JsonResponse({"ok": False, "error": "invalid token"}, status=403)

    logger.info("daily_cron: token valido, ejecutando daily_saas_run")
    ok, stdout, stderr = _run_daily_cron()
    return JsonResponse(
        {"ok": ok, "stdout": stdout, "stderr": stderr},
        status=200 if ok else 500,
    )


@require_POST
@staff_member_required
def daily_cron_manual_view(request):
    """Boton del admin Kiddo. Auth: sesion + SUPERADMIN."""
    if not request.user.is_superuser:
        return JsonResponse({"ok": False, "error": "superadmin required"}, status=403)

    logger.info("daily_cron: ejecucion manual disparada por %s", request.user.email)
    ok, stdout, stderr = _run_daily_cron()

    if ok:
        # Mostrar las primeras lineas del stdout como confirmacion
        preview = "\n".join(stdout.strip().split("\n")[-6:]) if stdout else "Sin salida."
        messages.success(
            request,
            f"Tareas diarias ejecutadas correctamente.\n{preview}",
        )
    else:
        messages.error(request, f"Error ejecutando tareas: {stderr or 'sin detalle'}")

    return redirect("admin:index")
