from decimal import Decimal
import base64
import tempfile
from unittest.mock import patch
from datetime import timedelta

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import Usuario
from apps.tenants.models import Empresa
from .models import Pedido, Produto


class ProdutoIsolationTests(APITestCase):
    def setUp(self):
        self.a = Empresa.objects.create(nome='Salão A', slug='salao-a')
        self.b = Empresa.objects.create(nome='Salão B', slug='salao-b')
        self.admin_a = Usuario.objects.create_user(username='admin-a', password='Senha!2026', tipo='ADMINISTRADOR', empresa=self.a)
        self.admin_b = Usuario.objects.create_user(username='admin-b', password='Senha!2026', tipo='ADMINISTRADOR', empresa=self.b)
        self.produto_a = Produto.objects.create(empresa=self.a, nome='Pomada', preco=Decimal('40'), estoque=2)
        self.produto_b = Produto.objects.create(empresa=self.b, nome='Óleo', preco=Decimal('30'), estoque=3)

    def test_catalogo_publico_exibe_apenas_produtos_disponiveis_do_salao(self):
        Produto.objects.create(empresa=self.a, nome='Oculto', preco=Decimal('10'), disponivel=False)
        response = self.client.get('/api/produtos/', {'empresa_slug': self.a.slug})
        self.assertEqual(response.status_code, 200)
        ids = {item['id'] for item in response.data['results']}
        self.assertEqual(ids, {self.produto_a.id})

    def test_admin_lista_e_cria_apenas_na_propria_empresa(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.get('/api/produtos/')
        self.assertEqual({item['id'] for item in response.data['results']}, {self.produto_a.id})
        created = self.client.post('/api/produtos/', {'nome': 'Shampoo', 'preco': '25.00', 'estoque': 4}, format='json')
        self.assertEqual(created.status_code, 201)
        self.assertEqual(Produto.objects.get(pk=created.data['id']).empresa, self.a)

    def test_admin_nao_altera_produto_de_outro_salao(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.patch(f'/api/produtos/{self.produto_b.id}/', {'preco': '1.00'}, format='json')
        self.assertEqual(response.status_code, 404)

    def test_preco_promocional_precisa_ser_menor(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.post('/api/produtos/', {
            'nome': 'Kit', 'preco': '50.00', 'preco_promocional': '60.00', 'estoque': 1,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('preco_promocional', response.data)

    def test_admin_pode_enviar_foto_do_produto(self):
        imagem = SimpleUploadedFile(
            'produto.png',
            base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='),
            content_type='image/png',
        )
        self.client.force_authenticate(self.admin_a)
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post('/api/produtos/', {
                'nome': 'Produto com foto', 'preco': '25.00', 'estoque': 1, 'foto': imagem,
            }, format='multipart')
            self.assertEqual(response.status_code, 201, response.data)
            self.assertTrue(Produto.objects.get(pk=response.data['id']).foto.name.startswith('produtos/'))


class PedidoTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.empresa = Empresa.objects.create(nome='Salão Pedido', slug='salao-pedido', chave_pix='pix@salao.test', beneficiario_pix='Salão Pedido')
        self.admin = Usuario.objects.create_user(username='gestor-pedido', password='Senha!2026', tipo='ADMINISTRADOR', empresa=self.empresa)
        self.produto = Produto.objects.create(empresa=self.empresa, nome='Pomada Reserva', preco=Decimal('40.00'), estoque=3)

    @patch('apps.vitrine.views.notificar_novo_pedido')
    def test_criacao_publica_usa_preco_do_servidor_e_reserva_estoque(self, notificar):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post('/api/pedidos/', {
                'empresa_slug': self.empresa.slug, 'cliente_nome': 'Cliente Teste',
                'cliente_telefone': '(11) 99999-0000', 'forma_pagamento': 'PIX',
                'itens': [{'produto': self.produto.id, 'quantidade': 2, 'preco_unitario': '0.01'}],
            }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['total'], '80.00')
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque, 1)
        self.assertTrue(response.data['ticket_url'].startswith('/api/pedidos/ticket/'))
        notificar.assert_called_once()

    def test_pedido_rejeita_produto_de_outro_salao(self):
        outra = Empresa.objects.create(nome='Outro', slug='outro')
        produto = Produto.objects.create(empresa=outra, nome='Óleo', preco=10, estoque=1)
        response = self.client.post('/api/pedidos/', {
            'empresa_slug': self.empresa.slug, 'cliente_nome': 'Cliente', 'cliente_telefone': '11999990000',
            'forma_pagamento': 'DINHEIRO', 'itens': [{'produto': produto.id, 'quantidade': 1}],
        }, format='json')
        self.assertEqual(response.status_code, 400)

    @patch('apps.vitrine.views.notificar_status_pedido')
    def test_transicoes_e_cancelamento_devolvem_estoque_uma_vez(self, notificar):
        pedido = Pedido.objects.create(empresa=self.empresa, cliente_nome='Cliente', cliente_telefone='11999990000', forma_pagamento='PIX', total=Decimal('40.00'))
        pedido.itens.create(produto=self.produto, nome_produto=self.produto.nome, quantidade=1, preco_unitario=Decimal('40'))
        Produto.objects.filter(pk=self.produto.pk).update(estoque=2)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.patch(f'/api/pedidos/{pedido.id}/status/', {'status': 'CONCLUIDO'}, format='json').status_code, 400)
        with self.captureOnCommitCallbacks(execute=True):
            cancelada = self.client.patch(f'/api/pedidos/{pedido.id}/status/', {'status': 'CANCELADO'}, format='json')
        self.assertEqual(cancelada.status_code, 200)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque, 3)
        self.assertEqual(self.client.patch(f'/api/pedidos/{pedido.id}/status/', {'status': 'CANCELADO'}, format='json').status_code, 400)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque, 3)

    def test_gestor_nao_enxerga_pedido_de_outra_empresa(self):
        outra = Empresa.objects.create(nome='Outro salão', slug='outro-salao')
        pedido = Pedido.objects.create(empresa=outra, cliente_nome='Cliente', cliente_telefone='11999990000', forma_pagamento='PIX', total=Decimal('10.00'))
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(f'/api/pedidos/{pedido.id}/').status_code, 404)

    def test_dashboard_financeiro_filtra_periodo_e_somente_concluidos(self):
        concluido = Pedido.objects.create(
            empresa=self.empresa, cliente_nome='Cliente', cliente_telefone='11999990000',
            forma_pagamento='PIX', total=Decimal('80.00'), status='CONCLUIDO', concluido_em=timezone.now(),
        )
        concluido.itens.create(produto=self.produto, nome_produto=self.produto.nome, quantidade=2, preco_unitario=Decimal('40'))
        Pedido.objects.create(
            empresa=self.empresa, cliente_nome='Pendente', cliente_telefone='11999990001',
            forma_pagamento='DINHEIRO', total=Decimal('40.00'), status='CONFIRMADO',
        )
        self.client.force_authenticate(self.admin)
        response = self.client.get('/api/pedidos/dashboard/', {'periodo': 'mensal'})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(Decimal(response.data['total_vendas']), Decimal('80.00'))
        self.assertEqual(response.data['pedidos_concluidos'], 1)
        self.assertEqual(response.data['itens_vendidos'], 2)
        self.assertEqual(Decimal(response.data['ticket_medio']), Decimal('80.00'))
        self.assertEqual(response.data['por_forma_pagamento']['PIX']['quantidade'], 1)

    def test_produtos_e_pedidos_sao_paginados(self):
        self.client.force_authenticate(self.admin)
        produtos = self.client.get('/api/produtos/')
        pedidos = self.client.get('/api/pedidos/')
        self.assertIn('results', produtos.data)
        self.assertIn('results', pedidos.data)

    @patch('apps.vitrine.views.notificar_status_pedido')
    def test_sinal_pix_mostra_metade_e_saldo_antes_da_confirmacao(self, notificar):
        pedido = Pedido.objects.create(
            empresa=self.empresa, cliente_nome='Cliente', cliente_telefone='11999990000',
            forma_pagamento='PIX', total=Decimal('79.80'),
        )
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f'/api/pedidos/{pedido.id}/status/', {'status': 'AGUARDANDO_SINAL'}, format='json',
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['valor_sinal'], '39.90')
        self.assertEqual(response.data['saldo_restante'], '39.90')

    @patch('apps.vitrine.views.notificar_novo_pedido')
    def test_pedido_duplicado_reabre_ticket_sem_baixar_estoque_novamente(self, notificar):
        dados = {
            'empresa_slug': self.empresa.slug, 'cliente_nome': 'Cliente Repetido',
            'cliente_telefone': '11999990000', 'forma_pagamento': 'PIX',
            'itens': [{'produto': self.produto.id, 'quantidade': 1}],
        }
        with self.captureOnCommitCallbacks(execute=True):
            primeiro = self.client.post('/api/pedidos/', dados, format='json')
        self.assertEqual(primeiro.status_code, 201)
        response = self.client.post('/api/pedidos/', dados, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], primeiro.data['id'])
        self.assertTrue(response.data['pedido_reutilizado'])
        self.assertEqual(response.data['ticket_url'], primeiro.data['ticket_url'])
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque, 2)
        self.assertEqual(Pedido.objects.count(), 1)

    def test_ticket_publico_mascara_dados_e_nao_permite_cache(self):
        pedido = Pedido.objects.create(
            empresa=self.empresa, cliente_nome='Maria da Silva', cliente_telefone='11987654321',
            forma_pagamento='PIX', total=Decimal('40.00'),
        )
        response = self.client.get(f'/api/pedidos/ticket/{pedido.token_ticket}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['cliente_nome'], 'Maria S.')
        self.assertEqual(response.data['cliente_telefone'], '(**) *****-4321')
        self.assertNotContains(response, '11987654321')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertNotIn('ticket_url', response.data)

    @patch('apps.vitrine.views.notificar_novo_pedido')
    def test_limite_publico_de_cinco_pedidos_em_dez_minutos(self, notificar):
        self.produto.controlar_estoque = False
        self.produto.save(update_fields=['controlar_estoque'])
        for indice in range(5):
            response = self.client.post('/api/pedidos/', {
                'empresa_slug': self.empresa.slug, 'cliente_nome': f'Cliente {indice}',
                'cliente_telefone': f'1199999000{indice}', 'forma_pagamento': 'PIX',
                'itens': [{'produto': self.produto.id, 'quantidade': 1}],
            }, format='json')
            self.assertEqual(response.status_code, 201, response.data)
        bloqueado = self.client.post('/api/pedidos/', {
            'empresa_slug': self.empresa.slug, 'cliente_nome': 'Cliente Bloqueado',
            'cliente_telefone': '11999990009', 'forma_pagamento': 'PIX',
            'itens': [{'produto': self.produto.id, 'quantidade': 1}],
        }, format='json')
        self.assertEqual(bloqueado.status_code, 429)

    @override_settings(PEDIDO_TICKET_DIAS_VALIDADE=90)
    def test_ticket_expirado_e_regenerado_somente_pelo_gestor(self):
        pedido = Pedido.objects.create(
            empresa=self.empresa, cliente_nome='Cliente', cliente_telefone='11999990000',
            forma_pagamento='PIX', total=Decimal('40.00'),
            token_ticket_criado_em=timezone.now() - timedelta(days=91),
        )
        antigo = pedido.token_ticket
        self.assertEqual(self.client.get(f'/api/pedidos/ticket/{antigo}/').status_code, 410)
        self.assertEqual(self.client.post(f'/api/pedidos/{pedido.id}/regenerar-ticket/').status_code, 401)
        self.client.force_authenticate(self.admin)
        response = self.client.post(f'/api/pedidos/{pedido.id}/regenerar-ticket/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(str(antigo), response.data['ticket_url'])
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f'/api/pedidos/ticket/{antigo}/').status_code, 404)
