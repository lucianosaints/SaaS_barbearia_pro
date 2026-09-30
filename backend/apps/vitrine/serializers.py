from decimal import Decimal

from rest_framework import serializers

from .models import ItemPedido, Pedido, Produto


class ProdutoSerializer(serializers.ModelSerializer):
    em_estoque = serializers.BooleanField(read_only=True)
    preco_atual = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Produto
        fields = [
            'id', 'empresa', 'nome', 'descricao', 'preco', 'preco_promocional',
            'preco_atual', 'estoque', 'controlar_estoque', 'em_estoque',
            'disponivel', 'destaque', 'foto', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']
        extra_kwargs = {'empresa': {'required': False}}
        validators = []

    def validate(self, attrs):
        request = self.context['request']
        user = request.user
        instance = self.instance
        empresa = attrs.get('empresa', instance.empresa if instance else getattr(user, 'empresa', None))

        if not user.is_superuser:
            if not user.is_authenticated or not user.empresa_id or empresa != user.empresa:
                raise serializers.ValidationError({'empresa': 'Empresa inválida.'})
            attrs['empresa'] = user.empresa
        if instance and empresa != instance.empresa:
            raise serializers.ValidationError({'empresa': 'Não é permitido transferir um produto.'})
        if not empresa:
            raise serializers.ValidationError({'empresa': 'Informe o salão.'})

        nome = attrs.get('nome', instance.nome if instance else '').strip()
        if not nome:
            raise serializers.ValidationError({'nome': 'Informe o nome do produto.'})
        attrs['nome'] = nome
        duplicados = Produto.objects.filter(empresa=empresa, nome__iexact=nome)
        if instance:
            duplicados = duplicados.exclude(pk=instance.pk)
        if duplicados.exists():
            raise serializers.ValidationError({'nome': 'Já existe um produto com este nome neste salão.'})

        preco = attrs.get('preco', instance.preco if instance else Decimal('0'))
        promocional = attrs.get('preco_promocional', instance.preco_promocional if instance else None)
        if promocional is not None and promocional >= preco:
            raise serializers.ValidationError({'preco_promocional': 'O preço promocional deve ser menor que o preço normal.'})
        return attrs


class ItemPedidoSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    class Meta:
        model = ItemPedido
        fields = ['produto', 'nome_produto', 'quantidade', 'preco_unitario', 'subtotal']


class PedidoSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True, read_only=True)
    empresa_nome = serializers.CharField(source='empresa.nome', read_only=True)
    valor_sinal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    saldo_restante = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    chave_pix = serializers.SerializerMethodField()
    beneficiario_pix = serializers.SerializerMethodField()
    ticket_url = serializers.SerializerMethodField()
    ticket_expira_em = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Pedido
        fields = ['id', 'empresa', 'empresa_nome', 'cliente_nome', 'cliente_telefone', 'forma_pagamento',
                  'status', 'total', 'sinal_solicitado', 'sinal_confirmado', 'valor_sinal', 'saldo_restante',
                  'chave_pix', 'beneficiario_pix', 'ticket_url', 'ticket_expira_em', 'itens', 'criado_em', 'atualizado_em']
        read_only_fields = ['id', 'empresa', 'status', 'total', 'sinal_solicitado', 'sinal_confirmado', 'criado_em', 'atualizado_em']

    def get_chave_pix(self, obj):
        return obj.empresa.chave_pix if obj.sinal_solicitado else ''

    def get_beneficiario_pix(self, obj):
        return obj.empresa.beneficiario_pix if obj.sinal_solicitado else ''

    def get_ticket_url(self, obj):
        return f'/api/pedidos/ticket/{obj.token_ticket}/'


class PedidoPublicoSerializer(PedidoSerializer):
    cliente_nome = serializers.SerializerMethodField()
    cliente_telefone = serializers.SerializerMethodField()

    class Meta(PedidoSerializer.Meta):
        fields = [
            'id', 'empresa_nome', 'cliente_nome', 'cliente_telefone', 'forma_pagamento',
            'status', 'total', 'sinal_solicitado', 'sinal_confirmado', 'valor_sinal',
            'saldo_restante', 'chave_pix', 'beneficiario_pix', 'itens', 'criado_em',
            'atualizado_em', 'ticket_expira_em',
        ]

    def get_cliente_nome(self, obj):
        partes = obj.cliente_nome.split()
        return partes[0] + (f' {partes[-1][0]}.' if len(partes) > 1 else '')

    def get_cliente_telefone(self, obj):
        digitos = ''.join(filter(str.isdigit, obj.cliente_telefone))
        return f'(**) *****-{digitos[-4:]}' if len(digitos) >= 4 else '(**) *****-****'
