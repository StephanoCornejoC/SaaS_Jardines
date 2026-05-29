import json

from django.contrib.admin.views.decorators import staff_member_required
from django.db import connection
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Plan, TenantSubscription
from .services import metricas_dashboard


@staff_member_required
def admin_dashboard(request):
    data = metricas_dashboard()
    # Serializar a JSON los datos que consumen los charts en JS
    data["series_json"] = json.dumps(data["series"])
    data["distribucion_json"] = json.dumps(data["distribucion"])
    return render(request, "admin/platform/dashboard.html", data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tier_status(request):
    """
    GET /api/v1/platform/tier-status/

    Devuelve el estado del plan del jardín actual y si excede el límite de
    alumnos del tier asignado.

    El request llega con header X-Tenant (vía el interceptor del frontend)
    y `TenantHeaderMiddleware` activa el schema correspondiente. Aquí
    `connection.tenant` apunta al jardín activo.

    Response:
        {
            "plan": {"slug", "nombre", "alumnos_max", "precio_acordado"},
            "alumnos_activos": int,
            "excede_limite": bool,
            "tier_correcto": {"slug", "nombre", "rango"} | null
        }

    Si el tenant no tiene suscripción asignada (caso raro de jardín recién
    creado sin paso por el flow normal), responde 404.
    """
    tenant = getattr(connection, "tenant", None)
    if tenant is None or tenant.schema_name == "public":
        return Response(
            {"detail": "Endpoint disponible solo en contexto de jardín."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        sub = TenantSubscription.objects.select_related("plan").get(tenant=tenant)
    except TenantSubscription.DoesNotExist:
        return Response(
            {"detail": "Este jardín no tiene una suscripción asignada."},
            status=status.HTTP_404_NOT_FOUND,
        )

    n_alumnos = tenant.alumnos_activos_count()
    plan_actual = sub.plan
    tier_correcto = Plan.por_alumnos(n_alumnos)

    excede = (
        plan_actual is not None
        and plan_actual.alumnos_max is not None
        and n_alumnos > plan_actual.alumnos_max
    )

    payload = {
        "plan": {
            "slug": plan_actual.slug if plan_actual else None,
            "nombre": plan_actual.nombre if plan_actual else None,
            "alumnos_max": plan_actual.alumnos_max if plan_actual else None,
            "precio_acordado": str(sub.precio_acordado),
        },
        "alumnos_activos": n_alumnos,
        "excede_limite": excede,
        "tier_correcto": None,
    }

    # Solo incluir tier_correcto si hay diferencia real con el plan actual
    # (si el plan actual ya está OK, el frontend no necesita el otro dato).
    if tier_correcto and plan_actual and tier_correcto.id != plan_actual.id:
        payload["tier_correcto"] = {
            "slug": tier_correcto.slug,
            "nombre": tier_correcto.nombre,
            "rango": tier_correcto.rango_alumnos_texto,
        }

    return Response(payload)
