from decimal import Decimal

from rest_framework import serializers

from .models import Produto


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
