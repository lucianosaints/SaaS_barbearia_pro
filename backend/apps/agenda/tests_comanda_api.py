from decimal import Decimal

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import Usuario
from apps.tenants.models import Empresa
from apps.vitrine.models import Produto
from .models import Agendamento, Comanda, Servico


@override_settings(AGENDA_NOTIFICATIONS_ASYNC=False)
class ComandaApiTests(APITestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome='Salão API', slug='salao-api')
        self.outra_empresa = Empresa.objects.create(nome='Outro Salão', slug='outro-salao-api')
        self.admin = Usuario.objects.create_user(
            username='admin-comanda-api', password='Senha!2026', tipo='ADMINISTRADOR', empresa=self.empresa,
        )
        self.outro_admin = Usuario.objects.create_user(
            username='outro-admin-comanda', password='Senha!2026', tipo='ADMINISTRADOR', empresa=self.outra_empresa,
        )
        self.profissional = Usuario.objects.create_user(
            username='prof-comanda-api', tipo='PROFISSIONAL', empresa=self.empresa, taxa_comissao=Decimal('40.00'),
        )
        self.cliente = Usuario.objects.create_user(username='cliente-comanda-api', tipo='CLIENTE', empresa=self.empresa)
        self.servico = Servico.objects.create(empresa=self.empresa, nome='Corte API', preco=Decimal('50.00'), duracao_minutos=30)
        self.extra = Servico.objects.create(empresa=self.empresa, nome='Barba API', preco=Decimal('20.00'), duracao_minutos=20)
        self.produto = Produto.objects.create(empresa=self.empresa, nome='Pomada API', preco=Decimal('30.00'), estoque=3)
        self.produto_outro = Produto.objects.create(empresa=self.outra_empresa, nome='Produto externo', preco=10, estoque=3)
        self.agendamento = Agendamento.objects.create(
            empresa=self.empresa, cliente=self.cliente, profissional=self.profissional,
            data_hora_inicio=timezone.now(), data_hora_fim=timezone.now(), status='CONFIRMADO',
        )
        self.agendamento.servicos.add(self.servico)
        self.client.force_authenticate(self.admin)

    def abrir(self):
        return self.client.post('/api/comandas/', {'agendamento': self.agendamento.id}, format='json')

    def test_abertura_e_idempotencia_criam_fotografia_dos_servicos(self):
        primeira = self.abrir()
        segunda = self.abrir()
        self.assertEqual(primeira.status_code, 201, primeira.data)
        self.assertEqual(segunda.status_code, 200, segunda.data)
        self.assertEqual(primeira.data['id'], segunda.data['id'])
        self.assertEqual(primeira.data['itens_servico'][0]['nome'], 'Corte API')
        self.assertEqual(Comanda.objects.count(), 1)

    def test_isolamento_impede_acesso_e_abertura_por_outro_salao(self):
        comanda_id = self.abrir().data['id']
        self.client.force_authenticate(self.outro_admin)
        self.assertEqual(self.client.get(f'/api/comandas/{comanda_id}/').status_code, 404)
        self.assertEqual(self.client.post('/api/comandas/', {'agendamento': self.agendamento.id}, format='json').status_code, 403)

    def test_servicos_produtos_e_desconto_recalculam_no_servidor(self):
        comanda_id = self.abrir().data['id']
        servico = self.client.post(f'/api/comandas/{comanda_id}/adicionar-servico/', {'servico': self.extra.id}, format='json')
        self.assertEqual(servico.status_code, 200, servico.data)
        produto = self.client.post(f'/api/comandas/{comanda_id}/adicionar-produto/', {'produto': self.produto.id, 'quantidade': 2}, format='json')
        self.assertEqual(produto.status_code, 200, produto.data)
        self.assertEqual(Decimal(produto.data['subtotal_produtos']), Decimal('60.00'))
        externo = self.client.post(f'/api/comandas/{comanda_id}/adicionar-produto/', {'produto': self.produto_outro.id}, format='json')
        self.assertEqual(externo.status_code, 400)
        desconto = self.client.patch(f'/api/comandas/{comanda_id}/', {'desconto': '10.00'}, format='json')
        self.assertEqual(desconto.status_code, 200, desconto.data)
        self.assertEqual(Decimal(desconto.data['total']), Decimal('120.00'))
        self.assertEqual(desconto.data['desconto_autorizado_por'], self.admin.id)

    def test_profissional_pode_descontar_somente_a_propria_comanda(self):
        comanda_id = self.abrir().data['id']
        self.client.force_authenticate(self.profissional)
        response = self.client.patch(f'/api/comandas/{comanda_id}/', {'desconto': '5.00'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['desconto_autorizado_por'], self.profissional.id)

        outro_profissional = Usuario.objects.create_user(
            username='outro-prof-comanda-api', tipo='PROFISSIONAL', empresa=self.empresa,
        )
        self.client.force_authenticate(outro_profissional)
        self.assertEqual(self.client.patch(f'/api/comandas/{comanda_id}/', {'desconto': '1.00'}, format='json').status_code, 404)

    def test_fechamento_registra_autor_pagamento_comissao_e_estoque(self):
        comanda_id = self.abrir().data['id']
        self.client.post(f'/api/comandas/{comanda_id}/adicionar-produto/', {'produto': self.produto.id, 'quantidade': 1}, format='json')
        response = self.client.post(f'/api/comandas/{comanda_id}/fechar/', {'metodo_pagamento': 'PIX'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['status'], 'FECHADA')
        self.assertEqual(response.data['fechado_por'], self.admin.id)
        self.assertEqual(Decimal(response.data['valor_comissao']), Decimal('20.00'))
        self.produto.refresh_from_db(); self.agendamento.refresh_from_db()
        self.assertEqual(self.produto.estoque, 2)
        self.assertEqual(self.agendamento.status_pagamento, 'PAGO')
        self.assertEqual(self.client.post(f'/api/comandas/{comanda_id}/fechar/', {'metodo_pagamento': 'PIX'}, format='json').status_code, 400)

    def test_cancelamento_estorna_estoque_e_nao_pode_repetir(self):
        comanda_id = self.abrir().data['id']
        self.client.post(f'/api/comandas/{comanda_id}/adicionar-produto/', {'produto': self.produto.id}, format='json')
        self.client.post(f'/api/comandas/{comanda_id}/fechar/', {'metodo_pagamento': 'DINHEIRO'}, format='json')
        response = self.client.post(f'/api/comandas/{comanda_id}/cancelar/', format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['cancelado_por'], self.admin.id)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque, 3)
        self.assertEqual(self.client.post(f'/api/comandas/{comanda_id}/cancelar/', format='json').status_code, 400)
