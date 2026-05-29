"""
Rebalance de rangos y precios de los 4 planes.

DECISIÓN ESTRATÉGICA: todos los planes tienen TODAS las funcionalidades del
SaaS. La diferencia entre tiers es solo el rango de alumnos y el precio.
Esto contradice el roadmap anterior (`saas-corem/roadmap-tiers-features`)
que planteaba gating por features — esa decisión queda obsoleta.

El gancho comercial pasa a ser: "Te damos todas las funcionalidades sin
recortes" — la directora no compara "qué features pierdo por pagar el
plan chico", sino que se le entrega el producto completo desde día 1.

Tabla de cambios:

| Slug | Antes (rango/precio público/piso)   | Ahora                          |
|------|--------------------------------------|--------------------------------|
| mini | 1-40 / S/70 / S/70 (fijo)            | 1-30 / S/100 / S/70            |
| plus | 41-70 / S/160 / S/130                | 31-60 / S/170 / S/130          |
| pro  | 71-100 / S/200 / S/170               | 61-90 / S/280 / S/210          |
| max  | 101+ / S/350 / S/300                 | 91+ / S/380 / S/300            |

El precio_acordado de las suscripciones EXISTENTES no se modifica
automáticamente — sigue siendo el valor que se negoció con cada jardín.
Cuando el superadmin quiera realinear, lo hace manualmente desde el admin.
En este momento solo existe el tenant Garabato sin suscripción asignada,
por lo que no hay riesgo de inconsistencia.
"""
from django.db import migrations


NUEVOS = {
    "mini": {"alumnos_min": 1, "alumnos_max": 30, "precio_mensual": "100.00", "precio_minimo": "70.00"},
    "plus": {"alumnos_min": 31, "alumnos_max": 60, "precio_mensual": "170.00", "precio_minimo": "130.00"},
    "pro":  {"alumnos_min": 61, "alumnos_max": 90, "precio_mensual": "280.00", "precio_minimo": "210.00"},
    "max":  {"alumnos_min": 91, "alumnos_max": None, "precio_mensual": "380.00", "precio_minimo": "300.00"},
}

ANTERIORES = {
    "mini": {"alumnos_min": 1, "alumnos_max": 40, "precio_mensual": "70.00", "precio_minimo": "70.00"},
    "plus": {"alumnos_min": 41, "alumnos_max": 70, "precio_mensual": "160.00", "precio_minimo": "130.00"},
    "pro":  {"alumnos_min": 71, "alumnos_max": 100, "precio_mensual": "200.00", "precio_minimo": "170.00"},
    "max":  {"alumnos_min": 101, "alumnos_max": None, "precio_mensual": "350.00", "precio_minimo": "300.00"},
}


def aplicar_nuevos(apps, schema_editor):
    Plan = apps.get_model("platform", "Plan")
    for slug, valores in NUEVOS.items():
        actualizados = Plan.objects.filter(slug=slug).update(**valores)
        if not actualizados:
            # Si el plan no existe (BD nueva o reset), lo creamos.
            Plan.objects.create(
                slug=slug,
                nombre=slug.capitalize(),
                activo=True,
                **valores,
            )


def revertir_a_anteriores(apps, schema_editor):
    Plan = apps.get_model("platform", "Plan")
    for slug, valores in ANTERIORES.items():
        Plan.objects.filter(slug=slug).update(**valores)


class Migration(migrations.Migration):

    dependencies = [
        ("platform", "0004_platformalert"),
    ]

    operations = [
        migrations.RunPython(aplicar_nuevos, revertir_a_anteriores),
    ]
