from rest_framework import serializers
from apps.tenants.models import Empresa

class EmpresaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo de Empresa (Tenant).
    """
    class Meta:
        model = Empresa
        fields = ['id', 'nome', 'slug', 'cnpj', 'data_criacao', 'ativo',
                  'hora_abertura', 'hora_fechamento', 'intervalo_almoco_inicio', 'intervalo_almoco_fim',
                  'em_trial', 'assinatura_ativa', 'data_fim_trial']
        read_only_fields = ['id', 'data_criacao', 'em_trial', 'assinatura_ativa', 'data_fim_trial']
