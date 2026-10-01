from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.tenants.models import Empresa
from apps.vitrine.models import Produto
from .models import Agendamento, Comanda, ItemComandaProduto, ItemComandaServico, Servico


class ComandaRulesTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome='Salão Comanda', slug='salao-comanda')
        self.profissional = Usuario.objects.create_user(
            username='profissional-comanda', tipo='PROFISSIONAL', empresa=self.empresa,
            taxa_comissao=Decimal('40.00'),
        )
        self.cliente = Usuario.objects.create_user(username='cliente-comanda', tipo='CLIENTE', empresa=self.empresa)
        self.servico = Servico.objects.create(empresa=self.empresa, nome='Corte', preco=Decimal('50.00'), duracao_minutos=30)
        self.produto = Produto.objects.create(empresa=self.empresa, nome='Pomada', preco=Decimal('30.00'), estoque=2)
        self.agendamento = Agendamento.objects.create(
            empresa=self.empresa, cliente=self.cliente, profissional=self.profissional,
            data_hora_inicio=timezone.now(), data_hora_fim=timezone.now(), status='CONFIRMADO',
        )
        self.agendamento.servicos.add(self.servico)
        self.comanda = Comanda.objects.create(
            empresa=self.empresa, agendamento=self.agendamento, profissional=self.profissional,
            desconto=Decimal('5.00'),
        )
        ItemComandaServico.objects.create(
            comanda=self.comanda, servico=self.servico, nome=self.servico.nome,
            preco_unitario=self.servico.preco,
        )
        ItemComandaProduto.objects.create(
            comanda=self.comanda, produto=self.produto, nome=self.produto.nome,
            preco_unitario=self.produto.preco, quantidade=1,
        )

    def test_fechamento_calcula_valores_e_baixa_estoque(self):
        fechada = self.comanda.fechar('PIX')
        self.assertEqual(fechada.total, Decimal('75.00'))
        self.assertEqual(fechada.valor_comissao, Decimal('20.00'))
        self.produto.refresh_from_db()
        self.agendamento.refresh_from_db()
        self.assertEqual(self.produto.estoque, 1)
        self.assertEqual(self.agendamento.status, 'CONCLUIDO')
        self.assertEqual(self.agendamento.status_pagamento, 'PAGO')

    def test_cancelar_fechada_devolve_estoque_uma_vez(self):
        self.comanda.fechar('DINHEIRO')
        self.comanda.cancelar()
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque, 2)
        with self.assertRaises(ValidationError):
            self.comanda.cancelar()

    def test_estoque_insuficiente_impede_fechamento(self):
        self.produto.estoque = 0
        self.produto.save(update_fields=['estoque'])
        with self.assertRaises(ValidationError):
            self.comanda.fechar('PIX')
        self.comanda.refresh_from_db()
        self.assertEqual(self.comanda.status, 'ABERTA')
