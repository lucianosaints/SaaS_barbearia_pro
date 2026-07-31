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
