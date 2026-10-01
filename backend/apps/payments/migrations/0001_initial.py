import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [('tenants', '0008_empresa_data_vencimento_assinatura')]
    operations = [
        migrations.CreateModel(
            name='CobrancaAssinatura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_reference', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('meses', models.PositiveSmallIntegerField()),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10)),
                ('moeda', models.CharField(default='BRL', max_length=3)),
                ('mercado_pago_payment_id', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('status', models.CharField(choices=[('PENDENTE', 'Pendente'), ('APROVADA', 'Aprovada'), ('REJEITADA', 'Rejeitada'), ('ERRO', 'Erro')], default='PENDENTE', max_length=10)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('processada_em', models.DateTimeField(blank=True, null=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cobrancas_assinatura', to='tenants.empresa')),
            ],
            options={'ordering': ['-criada_em']},
        ),
    ]
