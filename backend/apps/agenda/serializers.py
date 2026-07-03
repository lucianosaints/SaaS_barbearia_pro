from rest_framework import serializers
from apps.agenda.models import Servico, Agendamento
from apps.accounts.models import Usuario

class ServicoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Servico.
    """
    class Meta:
        model = Servico
        fields = ['id', 'empresa', 'nome', 'preco', 'duracao_minutos', 'ativo']
        read_only_fields = ['id', 'empresa']


class AgendamentoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Agendamento.
    Gerencia a associação de múltiplos serviços e garante que data_hora_fim seja somente leitura.
    """
    # M2M Field utilizando IDs
    servicos = serializers.PrimaryKeyRelatedField(
        queryset=Servico.objects.all(),
        many=True
    )

    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        required=False
    )

    class Meta:
        model = Agendamento
        fields = [
            'id', 'empresa', 'cliente', 'profissional', 'servicos',
            'data_hora_inicio', 'data_hora_fim', 'status', 'observacoes',
            'valor_total', 'valor_comissao', 'lucro_liquido'
        ]
        read_only_fields = ['id', 'data_hora_fim', 'empresa', 'valor_total', 'valor_comissao', 'lucro_liquido']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra as opções apenas se for um operador/administrador preso a um tenant específico.
        # Clientes finais são usuários globais do SaaS e podem agendar em qualquer barbearia.
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated and not request.user.is_superuser:
            if request.user.tipo != 'CLIENTE':
                empresa = request.user.empresa
                self.fields['servicos'].queryset = Servico.objects.filter(empresa=empresa, ativo=True)
                self.fields['cliente'].queryset = Usuario.objects.filter(empresa=empresa)
                self.fields['profissional'].queryset = Usuario.objects.filter(empresa=empresa)

    def create(self, validated_data):
        servicos = validated_data.pop('servicos', [])
        agendamento = Agendamento.objects.create(**validated_data)
        if servicos:
            # Associa os serviços (isso disparará o sinal m2m_changed e calculará o data_hora_fim)
            agendamento.servicos.set(servicos)
        return agendamento

    def update(self, instance, validated_data):
        servicos = validated_data.pop('servicos', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if servicos is not None:
            # Atualiza os serviços (isso disparará o sinal m2m_changed e recalculará o data_hora_fim)
            instance.servicos.set(servicos)
            
        return instance

    def to_representation(self, instance):
        # Sobrescreve para retornar os detalhes dos serviços em vez de apenas os IDs no GET
        representation = super().to_representation(instance)
        representation['servicos_detalhes'] = ServicoSerializer(instance.servicos.all(), many=True).data
        
        if instance.cliente:
            representation['cliente_nome'] = instance.cliente.get_full_name() or instance.cliente.username
            
        if instance.profissional:
            representation['profissional_nome'] = instance.profissional.get_full_name() or instance.profissional.username
            
        return representation
