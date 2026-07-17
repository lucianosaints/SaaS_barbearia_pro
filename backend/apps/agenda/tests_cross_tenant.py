from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from apps.tenants.models import Empresa
from apps.accounts.models import Usuario
from apps.agenda.models import Servico

class CrossTenantBookingTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Criar Empresas (Tenants)
        self.empresa_a = Empresa.objects.create(nome="Empresa A", slug="empresa-a")
        self.empresa_b = Empresa.objects.create(nome="Empresa B", slug="empresa-b")

        # Usuários da Empresa A
        self.cliente_a = Usuario.objects.create(
            username="cliente_a", 
            email="cliente_a@teste.com", 
            telefone="11999999999", 
            tipo="CLIENTE",
            empresa=self.empresa_a
        )
        self.profissional_a = Usuario.objects.create(
            username="barbeiro_a", 
            email="barbeiro_a@teste.com",
            tipo="PROFISSIONAL",
            empresa=self.empresa_a
        )
        self.servico_a = Servico.objects.create(
            nome="Corte A", 
            preco=50.0, 
            duracao_minutos=30,
            empresa=self.empresa_a
        )

        # Usuários da Empresa B
        self.profissional_b = Usuario.objects.create(
            username="barbeiro_b", 
            email="barbeiro_b@teste.com",
            tipo="PROFISSIONAL",
            empresa=self.empresa_b
        )
        self.servico_b = Servico.objects.create(
            nome="Corte B", 
            preco=50.0, 
            duracao_minutos=30,
            empresa=self.empresa_b
        )

    def test_impedir_agendamento_cruzado_de_cliente_a_com_profissional_b(self):
        """
        Garante que um cliente pertencente estritamente à Empresa A não consiga
        agendar um horário usando um profissional e/ou serviço da Empresa B.
        """
        # Cliente A se autentica
        self.client.force_authenticate(user=self.cliente_a)

        data_inicio = timezone.now() + timedelta(days=1)
        
        payload = {
            "profissional": self.profissional_b.id,
            "servicos": [self.servico_b.id],
            "data_hora_inicio": data_inicio.isoformat()
        }

        # Tentar criar o agendamento
        response = self.client.post('/api/agendamentos/', payload, format='json')

        # Deve ser bloqueado. O serializer agora restringe os profissionais que podem ser escolhidos, 
        # então pode dar erro de validação (400) porque o ID do profissional_b não está no queryset permitido,
        # ou se passasse, daria PermissionDenied (403). Vamos aceitar ambos (400 ou 403).
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN], 
                      f"Agendamento cruzado deveria ser barrado. Retornou {response.status_code}. Detalhes: {response.data}")
