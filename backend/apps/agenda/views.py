from datetime import datetime, time, timedelta
from django.utils import timezone
from django.db.models import Sum
from apps.accounts.permissions import PublicReadAdminWrite
from apps.agenda.rules import available_slots
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework import status
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.agenda.models import Servico, Agendamento
from apps.agenda.serializers import ServicoSerializer, AgendamentoSerializer
from apps.accounts.models import Usuario

from rest_framework.permissions import IsAuthenticated, AllowAny

class ServicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para listar, criar e gerenciar Serviços.
    Garante isolamento multi-tenant e visualização pública.
    """
    serializer_class = ServicoSerializer
    permission_classes = [PublicReadAdminWrite]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_queryset(self):
        # Filtro de listagem pública por empresa para o Wizard
        empresa_id = self.request.query_params.get('empresa_id')
        if empresa_id and self.request.method in SAFE_METHODS:
            if not empresa_id.isdigit():
                raise ValidationError({'empresa_id': 'Identificador inválido.'})
            return Servico.objects.filter(empresa_id=empresa_id, ativo=True, empresa__ativo=True)

        user = self.request.user
        if user.is_authenticated and user.tipo != 'CLIENTE':
            if user.is_superuser:
                return Servico.objects.all()
            if user.empresa:
                return Servico.objects.filter(empresa=user.empresa)
            return Servico.objects.none()
            
        # Se for consulta anônima ou cliente final logado, lista todos os serviços ativos no MVP
        return Servico.objects.filter(ativo=True, empresa__ativo=True)

    def perform_create(self, serializer):
        # Associa o serviço automaticamente à empresa do usuário criador
        if not self.request.user.is_superuser and self.request.user.empresa:
            serializer.save(empresa=self.request.user.empresa)
        else:
            serializer.save()


class AgendamentoFilter(filters.FilterSet):
    """
    Filtro personalizado para Agendamento.
    Mapeia a busca por 'barbeiro' para o campo 'profissional'.
    Trata a busca por 'data_hora_inicio' como busca por data pura.
    """
    barbeiro = filters.ModelChoiceFilter(
        queryset=Usuario.objects.all(),
        field_name='profissional',
        label="Profissional / Barbeiro"
    )
    data_hora_inicio = filters.DateFilter(
        field_name='data_hora_inicio',
        lookup_expr='date',
        label="Data do Agendamento"
    )

    class Meta:
        model = Agendamento
        fields = ['status', 'barbeiro', 'data_hora_inicio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra os profissionais listados no filtro de acordo com a empresa do usuário logado (exceto clientes finais)
        request = kwargs.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated and not request.user.is_superuser:
            if request.user.tipo != 'CLIENTE':
                empresa = request.user.empresa
                self.filters['barbeiro'].queryset = Usuario.objects.filter(empresa=empresa)
            else:
                self.filters['barbeiro'].queryset = Usuario.objects.filter(tipo='PROFISSIONAL')


class AgendamentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Agendamentos.
    Filtra os agendamentos pela empresa do usuário autenticado.
    Se for um cliente final, retorna apenas os seus próprios agendamentos.
    """
    serializer_class = AgendamentoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = AgendamentoFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Agendamento.objects.select_related('cliente', 'profissional', 'empresa').prefetch_related('servicos').all()
        
        # Cliente final: OBRIGATORIAMENTE retorna apenas seus próprios agendamentos
        if user.tipo == 'CLIENTE':
            return Agendamento.objects.filter(cliente=user)
            
        # Profissionais e Administradores: veem todos os agendamentos da empresa
        if user.tipo in ['ADMINISTRADOR', 'PROFISSIONAL'] and user.empresa:
            return Agendamento.objects.filter(empresa=user.empresa)
            
        return Agendamento.objects.none()

    @action(detail=True, methods=['patch'])
    def cancelar(self, request, pk=None):
        serializer = self.get_serializer(self.get_object(), data={'status': 'CANCELADO'}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Agendamento cancelado com sucesso."})


@api_view(['GET'])
@permission_classes([AllowAny])
def obter_disponibilidade(request):
    try:
        day = datetime.strptime(request.query_params.get('data', ''), '%Y-%m-%d').date()
        profissional_id = int(request.query_params.get('barbeiro_id', ''))
        ids = [int(value) for value in request.query_params.get('servicos', '').split(',')]
    except (ValueError, TypeError):
        raise ValidationError('Informe data (YYYY-MM-DD), barbeiro_id e serviços válidos.')
    profissional = Usuario.objects.select_related('empresa').filter(pk=profissional_id).first()
    services = list(Servico.objects.filter(pk__in=ids))
    if len(ids) != len(services):
        raise ValidationError({'servicos': 'Serviços inválidos ou repetidos.'})
    return Response({'horarios_disponiveis': available_slots(profissional, services, day)})


class FinancasDashboardView(APIView):
    """
    APIView para consolidar os dados financeiros do mês atual para o tenant.
    Apenas administradores do tenant (ou superuser) podem visualizar.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Apenas administradores do tenant (ou superuser)
        if user.tipo != 'ADMINISTRADOR' and not user.is_superuser:
            return Response(
                {"error": "Acesso negado. Apenas administradores podem visualizar o dashboard financeiro."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        empresa = user.empresa
        if not empresa and not user.is_superuser:
            return Response(
                {"error": "Usuário não associado a uma empresa."},
                status=status.HTTP_400_BAD_REQUEST
            )

        hoje = timezone.localdate()
        inicio_mes = hoje.replace(day=1)
        
        # Filtra os agendamentos concluídos do mês atual para a empresa
        agendamentos_mes = Agendamento.objects.filter(
            status='CONCLUIDO',
            data_hora_inicio__date__gte=inicio_mes,
            data_hora_inicio__date__lte=hoje
        )
        if not user.is_superuser:
            agendamentos_mes = agendamentos_mes.filter(empresa=empresa)

        # Consolidado financeiro
        consolidado = agendamentos_mes.aggregate(
            faturamento_bruto=Sum('valor_total'),
            total_comissoes=Sum('valor_comissao'),
            lucro_liquido=Sum('lucro_liquido')
        )
        
        faturamento_bruto = consolidado['faturamento_bruto'] or 0.0
        total_comissoes = consolidado['total_comissoes'] or 0.0
        lucro_liquido = consolidado['lucro_liquido'] or 0.0

        # Desempenho dos profissionais
        desempenho_profissionais = []
        barbeiros = Usuario.objects.filter(tipo='PROFISSIONAL')
        if not user.is_superuser:
            barbeiros = barbeiros.filter(empresa=empresa)
            
        for barbeiro in barbeiros:
            agendamentos_barbeiro = agendamentos_mes.filter(profissional=barbeiro)
            consolidado_barbeiro = agendamentos_barbeiro.aggregate(
                faturamento=Sum('valor_total'),
                comissao=Sum('valor_comissao')
            )
            desempenho_profissionais.append({
                "barbeiro_id": barbeiro.id,
                "nome": barbeiro.get_full_name() or barbeiro.username,
                "faturamento": float(consolidado_barbeiro['faturamento'] or 0.0),
                "comissao": float(consolidado_barbeiro['comissao'] or 0.0)
            })

        # Ordena desempenho pelo faturamento gerado (descendente)
        desempenho_profissionais.sort(key=lambda x: x['faturamento'], reverse=True)

        return Response({
            "faturamento_bruto": float(faturamento_bruto),
            "total_comissoes": float(total_comissoes),
            "lucro_liquido": float(lucro_liquido),
            "desempenho_profissionais": desempenho_profissionais
        })
