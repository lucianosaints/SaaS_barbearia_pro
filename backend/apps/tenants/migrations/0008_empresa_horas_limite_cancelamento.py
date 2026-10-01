"""Compatibilidade com o historico de migracoes aplicado em producao.

O campo horas_limite_cancelamento ja faz parte da migracao 0007 no codigo
consolidado. Esta migracao permanece vazia para conservar o no registrado no
banco de producao sem tentar criar a coluna uma segunda vez em bancos novos.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0007_empresa_beneficiario_pix_empresa_chave_pix_and_more'),
    ]

    operations = []
