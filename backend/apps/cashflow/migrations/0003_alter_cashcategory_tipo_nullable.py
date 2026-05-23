# Migration manual: CashCategory.tipo pasa a ser nullable.
#
# Motivo: la categoría "Otros" debe servir tanto para INGRESOS como para
# EGRESOS (gastos varios + ingresos varios). Si tipo es null, la categoría
# es bidireccional — aparece en ambos selectores y NO dispara la validación
# de "tipo debe coincidir" de CashTransaction.clean().

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cashflow", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cashcategory",
            name="tipo",
            field=models.CharField(
                blank=True,
                choices=[("INGRESO", "Ingreso"), ("EGRESO", "Egreso")],
                help_text=(
                    "Si se especifica, la categoría solo aparece en transacciones "
                    "de ese tipo (INGRESO o EGRESO). Si se deja vacío, la "
                    "categoría es bidireccional — sirve para INGRESOS y EGRESOS "
                    "(ej. 'Otros')."
                ),
                max_length=7,
                null=True,
                verbose_name="Tipo",
            ),
        ),
    ]
