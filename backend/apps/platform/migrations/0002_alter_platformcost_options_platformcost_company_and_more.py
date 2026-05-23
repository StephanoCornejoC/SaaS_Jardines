# Editado tras la eliminación de la app `empresas` (rebrand a Kiddo).
# Original: agregaba PlatformCost.company FK a empresas.Company.
# Versión actual: mantiene solo los cambios que NO dependen de empresas.
# Refleja el estado final deseado de la tabla `platform_platformcost`.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('platform', '0001_initial'),
        ('tenants', '0002_remove_tenant_plan'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='platformcost',
            options={
                'ordering': ('-fecha',),
                'verbose_name': 'Costo del SaaS',
                'verbose_name_plural': 'Costos del SaaS',
            },
        ),
        migrations.AlterField(
            model_name='platformcost',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "Si el gasto aplica a un jardín específico, asignarlo. "
                    "Si es un gasto genérico del SaaS (Railway, dominio, etc.), "
                    "dejarlo vacío."
                ),
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='costs',
                to='tenants.tenant',
            ),
        ),
    ]
