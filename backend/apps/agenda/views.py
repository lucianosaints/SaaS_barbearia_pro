from datetime import datetime, time, timedelta
from django.utils import timezone
from rest_framework.throttling import ScopedRateThrottle
from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework import status
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.agenda.models import Servico, Agendamento, BloqueioHorario, FilaEspera
from apps.agenda.serializers import ServicoSerializer, AgendamentoSerializer, BloqueioHorarioSerializer, FilaEsperaSerializer
from apps.accounts.models import Usuario
from django.db.models import Q

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
        user = self.request.user
        
        # Se for rota pública (wizard de agendamento), deve receber o empresa_id via query params
        empresa_id_param = self.request.query_params.get('empresa_id')
        if empresa_id_param:
            return Servico.objects.filter(empresa_id=empresa_id_param, ativo=True)
        
        # Se for rota do painel administrativo (usuário autenticado)
        if user and user.is_authenticated:
            # Se for superusuário, pode ver tudo (opcional)
            if user.is_superuser:
                return Servico.objects.all()
                
            # Para usuários comuns/administradores da empresa, filtra estritamente pelo ID da empresa deles
            empresa_id = getattr(user, 'empresa_id', None)
            if empresa_id:
                return Servico.objects.filter(empresa_id=empresa_id)
                
        # Caso falte autenticação ou parâmetro, bloqueia o retorno de dados globais
        return Servico.objects.none()

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
        
        # Determina o cliente e a empresa
        if user.tipo == 'CLIENTE':
            cliente = user
            profissional = serializer.validated_data.get('profissional')
            empresa = profissional.empresa if profissional else user.empresa
        else:
            cliente = serializer.validated_data.get('cliente', user)
            empresa = user.empresa or serializer.validated_data.get('empresa')

        # Validação de Cliente Bloqueado
        if cliente and getattr(cliente, 'status', 'ATIVO') == 'BLOQUEADO':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Não foi possível processar seu agendamento de forma automática no momento. Fale conosco pelo WhatsApp para garantir sua vaga rapidinho!")

        serializer.save(cliente=cliente, empresa=empresa)

    @action(detail=True, methods=['patch'])
    def cancelar(self, request, pk=None):
        agendamento = self.get_object()
        
        # Garante que só o próprio cliente ou um administrador/profissional da empresa possa cancelar
        if request.user.tipo == 'CLIENTE' and agendamento.cliente != request.user:
            return Response(
                {"error": "Você não tem permissão para cancelar este agendamento."},
                status=status.HTTP_403_FORBIDDEN
            )
        # Se for profissional, só pode cancelar se for da mesma empresa
        if request.user.tipo == 'PROFISSIONAL' and agendamento.empresa != request.user.empresa:
            return Response(
                {"error": "Você não tem permissão para cancelar este agendamento."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Regra de horas limite para cancelamento (apenas restringe o cliente final)
        if request.user.tipo == 'CLIENTE':
            empresa = agendamento.empresa
            limite_horas = getattr(empresa, 'horas_limite_cancelamento', 24)
            from django.utils import timezone
            from datetime import timedelta
            
            if agendamento.data_hora_inicio - timezone.now() < timedelta(hours=limite_horas):
                return Response(
                    {"error": f"O cancelamento automático não é permitido com menos de {limite_horas} horas de antecedência. Entre em contato direto pelo WhatsApp para realizar a alteração."},
                    status=status.HTTP_400_BAD_REQUEST
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
    
    datetime_inicio_dia = timezone.make_aware(datetime.combine(data_selecionada, time.min), tz)
    datetime_fim_dia = timezone.make_aware(datetime.combine(data_selecionada, time.max), tz)

    bloqueios = BloqueioHorario.objects.filter(
        empresa=empresa,
        data_hora_inicio__lt=datetime_fim_dia,
        data_hora_fim__gt=datetime_inicio_dia
    ).filter(
        Q(profissional_id=barbeiro_id) | Q(profissional__isnull=True)
    )
    
    user = request.user
    if user.is_authenticated and not user.is_superuser and user.empresa:
        agendamentos = agendamentos.filter(empresa=user.empresa)

    horarios_disponiveis = []
    horarios_ocupados = []
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

        # 3. Verifica colisão com bloqueios de horário
        if not tem_sobreposicao:
            for bloqueio in bloqueios:
                if slot_inicio < bloqueio.data_hora_fim and slot_fim > bloqueio.data_hora_inicio:
                    tem_sobreposicao = True
                    break

        if not tem_sobreposicao:
            horarios_disponiveis.append(timezone.localtime(slot_inicio).strftime('%H:%M'))
        else:
            horarios_ocupados.append(timezone.localtime(slot_inicio).strftime('%H:%M'))

        loop_time += timedelta(minutes=slot_intervalo_minutos)

    mensagem = None
    if not horarios_disponiveis and bloqueios.exists():
        mensagem = "Este dia está totalmente bloqueado ou indisponível para agendamentos."

    return Response({
        "horarios_disponiveis": horarios_disponiveis,
        "horarios_ocupados": horarios_ocupados,
        "mensagem": mensagem
    })


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
        data_inicio_str = request.query_params.get('data_inicio')
        data_fim_str = request.query_params.get('data_fim')
        
        # Filtra os agendamentos concluídos
        agendamentos = Agendamento.objects.filter(status='CONCLUIDO')
        
        if data_inicio_str and data_fim_str:
            try:
                # Opcional: try/except em datetime.strptime caso a data venha inválida
                agendamentos = agendamentos.filter(
                    data_hora_inicio__date__gte=data_inicio_str,
                    data_hora_inicio__date__lte=data_fim_str
                )
            except Exception:
                pass
        else:
            agendamentos = agendamentos.filter(
                data_hora_inicio__year=hoje.year,
                data_hora_inicio__month=hoje.month
            )
            
        if not user.is_superuser:
            agendamentos = agendamentos.filter(empresa=empresa)

        # Consolidado financeiro
        consolidado = agendamentos.aggregate(
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
            agendamentos_barbeiro = agendamentos.filter(profissional=barbeiro)
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


class ComissoesView(APIView):
    """
    Endpoint isolado para relatório de comissões.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.tipo != 'ADMINISTRADOR' and not user.is_superuser:
            return Response(
                {"error": "Apenas administradores podem visualizar o relatório de comissões."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        empresa = user.empresa
        
        data_inicio_str = request.query_params.get('data_inicio')
        data_fim_str = request.query_params.get('data_fim')
        
        agendamentos = Agendamento.objects.filter(status='CONCLUIDO')
        if not user.is_superuser:
            agendamentos = agendamentos.filter(empresa=empresa)
            
        if data_inicio_str and data_fim_str:
            try:
                agendamentos = agendamentos.filter(
                    data_hora_inicio__date__gte=data_inicio_str,
                    data_hora_inicio__date__lte=data_fim_str
                )
            except Exception:
                pass
                
        profissionais_data = []
        barbeiros = Usuario.objects.filter(tipo='PROFISSIONAL')
        if not user.is_superuser:
            barbeiros = barbeiros.filter(empresa=empresa)
            
        total_faturamento = 0.0
        total_comissoes_geral = 0.0
        total_lucro_liquido = 0.0
            
        for barbeiro in barbeiros:
            agendamentos_barbeiro = agendamentos.filter(profissional=barbeiro)
            faturamento_bruto = agendamentos_barbeiro.aggregate(total=Sum('valor_total'))['total'] or 0.0
            
            percentual = float(barbeiro.comissao_percentual) if hasattr(barbeiro, 'comissao_percentual') else 50.0
            valor_comissao = float(faturamento_bruto) * (percentual / 100.0)
            lucro_liquido = float(faturamento_bruto) - valor_comissao
            
            total_faturamento += float(faturamento_bruto)
            total_comissoes_geral += valor_comissao
            total_lucro_liquido += lucro_liquido
            
            profissionais_data.append({
                "profissional_id": barbeiro.id,
                "nome": barbeiro.get_full_name() or barbeiro.username,
                "comissao_percentual": percentual,
                "faturamento": float(faturamento_bruto),
                "comissao": valor_comissao,
                "lucro_liquido": lucro_liquido
            })
            
        profissionais_data.sort(key=lambda x: x['faturamento'], reverse=True)
            
        return Response({
            "faturamento_bruto": total_faturamento,
            "total_comissoes": total_comissoes_geral,
            "lucro_liquido": total_lucro_liquido,
            "desempenho_profissionais": profissionais_data
        })


class MeuCartaoFidelidadeView(APIView):
    """
    Endpoint para o cliente visualizar o progresso do seu Cartão Fidelidade.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        empresa = user.empresa

        if not empresa:
            return Response(
                {"error": "Usuário não associado a nenhuma empresa."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not empresa.fidelidade_ativo:
            return Response({
                "ativo": False,
                "mensagem": "O programa de fidelidade está inativo no momento."
            })

        from apps.agenda.models import CartaoFidelidade
        cartao, _ = CartaoFidelidade.objects.get_or_create(
            empresa=empresa,
            cliente=user
        )

        return Response({
            "ativo": True,
            "estilo": empresa.fidelidade_estilo,
            "meta": empresa.fidelidade_meta,
            "qtd_selos_atual": cartao.qtd_selos_atual,
            "premios_disponiveis": cartao.premios_disponiveis
        })



class BloqueioHorarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar os bloqueios de horário.
    """
    serializer_class = BloqueioHorarioSerializer
    permission_classes = [IsAuthenticated, IsEmpresaAtiva]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return BloqueioHorario.objects.all()
        if user.tipo in ['ADMINISTRADOR', 'PROFISSIONAL'] and user.empresa:
            return BloqueioHorario.objects.filter(empresa=user.empresa)
        return BloqueioHorario.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.tipo in ['ADMINISTRADOR', 'PROFISSIONAL'] and user.empresa:
            serializer.save(empresa=user.empresa)
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Apenas administradores ou profissionais podem criar bloqueios.")

class FilaEsperaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar a fila de espera.
    Clientes podem entrar na fila publicamente.
    """
    serializer_class = FilaEsperaSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['data_desejada', 'notificado']
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'fila_espera'

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated(), IsEmpresaAtiva()]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.tipo in ['ADMINISTRADOR', 'PROFISSIONAL'] and user.empresa:
            return FilaEspera.objects.filter(empresa=user.empresa)
        return FilaEspera.objects.none()
