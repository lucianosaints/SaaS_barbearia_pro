from django.test import TransactionTestCase
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta
from apps.tenants.models import Empresa
from apps.accounts.models import Usuario
from apps.agenda.models import Agendamento, Servico

class WahaIsolationTest(TransactionTestCase):
    def setUp(self):
        # Criar duas empresas diferentes
        self.empresa_a = Empresa.objects.create(nome="Empresa A", slug="empresa-a")
        self.empresa_b = Empresa.objects.create(nome="Empresa B", slug="empresa-b")

        # Criar usuários e vincular à empresa A
        self.cliente = Usuario.objects.create(
            username="cliente_a", 
            telefone="11999999999", 
            email="cliente@teste.com",
            empresa=self.empresa_a
        )
        self.profissional = Usuario.objects.create(
            username="barbeiro_a", 
            telefone="11888888888",
            empresa=self.empresa_a
        )

        # Criar serviço para a empresa A
        self.servico = Servico.objects.create(
            nome="Corte", 
            preco=50.0,
            duracao_minutos=30,
            empresa=self.empresa_a
        )

    @patch('requests.post')
    @patch('apps.agenda.signals.send_mail')
    def test_disparo_waha_utiliza_apenas_sessao_da_empresa(self, mock_send_mail, mock_post):
        """
        Garante que ao criar um agendamento na Empresa A, o disparo do WhatsApp 
        use ESTRITAMENTE a sessão do WAHA da Empresa A, e nunca chame a Sessão B.
        """
        mock_response = MagicMock(ok=True, status_code=200)
        mock_post.return_value = mock_response

        data_inicio = timezone.now() + timedelta(days=1)
        data_fim = data_inicio + timedelta(minutes=30)
        
        # Criar o agendamento
        agendamento = Agendamento.objects.create(
            empresa=self.empresa_a,
            cliente=self.cliente,
            profissional=self.profissional,
            data_hora_inicio=data_inicio,
            data_hora_fim=data_fim,
            status='PENDENTE'
        )
        
        # Adicionar o serviço dispara o signal m2m_changed
        # Em TransactionTestCase, on_commit é executado ao fim da transação real,
        # mas como estamos operando fora do rollback (autocommit), ele dispara.
        agendamento.servicos.add(self.servico)

        # A asserção vai checar as chamadas feitas para o mock do requests.post
        # O WAHA é disparado 2 vezes (1 para o cliente, 1 para o profissional)
        chamadas_waha = [
            call for call in mock_post.mock_calls
            if 'api/sendText' in call.args[0]
        ]
        
        self.assertTrue(len(chamadas_waha) > 0, "Deveria ter disparado chamadas para o WAHA")
        
        sessao_a = f"tenant_{self.empresa_a.id}"
        sessao_b = f"tenant_{self.empresa_b.id}"

        # Validar se TODAS as chamadas utilizaram APENAS a sessão da Empresa A
        for chamada in chamadas_waha:
            url_chamada = chamada.args[0]
            kwargs_chamada = chamada.kwargs

            # O payload foi enviado com JSON
            payload = kwargs_chamada.get('json', {})
            
            # Verifica explicitamente o body e a URL da chamada
            self.assertIn(f"session={sessao_a}", url_chamada, f"A URL da requisição deveria conter 'session={sessao_a}' explicitamente")
            self.assertEqual(payload.get('session'), sessao_a, "O payload da requisição deveria referenciar a Sessão A")
            
            self.assertNotIn(sessao_b, url_chamada, "O ID da sessão B NUNCA deveria estar na URL")
            self.assertNotEqual(payload.get('session'), sessao_b, "O payload NUNCA deveria referenciar a Sessão B")
