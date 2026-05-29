"""
Migración a planes escalonados por cantidad de alumnos.

Antes: 1 fila única en Plan (Plan COREM, S/120/mes flat).
Después: 4 filas activas (Mini, Plus, Pro, Max), una por rango de alumnos.

Greenfield: no hay jardines productivos pagando, por lo que se eliminan los
planes existentes y se repueblan los 4 tiers desde cero. Cualquier
TenantSubscription preexistente quedará apuntando a NULL si el plan fue
borrado, pero en este momento solo existe 1 tenant nominal (de prueba) sin
uso real, por lo que se reasigna a Mini en la misma data migration.

Ver `saas-corem/roadmap-tiers-features` para el roadmap de tiers con
features diferenciadas (postergado a post 5-10 jardines).
"""
from decimal import Decimal

from django.db import migrations, models


PLANES = [
    {
        "slug": "mini",
        "nombre": "Mini",
        "alumnos_min": 1,
        "alumnos_max": 40,
        "precio_mensual": Decimal("70.00"),
        "precio_minimo": Decimal("70.00"),
    },
    {
        "slug": "plus",
        "nombre": "Plus",
        "alumnos_min": 41,
        "alumnos_max": 70,
        "precio_mensual": Decimal("160.00"),
        "precio_minimo": Decimal("130.00"),
    },
    {
        "slug": "pro",
        "nombre": "Pro",
        "alumnos_min": 71,
        "alumnos_max": 100,
        "precio_mensual": Decimal("200.00"),
        "precio_minimo": Decimal("170.00"),
    },
    {
        "slug": "max",
        "nombre": "Max",
        "alumnos_min": 101,
        "alumnos_max": None,
        "precio_mensual": Decimal("350.00"),
        "precio_minimo": Decimal("300.00"),
    },
]


def poblar_planes(apps, schema_editor):
    Plan = apps.get_model("platform", "Plan")
    TenantSubscription = apps.get_model("platform", "TenantSubscription")

    # Greenfield: limpiar lo anterior. Desvincular suscripciones (set NULL en
    # plan FK es PROTECT, así que primero reasignamos a Mini después de crear).
    plan_ids_a_borrar = list(Plan.objects.values_list("id", flat=True))

    # Crear los 4 tiers nuevos
    creados = {}
    for definicion in PLANES:
        creados[definicion["slug"]] = Plan.objects.create(activo=True, **definicion)

    # Reasignar TODAS las TenantSubscription existentes al plan Mini
    # (en greenfield solo debería existir el tenant de prueba). El precio
    # acordado se mantiene tal cual estaba (no se sobreescribe).
    mini = creados["mini"]
    TenantSubscription.objects.filter(plan_id__in=plan_ids_a_borrar).update(plan=mini)

    # Recién ahora podemos borrar los planes viejos
    Plan.objects.filter(id__in=plan_ids_a_borrar).delete()


def revertir_planes(apps, schema_editor):
    Plan = apps.get_model("platform", "Plan")
    TenantSubscription = apps.get_model("platform", "TenantSubscription")

    # Recrear el Plan único anterior
    plan_legacy = Plan.objects.create(
        nombre="Plan COREM",
        slug="legacy",
        alumnos_min=0,
        alumnos_max=None,
        precio_mensual=Decimal("120.00"),
        precio_minimo=Decimal("120.00"),
        activo=True,
    )

    # Reasignar suscripciones al plan legacy
    nuevos_slugs = [p["slug"] for p in PLANES]
    TenantSubscription.objects.filter(plan__slug__in=nuevos_slugs).update(
        plan=plan_legacy
    )

    # Borrar los 4 tiers nuevos
    Plan.objects.filter(slug__in=nuevos_slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("platform", "0002_alter_platformcost_options_platformcost_company_and_more"),
    ]

    operations = [
        # 1. Add fields nuevos con nullable para no romper filas existentes
        migrations.AddField(
            model_name="plan",
            name="slug",
            field=models.SlugField(
                max_length=20,
                null=True,
                unique=True,
                help_text="Identificador único en código (mini, plus, pro, max).",
            ),
        ),
        migrations.AddField(
            model_name="plan",
            name="alumnos_min",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="Cantidad mínima de alumnos activos para que aplique este plan.",
            ),
        ),
        migrations.AddField(
            model_name="plan",
            name="alumnos_max",
            field=models.PositiveSmallIntegerField(
                null=True,
                blank=True,
                help_text="Cantidad máxima de alumnos activos. Dejar vacío significa sin límite.",
            ),
        ),
        migrations.AddField(
            model_name="plan",
            name="precio_minimo",
            field=models.DecimalField(
                max_digits=8,
                decimal_places=2,
                null=True,
                help_text="Piso negociable. Soporte interno NO debe cerrar ventas por debajo de este monto.",
            ),
        ),
        # 2. Quitar el default del nombre y de precio_mensual (los 4 tiers
        # nuevos deben definir su propio nombre y precio explícitamente)
        migrations.AlterField(
            model_name="plan",
            name="nombre",
            field=models.CharField(max_length=80),
        ),
        migrations.AlterField(
            model_name="plan",
            name="precio_mensual",
            field=models.DecimalField(
                max_digits=8,
                decimal_places=2,
                help_text="Precio público del plan en soles. Es el precio que se muestra en marketing.",
            ),
        ),
        migrations.AlterField(
            model_name="plan",
            name="activo",
            field=models.BooleanField(
                default=True,
                help_text=(
                    "Si está desactivado, no se asigna a jardines nuevos. "
                    "Los jardines existentes lo conservan."
                ),
            ),
        ),
        # 3. Borrar planes viejos, crear 4 tiers, reasignar suscripciones
        migrations.RunPython(poblar_planes, revertir_planes),
        # 4. Ahora que los datos están cargados, hacer slug y precio_minimo
        # NOT NULL definitivamente
        migrations.AlterField(
            model_name="plan",
            name="slug",
            field=models.SlugField(
                max_length=20,
                unique=True,
                help_text="Identificador único en código (mini, plus, pro, max).",
            ),
        ),
        migrations.AlterField(
            model_name="plan",
            name="precio_minimo",
            field=models.DecimalField(
                max_digits=8,
                decimal_places=2,
                help_text="Piso negociable. Soporte interno NO debe cerrar ventas por debajo de este monto.",
            ),
        ),
        # 5. Cambiar opciones de Meta (verbose_name_plural y ordering)
        migrations.AlterModelOptions(
            name="plan",
            options={
                "ordering": ("alumnos_min",),
                "verbose_name": "Plan",
                "verbose_name_plural": "Planes",
            },
        ),
    ]
