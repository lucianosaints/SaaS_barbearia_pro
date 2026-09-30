import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('accounts', '0006_usuario_status_alter_usuario_foto'), ('vitrine', '0001_initial')]
    operations = [
        migrations.CreateModel(name='Pedido', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('cliente_nome', models.CharField(max_length=150)), ('cliente_telefone', models.CharField(max_length=20)),
            ('forma_pagamento', models.CharField(choices=[('PIX','PIX'),('DINHEIRO','Dinheiro'),('DEBITO','Cartão de débito'),('CREDITO','Cartão de crédito')], max_length=10)),
            ('status', models.CharField(choices=[('AGUARDANDO_CONFIRMACAO','Aguardando confirmação'),('CONFIRMADO','Confirmado'),('AGUARDANDO_SINAL','Aguardando sinal'),('SINAL_CONFIRMADO','Sinal confirmado'),('PRONTO','Pronto para retirada'),('CONCLUIDO','Concluído'),('CANCELADO','Cancelado')], default='AGUARDANDO_CONFIRMACAO', max_length=30)),
            ('total', models.DecimalField(decimal_places=2, max_digits=10)), ('sinal_solicitado', models.BooleanField(default=False)), ('sinal_confirmado', models.BooleanField(default=False)),
            ('token_ticket', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)), ('criado_em', models.DateTimeField(auto_now_add=True)), ('atualizado_em', models.DateTimeField(auto_now=True)),
            ('cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pedidos_vitrine', to='accounts.usuario')),
            ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pedidos_vitrine', to='tenants.empresa')),
        ], options={'ordering':['-criado_em']}),
        migrations.CreateModel(name='ItemPedido', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('nome_produto', models.CharField(max_length=150)), ('quantidade', models.PositiveIntegerField()), ('preco_unitario', models.DecimalField(decimal_places=2, max_digits=10)),
            ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='vitrine.pedido')),
            ('produto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='itens_pedido', to='vitrine.produto')),
        ]),
    ]
