from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [('vitrine', '0002_pedido_itempedido')]
    operations = [
        migrations.AddField(
            model_name='pedido',
            name='token_ticket_criado_em',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
    ]
