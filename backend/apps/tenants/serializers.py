from rest_framework import serializers
from apps.tenants.models import Empresa


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ['id', 'nome', 'slug', 'cnpj', 'data_criacao', 'ativo', 'hora_abertura',
                  'hora_fechamento', 'intervalo_almoco_inicio', 'intervalo_almoco_fim']
        read_only_fields = ['id', 'data_criacao']

    def validate(self, attrs):
        from datetime import time
        def value(key, default=None):
            return attrs.get(key, getattr(self.instance, key, default))
        opening, closing = value('hora_abertura', time(9)), value('hora_fechamento', time(19))
        start, end = value('intervalo_almoco_inicio'), value('intervalo_almoco_fim')
        if opening >= closing:
            raise serializers.ValidationError('O fechamento deve ser posterior à abertura.')
        if (start is None) != (end is None):
            raise serializers.ValidationError('Informe início e fim do almoço.')
        if start is not None and not opening <= start < end <= closing:
            raise serializers.ValidationError('O almoço deve estar dentro do expediente.')
        return attrs
