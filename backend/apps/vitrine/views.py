from decimal import Decimal
import hashlib
import re
from datetime import datetime, time

from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, SAFE_METHODS
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import PublicReadAdminWrite
from .models import ItemPedido, Pedido, Produto
from .serializers import PedidoPublicoSerializer, PedidoSerializer, ProdutoSerializer
from .throttles import PedidoCreateThrottle
from .notifications import notificar_novo_pedido, notificar_status_pedido


class ProdutoPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = 'page_size'
    max_page_size = 24


class PedidoPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 30


def inicio_periodo(periodo):
    agora = timezone.localtime()
    if periodo == 'diario':
        data = agora.date()
    elif periodo == 'mensal':
        data = agora.date().replace(day=1)
    elif periodo == 'anual':
        data = agora.date().replace(month=1, day=1)
    else:
        return None
    return timezone.make_aware(datetime.combine(data, time.min), timezone.get_current_timezone())


class ProdutoViewSet(ModelViewSet):
    serializer_class = ProdutoSerializer
    permission_classes = [PublicReadAdminWrite]
    http_method_names = ['get', 'post', 'patch', 'put', 'head', 'options']
    pagination_class = ProdutoPagination

    def get_queryset(self):
        user = self.request.user
        empresa_id = self.request.query_params.get('empresa_id')
        empresa_slug = self.request.query_params.get('empresa_slug')

        if user.is_authenticated and user.is_superuser and not (empresa_id or empresa_slug):
            return Produto.objects.select_related('empresa').all()
        if user.is_authenticated and getattr(user, 'empresa_id', None) and not (empresa_id or empresa_slug):
            return Produto.objects.filter(empresa=user.empresa)

        if not empresa_id and not empresa_slug:
            raise ValidationError({'empresa': 'Informe o salão para consultar a vitrine.'})
        if empresa_id and not empresa_id.isdigit():
            raise ValidationError({'empresa_id': 'Identificador inválido.'})

        filtros = {'empresa__ativo': True, 'disponivel': True}
        if empresa_id:
            filtros['empresa_id'] = empresa_id
        else:
            filtros['empresa__slug__iexact'] = empresa_slug
        return Produto.objects.filter(**filtros)

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            serializer.save(empresa=self.request.user.empresa)
        else:
            serializer.save()

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]


class PedidoViewSet(ModelViewSet):
    serializer_class = PedidoSerializer
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    pagination_class = PedidoPagination

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Pedido.objects.none()
        if user.is_superuser:
            queryset = Pedido.objects.select_related('empresa').prefetch_related('itens')
        elif user.tipo != 'ADMINISTRADOR' or not user.empresa_id:
            raise PermissionDenied('Apenas o gestor pode consultar pedidos.')
        else:
            queryset = Pedido.objects.filter(empresa=user.empresa).select_related('empresa').prefetch_related('itens')
        periodo = self.request.query_params.get('periodo', 'todos')
        if periodo not in {'todos', 'diario', 'mensal', 'anual'}:
            raise ValidationError({'periodo': 'Use diario, mensal, anual ou todos.'})
        inicio = inicio_periodo(periodo)
        return queryset.filter(criado_em__gte=inicio) if inicio and self.action != 'dashboard' else queryset

    def get_permissions(self):
        return [AllowAny()] if self.action == 'create' else super().get_permissions()

    def get_throttles(self):
        return [PedidoCreateThrottle()] if self.action == 'create' else super().get_throttles()

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        periodo = request.query_params.get('periodo', 'mensal')
        if periodo not in {'diario', 'mensal', 'anual'}:
            raise ValidationError({'periodo': 'Use diario, mensal ou anual.'})
        inicio = inicio_periodo(periodo)
        queryset = self.get_queryset().filter(status='CONCLUIDO', concluido_em__gte=inicio)
        resumo = queryset.aggregate(total_vendas=Sum('total'), pedidos_concluidos=Count('id'))
        total = resumo['total_vendas'] or Decimal('0')
        quantidade = resumo['pedidos_concluidos'] or 0
        itens = ItemPedido.objects.filter(pedido__in=queryset).aggregate(total=Sum('quantidade'))['total'] or 0
        pagamentos = {
            item['forma_pagamento']: {'quantidade': item['quantidade'], 'total': str(item['total'] or Decimal('0'))}
            for item in queryset.values('forma_pagamento').annotate(quantidade=Count('id'), total=Sum('total')).order_by()
        }
        return Response({
            'periodo': periodo,
            'total_vendas': str(total),
            'pedidos_concluidos': quantidade,
            'itens_vendidos': itens,
            'ticket_medio': str(total / quantidade if quantidade else Decimal('0')),
            'por_forma_pagamento': pagamentos,
        })

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        empresa_slug = str(request.data.get('empresa_slug', '')).strip()
        nome = str(request.data.get('cliente_nome', '')).strip()
        telefone = re.sub(r'\D', '', str(request.data.get('cliente_telefone', '')))
        forma = request.data.get('forma_pagamento')
        itens = request.data.get('itens') or []
        if not nome or len(telefone) < 10 or forma not in dict(Pedido.PAGAMENTO_CHOICES) or not itens:
            raise ValidationError('Informe nome, WhatsApp, forma de pagamento e os produtos.')
        ids = [item.get('produto') for item in itens]
        if len(ids) != len(set(ids)):
            raise ValidationError({'itens': 'Não repita produtos no pedido.'})
        produtos = {p.id: p for p in Produto.objects.select_for_update().filter(empresa__slug=empresa_slug, empresa__ativo=True, disponivel=True, id__in=ids)}
        if len(produtos) != len(ids):
            raise ValidationError({'itens': 'Um dos produtos não está disponível neste salão.'})
        normalizados, total = [], Decimal('0')
        for item in itens:
            try: quantidade = int(item.get('quantidade', 0))
            except (TypeError, ValueError): quantidade = 0
            produto = produtos.get(item.get('produto'))
            if quantidade < 1 or quantidade > 99 or (produto.controlar_estoque and quantidade > produto.estoque):
                raise ValidationError({'itens': f'Estoque insuficiente para {produto.nome}.'})
            normalizados.append((produto, quantidade))
            total += produto.preco_atual * quantidade
        empresa = next(iter(produtos.values())).empresa
        assinatura = '|'.join(f'{produto.id}:{quantidade}' for produto, quantidade in sorted(normalizados, key=lambda valor: valor[0].id))
        chave_duplicidade = 'pedido-duplicado:' + hashlib.sha256(f'{empresa.id}|{telefone}|{forma}|{assinatura}'.encode()).hexdigest()
        pedido_existente_id = cache.get(chave_duplicidade)
        if isinstance(pedido_existente_id, int):
            pedido_existente = Pedido.objects.select_related('empresa').prefetch_related('itens').filter(
                pk=pedido_existente_id, empresa=empresa, cliente_telefone=telefone,
            ).first()
            if pedido_existente:
                dados = dict(self.get_serializer(pedido_existente).data)
                dados['pedido_reutilizado'] = True
                return Response(dados, status=status.HTTP_200_OK)
        if not cache.add(chave_duplicidade, 'processando', timeout=120):
            return Response(
                {'detail': 'Seu pedido está sendo processado. Tente novamente em alguns segundos.'},
                status=status.HTTP_409_CONFLICT,
            )
        pedido = Pedido.objects.create(empresa=empresa, cliente=request.user if request.user.is_authenticated else None,
            cliente_nome=nome, cliente_telefone=telefone, forma_pagamento=forma, total=total)
        for produto, quantidade in normalizados:
            ItemPedido.objects.create(pedido=pedido, produto=produto, nome_produto=produto.nome, quantidade=quantidade, preco_unitario=produto.preco_atual)
            if produto.controlar_estoque:
                produto.estoque -= quantidade
                produto.save(update_fields=['estoque'])
        transaction.on_commit(lambda: cache.set(chave_duplicidade, pedido.id, timeout=120))
        transaction.on_commit(lambda pedido_id=pedido.id: notificar_novo_pedido(pedido_id))
        return Response(self.get_serializer(pedido).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='regenerar-ticket')
    def regenerar_ticket(self, request, pk=None):
        pedido = self.get_object()
        pedido.regenerar_ticket()
        return Response(self.get_serializer(pedido).data)

    @action(detail=True, methods=['patch'])
    @transaction.atomic
    def status(self, request, pk=None):
        pedido = self.get_queryset().select_for_update().get(pk=pk)
        novo = request.data.get('status')
        if not pedido.pode_transicionar_para(novo):
            raise ValidationError({'status': f'Não é possível alterar de {pedido.get_status_display()} para a situação solicitada.'})
        if novo == 'AGUARDANDO_SINAL' and (not pedido.empresa.chave_pix or not pedido.empresa.beneficiario_pix):
            raise ValidationError({'status': 'Cadastre a chave PIX e o beneficiário antes de solicitar o sinal.'})
        status_anterior = pedido.status
        if novo == 'CANCELADO':
            pedido.devolver_estoque()
        pedido.status = novo
        if novo == 'CONCLUIDO':
            pedido.concluido_em = timezone.now()
        pedido.sinal_solicitado = novo in {'AGUARDANDO_SINAL', 'SINAL_CONFIRMADO', 'PRONTO', 'CONCLUIDO'} or pedido.sinal_solicitado
        pedido.sinal_confirmado = novo in {'SINAL_CONFIRMADO', 'PRONTO', 'CONCLUIDO'} and pedido.sinal_solicitado
        pedido.save()
        transaction.on_commit(lambda pedido_id=pedido.id, anterior=status_anterior: notificar_status_pedido(pedido_id, anterior))
        return Response(self.get_serializer(pedido).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def ticket_pedido(request, token):
    try:
        pedido = Pedido.objects.select_related('empresa').prefetch_related('itens').get(token_ticket=token)
    except Pedido.DoesNotExist:
        return Response({'detail': 'Ticket não encontrado.'}, status=404)
    if pedido.ticket_expirado:
        return Response({'detail': 'Este link expirou. Solicite um novo link ao salão.'}, status=410)
    response = Response(PedidoPublicoSerializer(pedido, context={'request': request}).data)
    response['Cache-Control'] = 'no-store, private, max-age=0'
    response['Pragma'] = 'no-cache'
    return response
