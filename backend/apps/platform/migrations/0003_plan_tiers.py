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

    # FK PROTECT entre TenantSubscription.plan y Plan deja constraint checks
    # diferidos en la transacción de migración. Si no los drenamos acá, el
    # siguiente AlterField sobre platform_plan falla con
    # `psycopg2.errors.ObjectInUse: cannot ALTER TABLE ... because it has
    # pending trigger events`. SET CONSTRAINTS ALL IMMEDIATE evalúa los
    # checks ya mismo y los limpia, dejando la tabla lista para ALTER.
    schema_editor.execute("SET CONSTRAINTS ALL IMMEDIATE;")


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

    # atomic=False hace que cada operation se commitee independientemente
    # en lugar de envolver TODA la migración en una sola transacción. Es
    # imprescindible acá porque:
    #
    # 1. Si la migración falla a mitad con atomic=True, el rollback DESHACE
    #    nuestro cleanup defensivo (RunSQL DROP IF EXISTS) y deja los
    #    residuos del intento anterior, generando un loop infinito de
    #    `relation ... already exists` en re-deploys.
    #
    # 2. Con atomic=False el DROP IF EXISTS persiste aunque el resto falle,
    #    permitiendo que el próximo intento arranque desde una BD limpia.
    #
    # Trade-off: si una operation falla, las anteriores ya committearon.
    # En este caso es aceptable porque las operations son todas idempotentes
    # (DROP IF EXISTS, AddField sin unique, RunPython con borrado previo).
    atomic = False

    dependencies = [
        ("platform", "0002_alter_platformcost_options_platformcost_company_and_more"),
    ]

    # OJO con el orden de operations en Postgres + django-tenants:
    # si se hace AddField(unique=True) seguido de cualquier AlterField sobre
    # la misma tabla, Postgres queda con "pending trigger events" del UNIQUE
    # INDEX recién creado y rechaza el ALTER TABLE con
    # `psycopg2.errors.ObjectInUse: cannot ALTER TABLE ... because it has
    # pending trigger events`.
    #
    # Solución: el slug se agrega primero como NULL y SIN unique, la RunPython
    # puebla los valores, y recién al final un AlterField lo marca como
    # unique=True NOT NULL. Lo mismo para precio_minimo (NOT NULL al final).

    operations = [
        # 0. Limpieza defensiva de residuos de intentos previos.
        # IMPORTANTE: el `_uniq` NO es solo un índice — es el índice
        # subyacente de una UNIQUE CONSTRAINT. Postgres rechaza
        # `DROP INDEX platform_plan_slug_*_uniq` con
        # `DependentObjectsStillExist: ... requires it`. Hay que dropear la
        # CONSTRAINT primero (lo cual cae el índice asociado en cascada).
        # El orden importa: constraint primero, después los índices puros.
        migrations.RunSQL(
            sql=[
                # Constraints (incluyen su índice subyacente automáticamente)
                "ALTER TABLE platform_plan DROP CONSTRAINT IF EXISTS platform_plan_slug_d4ad4e10_uniq;",
                "ALTER TABLE platform_plan DROP CONSTRAINT IF EXISTS platform_plan_slug_key;",
                # Índices estándar (db_index implícito + varchar_pattern_ops)
                "DROP INDEX IF EXISTS platform_plan_slug_d4ad4e10;",
                "DROP INDEX IF EXISTS platform_plan_slug_d4ad4e10_like;",
                # Columnas que esta migración agrega; si quedaron de un
                # intento previo las recreamos limpias en los AddField
                # siguientes. El CASCADE en DROP COLUMN se aplica solo a
                # índices/constraints de esa columna específicamente.
                "ALTER TABLE platform_plan DROP COLUMN IF EXISTS slug CASCADE;",
                "ALTER TABLE platform_plan DROP COLUMN IF EXISTS alumnos_min;",
                "ALTER TABLE platform_plan DROP COLUMN IF EXISTS alumnos_max;",
                "ALTER TABLE platform_plan DROP COLUMN IF EXISTS precio_minimo;",
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 1. Add fields nuevos. IMPORTANTE: slug se agrega con db_index=False
        # explícito. SlugField default es db_index=True que crea el índice
        # secundario + el `_like` desde el ADD COLUMN. Eso entra en conflicto
        # con el AlterField posterior que marca unique=True (que también
        # quiere crear `_like`). Al diferir TODA la creación de índices al
        # AlterField final del slug, no hay colisión.
        migrations.AddField(
            model_name="plan",
            name="slug",
            field=models.SlugField(
                max_length=20,
                null=True,
                db_index=False,
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
        # 2. Borrar planes viejos, crear 4 tiers con slugs únicos, reasignar
        # suscripciones existentes.
        migrations.RunPython(poblar_planes, revertir_planes),
        # 3. Ahora que los datos están cargados y los slugs son únicos,
        # marcamos slug como unique=True NOT NULL y precio_minimo como NOT NULL.
        # Estos AlterField van DESPUÉS del RunPython y no causan conflicto
        # con pending events porque el data fill ya completó.
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
        # 4. Cambios cosmeticos (quita defaults, agrega help_text) — al final,
        # cuando ya no hay constraints pendientes que afecten ALTER TABLE.
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
