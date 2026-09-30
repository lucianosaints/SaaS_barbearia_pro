import uuid
from datetime import timedelta

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F
from django.utils import timezone

from apps.tenants.models import Empresa


class Produto(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='produtos')
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, default='')
    preco = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    preco_promocional = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    estoque = models.PositiveIntegerField(default=0)
    controlar_estoque = models.BooleanField(default=True)
    disponivel = models.BooleanField(default=True)
    destaque = models.BooleanField(default=False)
    foto = models.ImageField(upload_to='produtos/', blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-destaque', 'nome']
        constraints = [
            models.UniqueConstraint(fields=['empresa', 'nome'], name='produto_nome_unico_por_empresa'),
        ]

    @property
    def em_estoque(self):
        return not self.controlar_estoque or self.estoque > 0

    @property
    def preco_atual(self):
        return self.preco_promocional if self.preco_promocional is not None else self.preco

    def __str__(self):
        return f'{self.nome} - {self.empresa.nome}'


class Pedido(models.Model):
    STATUS_CHOICES = [
        ('AGUARDANDO_CONFIRMACAO', 'Aguardando confirmação'),
        ('CONFIRMADO', 'Confirmado'),
        ('AGUARDANDO_SINAL', 'Aguardando sinal'),
        ('SINAL_CONFIRMADO', 'Sinal confirmado'),
        ('PRONTO', 'Pronto para retirada'),
        ('CONCLUIDO', 'Concluído'),
        ('CANCELADO', 'Cancelado'),
    ]
    PAGAMENTO_CHOICES = [('PIX', 'PIX'), ('DINHEIRO', 'Dinheiro'), ('DEBITO', 'Cartão de débito'), ('CREDITO', 'Cartão de crédito')]

    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='pedidos_vitrine')
    cliente = models.ForeignKey('accounts.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_vitrine')
    cliente_nome = models.CharField(max_length=150)
    cliente_telefone = models.CharField(max_length=20)
    forma_pagamento = models.CharField(max_length=10, choices=PAGAMENTO_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='AGUARDANDO_CONFIRMACAO')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    sinal_solicitado = models.BooleanField(default=False)
    sinal_confirmado = models.BooleanField(default=False)
    token_ticket = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    token_ticket_criado_em = models.DateTimeField(default=timezone.now, editable=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']

    TRANSICOES = {
        'AGUARDANDO_CONFIRMACAO': {'CONFIRMADO', 'AGUARDANDO_SINAL', 'CANCELADO'},
        'CONFIRMADO': {'AGUARDANDO_SINAL', 'PRONTO', 'CANCELADO'},
        'AGUARDANDO_SINAL': {'SINAL_CONFIRMADO', 'CANCELADO'},
        'SINAL_CONFIRMADO': {'PRONTO', 'CANCELADO'},
        'PRONTO': {'CONCLUIDO', 'CANCELADO'},
        'CONCLUIDO': set(),
        'CANCELADO': set(),
    }

    @property
    def valor_sinal(self):
        return (self.total / 2).quantize(self.total)

    @property
    def saldo_restante(self):
        return self.total - (self.valor_sinal if self.sinal_solicitado else 0)

    def pode_transicionar_para(self, novo_status):
        return novo_status in self.TRANSICOES.get(self.status, set())

    @property
    def ticket_expira_em(self):
        dias = getattr(settings, 'PEDIDO_TICKET_DIAS_VALIDADE', 90)
        return self.token_ticket_criado_em + timedelta(days=dias)

    @property
    def ticket_expirado(self):
        return timezone.now() >= self.ticket_expira_em

    def regenerar_ticket(self):
        self.token_ticket = uuid.uuid4()
        self.token_ticket_criado_em = timezone.now()
        self.save(update_fields=['token_ticket', 'token_ticket_criado_em', 'atualizado_em'])

    def devolver_estoque(self):
        for item in self.itens.select_related('produto'):
            if item.produto.controlar_estoque:
                Produto.objects.filter(pk=item.produto_id).update(estoque=F('estoque') + item.quantidade)


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name='itens_pedido')
    nome_produto = models.CharField(max_length=150)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.preco_unitario * self.quantidade
