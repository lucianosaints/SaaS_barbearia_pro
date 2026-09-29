from decimal import Decimal

from rest_framework.test import APITestCase

from apps.accounts.models import Usuario
from apps.tenants.models import Empresa
from .models import Produto


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
        ids = {item['id'] for item in response.data}
        self.assertEqual(ids, {self.produto_a.id})

    def test_admin_lista_e_cria_apenas_na_propria_empresa(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.get('/api/produtos/')
        self.assertEqual({item['id'] for item in response.data}, {self.produto_a.id})
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
