# Migration manual: agrega Teacher.tipo (TITULAR/AUXILIAR).
# Necesario para soportar profesores auxiliares en las aulas. Los registros
# existentes quedan como TITULAR (default) para no romper relaciones de
# Classroom.profesor_titular ya creadas.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("teachers", "0003_remove_teacher_activo"),
    ]

    operations = [
        migrations.AddField(
            model_name="teacher",
            name="tipo",
            field=models.CharField(
                choices=[("TITULAR", "Titular"), ("AUXILIAR", "Auxiliar")],
                default="TITULAR",
                help_text=(
                    "Titular: a cargo del aula. Auxiliar: apoya al titular. "
                    "Solo los Titulares pueden asignarse como profesor_titular "
                    "del aula; solo los Auxiliares como profesor_auxiliar."
                ),
                max_length=10,
                verbose_name="Tipo de profesor",
            ),
        ),
    ]
