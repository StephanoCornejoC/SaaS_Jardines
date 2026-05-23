# Migration manual: elimina Payment.qr_code.
# Decisión Etapa A — el flujo padre→jardín NO usa más QR generado por el SaaS.
# El método de pago se mantiene como `Payment.metodo_pago` (CharField choices).
# El QR Yape jardín→COREM (cobros del SaaS) NO se ve afectado: vive en
# apps.platform, no en apps.payments.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0002_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="payment",
            name="qr_code",
        ),
    ]
