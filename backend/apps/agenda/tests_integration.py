"""Regressões da combinação das regras locais com as funções da develop."""
from datetime import datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import override_settings
from django.urls import resolve
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import Usuario
from apps.agenda.models import Agendamento, BloqueioHorario, CartaoFidelidade, Servico
from apps.tenants.models import Empresa


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class DevelopIntegrationTests(APITestCase):
    def setUp(self):
        self.company = Empresa.objects.create(nome='Integração', slug='integracao', fidelidade_ativo=True, fidelidade_meta=2)
        self.manager = Usuario.objects.create_user(username='admin-integration', password='IntegrationTest!2026', tipo='ADMINISTRADOR', empresa=self.company)
        self.barber = Usuario.objects.create_user(username='barber-integration', tipo='PROFISSIONAL', empresa=self.company, taxa_comissao=Decimal('40'))
        self.customer = Usuario.objects.create_user(username='customer-integration', tipo='CLIENTE', empresa=self.company)
        self.service = Servico.objects.create(nome='Corte', empresa=self.company, preco=Decimal('50'), duracao_minutos=30)
        self.start = timezone.make_aware(datetime.combine(timezone.localdate() + timedelta(days=2), time(10)))
        self.client.force_authenticate(self.customer)
        self.waha = patch('services.waha_service.enviar_mensagem_whatsapp').start()
        self.addCleanup(patch.stopall)

    def payload(self, **changes):
        data = {'profissional': self.barber.pk, 'servicos': [self.service.pk], 'data_hora_inicio': self.start.isoformat(), 'metodo_pagamento': 'PIX'}
        data.update(changes)
        return data

    def book(self):
        response = self.client.post('/api/agendamentos/', self.payload(), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data['id']

    def test_login_keeps_company_subscription_metadata(self):
        self.client.force_authenticate(None)
        response = self.client.post('/api/token/', {'username': self.manager.username, 'password': 'IntegrationTest!2026'})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['user']['empresa']['slug'], self.company.slug)
        self.assertIn('em_trial', response.data['user']['empresa'])

    def test_public_professional_photos_and_working_owner_remain_available(self):
        self.client.force_authenticate(None)
        response = self.client.get('/api/usuarios/', {'empresa_id': self.company.pk})
        self.assertEqual({row['id'] for row in response.data}, {self.manager.pk, self.barber.pk})
        for row in response.data:
            self.assertIn('foto', row)
            self.assertIn('avaliacao', row)
            self.assertNotIn('email', row)
        self.client.force_authenticate(self.customer)
        response = self.client.post('/api/agendamentos/', self.payload(profissional=self.manager.pk), format='json')
        self.assertEqual(response.status_code, 201, response.data)

    def test_me_and_team_edit_preserve_blank_password_and_privileges(self):
        self.client.force_authenticate(self.manager)
        response = self.client.patch('/api/usuarios/me/', {'first_name': 'Gestor', 'password': '', 'is_staff': True}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.manager.refresh_from_db()
        self.assertFalse(self.manager.is_staff)
        self.assertTrue(self.manager.check_password('IntegrationTest!2026'))
        response = self.client.patch(f'/api/usuarios/{self.barber.pk}/', {'password': '', 'comissao_percentual': '55.00', 'status': 'ATIVO'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)

    def test_blocks_are_honored_by_both_availability_and_booking(self):
        BloqueioHorario.objects.create(empresa=self.company, profissional=None, data_hora_inicio=self.start, data_hora_fim=self.start + timedelta(hours=1))
        response = self.client.get('/api/disponibilidade/', {'data': self.start.date().isoformat(), 'barbeiro_id': self.barber.pk, 'servicos': self.service.pk})
        self.assertNotIn('10:00', response.data['horarios_disponiveis'])
        response = self.client.post('/api/agendamentos/', self.payload(), format='json')
        self.assertEqual(response.status_code, 400)

    def test_waitlist_receives_occupied_slots_and_rejects_duplicate_services(self):
        self.book()
        query = {'data': self.start.date().isoformat(), 'barbeiro_id': self.barber.pk, 'servicos': self.service.pk}
        response = self.client.get('/api/disponibilidade/', query)
        self.assertIn('10:00', response.data['horarios_ocupados'])
        query['servicos'] = f'{self.service.pk},{self.service.pk}'
        self.assertEqual(self.client.get('/api/disponibilidade/', query).status_code, 400)

    def test_blocked_customer_and_client_payment_forgery_are_rejected(self):
        response = self.client.post('/api/agendamentos/', self.payload(status_pagamento='PAGO'), format='json')
        self.assertEqual(response.status_code, 403)
        self.customer.status = 'BLOQUEADO'
        self.customer.save()
        self.assertEqual(self.client.post('/api/agendamentos/', self.payload(), format='json').status_code, 403)

    def test_company_cancellation_deadline_is_preserved(self):
        pk = self.book()
        Agendamento.objects.filter(pk=pk).update(data_hora_inicio=timezone.now()+timedelta(hours=2))
        self.assertEqual(self.client.patch(f'/api/agendamentos/{pk}/cancelar/').status_code, 400)
        self.assertEqual(Agendamento.objects.get(pk=pk).status, 'PENDENTE')

    def test_completion_payment_and_loyalty_do_not_recalculate_history(self):
        pk = self.book()
        self.client.force_authenticate(self.manager)
        url = f'/api/agendamentos/{pk}/'
        self.assertEqual(self.client.patch(url, {'status': 'CONFIRMADO'}, format='json').status_code, 200)
        Agendamento.objects.filter(pk=pk).update(data_hora_inicio=timezone.now()-timedelta(hours=1))
        response = self.client.patch(url, {'status': 'CONCLUIDO', 'status_pagamento': 'PENDENTE'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(CartaoFidelidade.objects.get(cliente=self.customer).qtd_selos_atual, 1)
        self.barber.taxa_comissao = Decimal('90')
        self.barber.save()
        response = self.client.patch(url, {'status': 'CONCLUIDO', 'status_pagamento': 'PAGO'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        appointment = Agendamento.objects.get(pk=pk)
        self.assertEqual(appointment.valor_comissao, Decimal('20.00'))
        self.assertEqual(appointment.status_pagamento, 'PAGO')
        self.assertEqual(CartaoFidelidade.objects.get(cliente=self.customer).qtd_selos_atual, 1)

    def test_signup_without_company_and_subscription_routes_survive(self):
        self.client.force_authenticate(None)
        response = self.client.post('/api/clientes/registrar/', {'nome': 'Cliente Novo', 'email': 'new@example.test', 'senha': 'IntegrationTest!2026', 'empresa_id': None}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIsNone(response.data['user']['empresa'])
        for url in ('/api/saas/registrar/', '/api/whatsapp/status/', '/api/fidelidade/meu-cartao/', '/api/assinaturas/webhook/'):
            self.assertIsNotNone(resolve(url).func)

    def test_tenant_settings_remain_available_but_subscription_is_readonly(self):
        self.client.force_authenticate(self.manager)
        response = self.client.patch(f'/api/empresas/{self.company.pk}/', {'fidelidade_meta': 5, 'horas_limite_cancelamento': 12, 'assinatura_ativa': True}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.company.refresh_from_db()
        self.assertEqual(self.company.fidelidade_meta, 5)
        self.assertEqual(self.company.horas_limite_cancelamento, 12)
        self.assertFalse(self.company.assinatura_ativa)
