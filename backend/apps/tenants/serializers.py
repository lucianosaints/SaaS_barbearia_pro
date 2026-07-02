from rest_framework import serializers
from apps.tenants.models import Empresa

class EmpresaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo de Empresa (Tenant).
    """
    class Meta:
        model = Empresa
        fields = ['id', 'nome', 'slug', 'cnpj', 'data_criacao', 'ativo']
        read_only_fields = ['id', 'data_criacao']
