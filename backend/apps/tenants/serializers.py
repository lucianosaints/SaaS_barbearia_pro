from rest_framework import serializers
from apps.tenants.models import Empresa

class EmpresaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo de Empresa (Tenant).
    """
    dias_restantes = serializers.SerializerMethodField()

    class Meta:
        model = Empresa
        fields = ['id', 'nome', 'slug', 'cnpj', 'data_criacao', 'ativo',
                  'hora_abertura', 'hora_fechamento', 'intervalo_almoco_inicio', 'intervalo_almoco_fim',
                  'em_trial', 'assinatura_ativa', 'data_fim_trial', 'data_vencimento_assinatura', 'dias_restantes',
                  'dias_retorno_lembrete', 'fidelidade_ativo', 'fidelidade_meta', 'fidelidade_estilo',
                  'exigir_sinal', 'chave_pix', 'beneficiario_pix', 'horas_limite_cancelamento']
        read_only_fields = ['id', 'data_criacao', 'em_trial', 'assinatura_ativa', 'data_fim_trial', 'data_vencimento_assinatura']

    def get_dias_restantes(self, obj):
        import datetime
        if obj.data_vencimento_assinatura:
            delta = obj.data_vencimento_assinatura - datetime.date.today()
            return delta.days
        elif obj.em_trial and obj.data_fim_trial:
            delta = obj.data_fim_trial - datetime.date.today()
            return delta.days
        return 0


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
