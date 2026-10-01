"""Jornada ponta a ponta: criação do negócio, gestão e agendamento do cliente."""
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import Usuario
from apps.agenda.models import Agendamento, Servico
from apps.tenants.models import Empresa


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    REST_FRAMEWORK={
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework_simplejwt.authentication.JWTAuthentication',
        ),
        'DEFAULT_THROTTLE_RATES': {'auth_ip': '1000/min', 'auth_account': '1000/min'},
    },
)
class CompleteBusinessJourneyTests(APITestCase):
    manager_password = 'GestorFluxo!2026'
    customer_password = 'ClienteFluxo!2026'

    def bearer(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    @patch('services.waha_service.enviar_mensagem_whatsapp')
    def test_complete_manager_and_customer_journey(self, send_whatsapp):
        # 1. O futuro gestor cria a barbearia e recebe uma sessão válida.
        signup = self.client.post('/api/saas/registrar/', {
            'nome_barbearia': 'Barbearia Jornada Completa',
            'nome_admin': 'Gestor da Jornada',
            'email': 'gestor.jornada@example.test',
            'senha': self.manager_password,
            'whatsapp': '11999990001',
            'aceitou_termos': True,
        }, format='json', REMOTE_ADDR='10.50.0.1')
        self.assertEqual(signup.status_code, 201, signup.data)
        manager_token = signup.data['access']
        company_id = signup.data['user']['empresa']['id']
        company_slug = signup.data['user']['empresa']['slug']

        company = Empresa.objects.get(pk=company_id)
        manager = Usuario.objects.get(email='gestor.jornada@example.test')
        self.assertEqual(manager.tipo, 'ADMINISTRADOR')
        self.assertTrue(company.em_trial)
        # O cadastro atualmente usa timezone.now().date() (UTC), portanto este
        # teste documenta o comportamento existente; a diferença para a data
        # local perto da virada do dia é reportada separadamente pela QA.
        self.assertEqual(company.data_fim_trial, timezone.now().date() + timedelta(days=30))

        # 2. O gestor configura o estabelecimento.
        self.bearer(manager_token)
        settings_response = self.client.patch(f'/api/empresas/{company_id}/', {
            'hora_abertura': '09:00',
            'hora_fechamento': '19:00',
            'intervalo_almoco_inicio': '12:00',
            'intervalo_almoco_fim': '13:00',
            'horas_limite_cancelamento': 6,
            'dias_retorno_lembrete': 20,
            'fidelidade_ativo': True,
            'fidelidade_meta': 5,
        }, format='json')
        self.assertEqual(settings_response.status_code, 200, settings_response.data)

        # 3. O gestor cadastra o serviço que será vendido.
        service_response = self.client.post('/api/servicos/', {
            'nome': 'Corte Jornada',
            'preco': '55.00',
            'duracao_minutos': 30,
            'ativo': True,
        }, format='json')
        self.assertEqual(service_response.status_code, 201, service_response.data)
        service_id = service_response.data['id']
        service = Servico.objects.get(pk=service_id)
        self.assertEqual(service.empresa_id, company_id)

        # 4. O gestor cria um profissional, automaticamente vinculado ao tenant.
        professional_response = self.client.post('/api/usuarios/', {
            'username': 'barbeiro.jornada@example.test',
            'email': 'barbeiro.jornada@example.test',
            'first_name': 'Carlos',
            'last_name': 'Jornada',
            'password': 'ProfissionalFluxo!2026',
            'telefone': '11999990002',
            'taxa_comissao': '40.00',
            'status': 'ATIVO',
        }, format='json')
        self.assertEqual(professional_response.status_code, 201, professional_response.data)
        professional_id = professional_response.data['id']
        professional = Usuario.objects.get(pk=professional_id)
        self.assertEqual(professional.tipo, 'PROFISSIONAL')
        self.assertEqual(professional.empresa_id, company_id)

        # 5. O catálogo público mostra apenas os dados necessários ao cliente.
        self.client.credentials()
        company_public = self.client.get(f'/api/empresas/por-slug/{company_slug}/')
        self.assertEqual(company_public.status_code, 200, company_public.data)
        services_public = self.client.get('/api/servicos/', {'empresa_id': company_id})
        self.assertEqual(services_public.status_code, 200, services_public.data)
        self.assertEqual([row['id'] for row in services_public.data], [service_id])
        professionals_public = self.client.get('/api/usuarios/', {'empresa_id': company_id})
        self.assertEqual(professionals_public.status_code, 200, professionals_public.data)
        public_barber = next(row for row in professionals_public.data if row['id'] == professional_id)
        self.assertNotIn('email', public_barber)
        self.assertNotIn('telefone', public_barber)

        # 6. O cliente aceita os termos, cria a conta para essa barbearia e recebe JWT.
        customer_signup = self.client.post('/api/clientes/registrar/', {
            'nome': 'Cliente da Jornada',
            'email': 'cliente.jornada@example.test',
            'senha': self.customer_password,
            'telefone': '11999990003',
            'empresa_id': company_id,
            'aceitou_termos': True,
        }, format='json', REMOTE_ADDR='10.50.0.2')
        self.assertEqual(customer_signup.status_code, 201, customer_signup.data)
        customer_token = customer_signup.data['access']
        customer = Usuario.objects.get(email='cliente.jornada@example.test')
        self.assertEqual(customer.tipo, 'CLIENTE')
        self.assertEqual(customer.empresa_id, company_id)
        self.assertTrue(customer.aceitou_termos)

        # 7. O cliente consulta a disponibilidade real e escolhe o primeiro horário.
        booking_date = timezone.localdate() + timedelta(days=2)
        availability = self.client.get('/api/disponibilidade/', {
            'data': booking_date.isoformat(),
            'barbeiro_id': professional_id,
            'servicos': str(service_id),
        })
        self.assertEqual(availability.status_code, 200, availability.data)
        self.assertTrue(availability.data['horarios_disponiveis'])
        selected_time = availability.data['horarios_disponiveis'][0]
        local_start = timezone.make_aware(
            datetime.combine(booking_date, datetime.strptime(selected_time, '%H:%M').time()),
            timezone.get_current_timezone(),
        )

        # 8. O cliente agenda o serviço; e-mail/WhatsApp são isolados por mocks.
        self.bearer(customer_token)
        with self.captureOnCommitCallbacks(execute=True):
            booking = self.client.post('/api/agendamentos/', {
                'profissional': professional_id,
                'servicos': [service_id],
                'data_hora_inicio': local_start.isoformat(),
                'metodo_pagamento': 'PIX',
            }, format='json')
        self.assertEqual(booking.status_code, 201, booking.data)
        appointment = Agendamento.objects.get(pk=booking.data['id'])
        self.assertEqual(appointment.cliente_id, customer.id)
        self.assertEqual(appointment.empresa_id, company_id)
        self.assertEqual(appointment.status, 'PENDENTE')
        self.assertEqual(appointment.valor_total, Decimal('55.00'))
        self.assertEqual(appointment.data_hora_fim, appointment.data_hora_inicio + timedelta(minutes=30))

        # 9. O horário fica ocupado e aparece no painel do gestor.
        self.client.credentials()
        after_booking = self.client.get('/api/disponibilidade/', {
            'data': booking_date.isoformat(),
            'barbeiro_id': professional_id,
            'servicos': str(service_id),
        })
        self.assertIn(selected_time, after_booking.data['horarios_ocupados'])

        self.bearer(manager_token)
        manager_agenda = self.client.get('/api/agendamentos/')
        self.assertEqual(manager_agenda.status_code, 200, manager_agenda.data)
        self.assertEqual([row['id'] for row in manager_agenda.data], [appointment.id])

        # 10. O gestor confirma o atendimento e o cliente vê o novo estado.
        confirmation = self.client.patch(
            f'/api/agendamentos/{appointment.id}/', {'status': 'CONFIRMADO'}, format='json'
        )
        self.assertEqual(confirmation.status_code, 200, confirmation.data)
        self.bearer(customer_token)
        customer_agenda = self.client.get('/api/agendamentos/')
        self.assertEqual(customer_agenda.status_code, 200, customer_agenda.data)
        self.assertEqual(customer_agenda.data[0]['status'], 'CONFIRMADO')
        self.assertGreaterEqual(send_whatsapp.call_count, 1)
