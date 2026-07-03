from datetime import datetime, time, timedelta
from django.utils import timezone
from django.db.models import Sum
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

from apps.accounts.permissions import IsAdminUserOrReadOnly
from apps.tenants.permissions import IsEmpresaAtiva

class ServicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para listar, criar e gerenciar Serviços.
    Garante isolamento multi-tenant e visualização pública.
    """
    serializer_class = ServicoSerializer
    permission_classes = [IsAdminUserOrReadOnly, IsEmpresaAtiva]

    def get_queryset(self):
        # Filtro de listagem pública por empresa para o Wizard
        empresa_id = self.request.query_params.get('empresa_id')
        if empresa_id:
            return Servico.objects.filter(empresa_id=empresa_id, ativo=True)

        user = self.request.user
        if user.is_authenticated and user.tipo != 'CLIENTE':
            if user.is_superuser:
                return Servico.objects.all()
            if user.empresa:
                return Servico.objects.filter(empresa=user.empresa)
            return Servico.objects.none()
            
        # Se for consulta anônima ou cliente final logado, lista todos os serviços ativos no MVP
        return Servico.objects.filter(ativo=True)

    def perform_create(self, serializer):
        user = self.request.user
        empresa_id = self.request.data.get('empresa')
        if not empresa_id and user.empresa:
            serializer.save(empresa=user.empresa)
        elif empresa_id:
            serializer.save()
        else:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"empresa": "Não foi possível associar o serviço a uma empresa. Verifique se seu usuário está vinculado a uma barbearia."})


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
    permission_classes = [IsAuthenticated, IsEmpresaAtiva]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = AgendamentoFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Agendamento.objects.all()
        
        # Cliente final: OBRIGATORIAMENTE retorna apenas seus próprios agendamentos
        if user.tipo == 'CLIENTE':
            return Agendamento.objects.filter(cliente=user)
            
        # Profissionais: veem apenas os agendamentos em que são o barbeiro
        if user.tipo == 'PROFISSIONAL' and user.empresa:
            return Agendamento.objects.filter(empresa=user.empresa, profissional=user)
            
        # Administradores: veem todos os agendamentos da empresa
        if user.tipo == 'ADMINISTRADOR' and user.empresa:
            return Agendamento.objects.filter(empresa=user.empresa)
            
        return Agendamento.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        # Se for cliente, associa-o automaticamente ao agendamento
        if user.tipo == 'CLIENTE':
            profissional = serializer.validated_data.get('profissional')
            empresa = profissional.empresa if profissional else user.empresa
            serializer.save(cliente=user, empresa=empresa)
        else:
            # Admin/Profissional: se cliente não for informado (ex: usando o wizard do cliente),
            # assume que ele está agendando para si mesmo.
            cliente = serializer.validated_data.get('cliente', user)
            empresa = user.empresa or serializer.validated_data.get('empresa')
            serializer.save(cliente=cliente, empresa=empresa)

    @action(detail=True, methods=['patch'])
    def cancelar(self, request, pk=None):
        agendamento = self.get_object()
        
        # Garante que só o próprio cliente ou um administrador possa cancelar
        if request.user.tipo == 'CLIENTE' and agendamento.cliente != request.user:
            return Response(
                {"error": "Você não tem permissão para cancelar este agendamento."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        if agendamento.status == 'CANCELADO':
            return Response(
                {"error": "Este agendamento já está cancelado."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        agendamento.status = 'CANCELADO'
        agendamento.save()
        return Response({"message": "Agendamento cancelado com sucesso."})


@api_view(['GET'])
@permission_classes([AllowAny])
def obter_disponibilidade(request):
    """
    Calcula e retorna a lista de horários livres de um profissional (barbeiro)
    para uma data e serviços selecionados. Evita qualquer sobreposição.
    """
    data_str = request.query_params.get('data')
    barbeiro_id = request.query_params.get('barbeiro_id')
    servicos_str = request.query_params.get('servicos')

    if not all([data_str, barbeiro_id, servicos_str]):
        return Response(
            {"error": "Os parâmetros 'data', 'barbeiro_id' e 'servicos' são obrigatórios."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        data_selecionada = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return Response(
            {"error": "Formato de data inválido. Use YYYY-MM-DD."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        servico_ids = [int(id_str.strip()) for id_str in servicos_str.split(',') if id_str.strip()]
    except ValueError:
        return Response(
            {"error": "Formato do parâmetro 'servicos' inválido. Use IDs separados por vírgula."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not servico_ids:
        return Response(
            {"error": "Pelo menos um serviço deve ser selecionado."},
            status=status.HTTP_400_BAD_REQUEST
        )

    barbeiro = Usuario.objects.filter(id=barbeiro_id).first()
    if not barbeiro or not barbeiro.empresa:
        return Response(
            {"error": "Profissional inválido ou sem barbearia (empresa) vinculada."},
            status=status.HTTP_404_NOT_FOUND
        )

    empresa = barbeiro.empresa

    # Filtra os serviços pela empresa do barbeiro selecionado (não do usuário logado)
    servicos_qs = Servico.objects.filter(id__in=servico_ids, ativo=True, empresa=empresa)

    if servicos_qs.count() != len(set(servico_ids)):
        return Response(
            {"error": "Um ou mais serviços informados são inválidos ou não pertencem à empresa."},
            status=status.HTTP_404_NOT_FOUND
        )

    duracao_total = sum(s.duracao_minutos for s in servicos_qs)

    tz = timezone.get_current_timezone()
    
    # Parâmetros de expediente e almoço dinâmicos da empresa
    hora_abertura = empresa.hora_abertura
    hora_fechamento = empresa.hora_fechamento
    almoco_inicio = empresa.intervalo_almoco_inicio
    almoco_fim = empresa.intervalo_almoco_fim
    slot_intervalo_minutos = 30

    agendamentos = Agendamento.objects.filter(
        profissional_id=barbeiro_id,
        data_hora_inicio__date=data_selecionada,
        status__in=['PENDENTE', 'CONFIRMADO', 'CONCLUIDO']
    )
    user = request.user
    if user.is_authenticated and not user.is_superuser and user.empresa:
        agendamentos = agendamentos.filter(empresa=user.empresa)

    horarios_disponiveis = []
    agora = timezone.localtime(timezone.now())

    datetime_inicio_exp = timezone.make_aware(datetime.combine(data_selecionada, hora_abertura), tz)
    datetime_fim_exp = timezone.make_aware(datetime.combine(data_selecionada, hora_fechamento), tz)

    # Converte intervalo de almoço para datetimes cientes de fuso horário se configurados
    datetime_inicio_almoco = None
    datetime_fim_almoco = None
    if almoco_inicio and almoco_fim:
        datetime_inicio_almoco = timezone.make_aware(datetime.combine(data_selecionada, almoco_inicio), tz)
        datetime_fim_almoco = timezone.make_aware(datetime.combine(data_selecionada, almoco_fim), tz)

    loop_time = datetime_inicio_exp
    while loop_time + timedelta(minutes=duracao_total) <= datetime_fim_exp:
        slot_inicio = loop_time
        slot_fim = loop_time + timedelta(minutes=duracao_total)

        # Se a data for hoje, pula os horários passados
        if data_selecionada == agora.date() and slot_inicio < agora:
            loop_time += timedelta(minutes=slot_intervalo_minutos)
            continue

        tem_sobreposicao = False

        # 1. Verifica colisão com o intervalo de almoço configurado da empresa
        if datetime_inicio_almoco and datetime_fim_almoco:
            if slot_inicio < datetime_fim_almoco and slot_fim > datetime_inicio_almoco:
                tem_sobreposicao = True

        # 2. Verifica colisão com os agendamentos já reservados no banco
        if not tem_sobreposicao:
            for agendamento in agendamentos:
                if slot_inicio < agendamento.data_hora_fim and slot_fim > agendamento.data_hora_inicio:
                    tem_sobreposicao = True
                    break

        if not tem_sobreposicao:
            horarios_disponiveis.append(timezone.localtime(slot_inicio).strftime('%H:%M'))

        loop_time += timedelta(minutes=slot_intervalo_minutos)

    return Response({"horarios_disponiveis": horarios_disponiveis})


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
