from datetime import datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch
from django.core import mail
from django.db import transaction
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase
from apps.accounts.models import Usuario
from apps.tenants.models import Empresa
from apps.agenda.models import Servico, Agendamento


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class BusinessRulesTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = Empresa.objects.create(nome='A', slug='a', intervalo_almoco_inicio=time(12), intervalo_almoco_fim=time(13))
        cls.other_company = Empresa.objects.create(nome='B', slug='b')
        cls.customer = Usuario.objects.create_user(username='cliente@example.com', email='cliente@example.com', password='StrongPassword!786')
        cls.other_customer = Usuario.objects.create_user(username='outro@example.com', password='StrongPassword!786')
        cls.manager = Usuario.objects.create_user(username='gestor', tipo='ADMINISTRADOR', empresa=cls.company)
        cls.barber = Usuario.objects.create_user(username='barbeiro', tipo='PROFISSIONAL', empresa=cls.company, taxa_comissao=Decimal('40'))
        cls.other_barber = Usuario.objects.create_user(username='barbeiro2', tipo='PROFISSIONAL', empresa=cls.other_company)
        cls.service = Servico.objects.create(empresa=cls.company, nome='Corte', preco=Decimal('50'), duracao_minutos=30)
        cls.other_service = Servico.objects.create(empresa=cls.other_company, nome='Corte', preco=Decimal('60'), duracao_minutos=45)
        cls.start = timezone.make_aware(datetime.combine(timezone.localdate() + timedelta(days=2), time(10)))

    def setUp(self):
        self.client.force_authenticate(self.customer)

    def payload(self, **changes):
        data = {'profissional': self.barber.pk, 'servicos': [self.service.pk], 'data_hora_inicio': self.start.isoformat()}
        data.update(changes)
        return data

    def book(self, **changes):
        response = self.client.post('/api/agendamentos/', self.payload(**changes), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data['id']

    def test_booking_and_end_time(self):
        pk = self.book()
        appointment = Agendamento.objects.get(pk=pk)
        self.assertEqual(appointment.cliente, self.customer)
        self.assertEqual(appointment.empresa, self.company)
        self.assertEqual(appointment.status, 'PENDENTE')
        self.assertEqual(appointment.data_hora_fim, self.start + timedelta(minutes=30))

    def test_conflict_is_rechecked_at_write(self):
        self.book()
        for start in (self.start, self.start + timedelta(minutes=15)):
            with self.subTest(start=start):
                response = self.client.post('/api/agendamentos/', self.payload(data_hora_inicio=start.isoformat()), format='json')
                self.assertEqual(response.status_code, 400)
        self.book(data_hora_inicio=(self.start + timedelta(minutes=30)).isoformat())

    def test_invalid_selection(self):
        for payload in (
            {'servicos': []}, {'servicos': [self.other_service.pk]},
            {'servicos': [self.service.pk, self.service.pk]}, {'profissional': self.customer.pk},
            {'profissional': self.other_barber.pk}, {'status': 'CONCLUIDO'},
            {'cliente': self.other_customer.pk},
        ):
            with self.subTest(payload=payload):
                response = self.client.post('/api/agendamentos/', self.payload(**payload), format='json')
                self.assertIn(response.status_code, (400, 403), response.data)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_past_lunch_and_closing_rejected(self):
        for start in (self.start - timedelta(days=4), self.start.replace(hour=12), self.start.replace(hour=18, minute=45)):
            with self.subTest(start=start):
                response = self.client.post('/api/agendamentos/', self.payload(data_hora_inicio=start.isoformat()), format='json')
                self.assertEqual(response.status_code, 400, response.data)

    def test_inactive_service_professional_company(self):
        for obj, field in ((self.service, 'ativo'), (self.barber, 'is_active'), (self.company, 'ativo')):
            with self.subTest(model=type(obj).__name__):
                setattr(obj, field, False)
                obj.save()
                response = self.client.post('/api/agendamentos/', self.payload(), format='json')
                self.assertEqual(response.status_code, 400)
                setattr(obj, field, True)
                obj.save()

    def test_customer_isolation_and_permissions(self):
        pk = self.book()
        self.assertEqual(self.client.patch(f'/api/agendamentos/{pk}/', {'status': 'CONFIRMADO'}, format='json').status_code, 403)
        self.assertEqual(self.client.patch(f'/api/agendamentos/{pk}/', {'cliente': self.other_customer.pk}, format='json').status_code, 403)
        self.assertEqual(self.client.delete(f'/api/agendamentos/{pk}/').status_code, 405)
        self.client.force_authenticate(self.other_customer)
        self.assertEqual(self.client.get('/api/agendamentos/').data, [])
        self.assertEqual(self.client.patch(f'/api/agendamentos/{pk}/cancelar/').status_code, 404)

    def test_cancel_frees_slot(self):
        pk = self.book()
        url = '/api/disponibilidade/'
        params = {'data': self.start.date().isoformat(), 'barbeiro_id': self.barber.pk, 'servicos': str(self.service.pk)}
        self.assertNotIn('10:00', self.client.get(url, params).data['horarios_disponiveis'])
        self.assertEqual(self.client.patch(f'/api/agendamentos/{pk}/cancelar/').status_code, 200)
        self.assertIn('10:00', self.client.get(url, params).data['horarios_disponiveis'])
        self.assertEqual(self.client.patch(f'/api/agendamentos/{pk}/cancelar/').status_code, 400)
        self.book()

    def test_availability_validates_inputs_and_tenant(self):
        params = {'data': self.start.date().isoformat(), 'barbeiro_id': self.barber.pk, 'servicos': str(self.other_service.pk)}
        self.assertEqual(self.client.get('/api/disponibilidade/', params).status_code, 400)
        params['servicos'] = str(self.service.pk)
        params['data'] = (timezone.localdate() - timedelta(days=1)).isoformat()
        self.assertEqual(self.client.get('/api/disponibilidade/', params).data['horarios_disponiveis'], [])
        self.assertEqual(self.client.get('/api/disponibilidade/', {'barbeiro_id': 'abc'}).status_code, 400)

    def test_public_catalog_has_no_private_user_fields(self):
        self.client.force_authenticate(None)
        data = self.client.get('/api/usuarios/').data
        for user in data:
            self.assertFalse(set(user) & {'email', 'password', 'username', 'is_staff', 'taxa_comissao', 'ip_aceite_termos'})
        for endpoint, pk in (('usuarios', self.barber.pk), ('servicos', self.service.pk)):
            self.assertEqual(self.client.patch(f'/api/{endpoint}/{pk}/', {}, format='json').status_code, 401)
            self.assertEqual(self.client.post(f'/api/{endpoint}/', {}, format='json').status_code, 401)

    def test_manager_cannot_bypass_tenant_with_query_parameter(self):
        self.client.force_authenticate(self.manager)
        for endpoint, pk in (('usuarios', self.other_barber.pk), ('servicos', self.other_service.pk)):
            response = self.client.patch(f'/api/{endpoint}/{pk}/?empresa_id={self.other_company.pk}', {'ativo': False}, format='json')
            self.assertEqual(response.status_code, 404, response.data)
        data = self.client.get('/api/usuarios/', {'empresa_id': self.other_company.pk}).data
        self.assertNotIn('email', data[0])
        response = self.client.patch(f'/api/usuarios/{self.barber.pk}/', {'is_staff': True}, format='json')
        self.assertEqual(response.status_code, 200)
        self.barber.refresh_from_db()
        self.assertFalse(self.barber.is_staff)

    def test_client_cannot_edit_company_or_catalog(self):
        self.customer.empresa = self.company
        self.customer.save()
        for endpoint, pk in (('empresas', self.company.pk), ('servicos', self.service.pk), ('usuarios', self.barber.pk)):
            self.assertEqual(self.client.patch(f'/api/{endpoint}/{pk}/', {'nome': 'changed'}, format='json').status_code, 403)

    def test_manager_reschedule_recalculates_end_and_rejects_overlap(self):
        pk = self.book()
        other = self.book(data_hora_inicio=(self.start + timedelta(hours=1)).isoformat())
        self.client.force_authenticate(self.manager)
        url = f'/api/agendamentos/{pk}/'
        self.assertEqual(self.client.patch(url, {'data_hora_inicio': (self.start + timedelta(hours=1)).isoformat()}, format='json').status_code, 400)
        new_start = self.start + timedelta(hours=4)
        self.assertEqual(self.client.patch(url, {'data_hora_inicio': new_start.isoformat()}, format='json').status_code, 200)
        self.assertEqual(Agendamento.objects.get(pk=pk).data_hora_fim, new_start + timedelta(minutes=30))

    def test_financial_transition_and_snapshot(self):
        pk = self.book()
        self.client.force_authenticate(self.manager)
        url = f'/api/agendamentos/{pk}/'
        self.assertEqual(self.client.patch(url, {'status': 'CONCLUIDO'}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(url, {'status': 'CONFIRMADO'}, format='json').status_code, 200)
        self.assertEqual(self.client.patch(url, {'status': 'CONCLUIDO'}, format='json').status_code, 400)
        Agendamento.objects.filter(pk=pk).update(data_hora_inicio=timezone.now() - timedelta(hours=1), data_hora_fim=timezone.now())
        self.assertEqual(self.client.patch(url, {'status': 'CONCLUIDO'}, format='json').status_code, 200)
        appointment = Agendamento.objects.get(pk=pk)
        self.assertEqual(appointment.valor_total, Decimal('50.00'))
        self.assertEqual(appointment.valor_comissao, Decimal('20.00'))
        self.assertEqual(appointment.lucro_liquido, Decimal('30.00'))
        self.barber.taxa_comissao = Decimal('80')
        self.barber.save()
        self.assertEqual(self.client.patch(url, {'status': 'CONCLUIDO'}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(f'{url}cancelar/').status_code, 400)
        appointment.refresh_from_db()
        self.assertEqual(appointment.valor_comissao, Decimal('20.00'))
        response = self.client.get('/api/financas/dashboard/')
        self.assertEqual(response.data['faturamento_bruto'], 50.0)
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get('/api/financas/dashboard/').status_code, 403)

    def test_email_only_after_commit_with_services(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            self.book()
            self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Corte', mail.outbox[0].body)

    def test_failed_transaction_does_not_send_email(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            try:
                with transaction.atomic():
                    self.book()
                    raise RuntimeError('rollback')
            except RuntimeError:
                pass
        self.assertEqual(callbacks, [])
        self.assertEqual(Agendamento.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_registration_validation(self):
        self.client.force_authenticate(None)
        endpoint = '/api/clientes/registrar/'
        for data in ({'nome': '   ', 'email': 'a@example.com', 'senha': 'SomeStrongPassword987!'},
                     {'nome': 'Teste', 'email': 'invalid', 'senha': 'SomeStrongPassword987!'},
                     {'nome': 'Teste', 'email': 'new@example.com', 'senha': '123'},
                     {'nome': 'Teste', 'email': 'CLIENTE@EXAMPLE.COM', 'senha': 'SomeStrongPassword987!'}):
            self.assertEqual(self.client.post(endpoint, data, format='json').status_code, 400)
        response = self.client.post(endpoint, {'nome': 'Teste Novo', 'email': 'NOVO@example.com', 'senha': 'SomeStrongPassword987!'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Usuario.objects.get(username='novo@example.com').tipo, 'CLIENTE')

    def test_refresh_rotation_revokes_previous_token(self):
        self.client.force_authenticate(None)
        response = self.client.post('/api/token/', {'username': self.customer.username, 'password': 'StrongPassword!786'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        refresh = response.data['refresh']
        self.assertEqual(self.client.post('/api/token/refresh/', {'refresh': refresh}, format='json').status_code, 200)
        self.assertEqual(self.client.post('/api/token/refresh/', {'refresh': refresh}, format='json').status_code, 401)

    def test_audit_reports_legacy_inconsistency_without_mutation(self):
        from io import StringIO
        from django.core.management import call_command
        from django.core.management.base import CommandError
        pk = self.book()
        Agendamento.objects.filter(pk=pk).update(data_hora_fim=None)
        output = StringIO()
        with self.assertRaises(CommandError):
            call_command('auditar_agenda', fail_on_issues=True, stdout=output)
        self.assertIn(str(pk), output.getvalue())
        self.assertIsNone(Agendamento.objects.get(pk=pk).data_hora_fim)

    def test_email_failure_does_not_undo_booking(self):
        with patch('apps.agenda.signals.send_mail', side_effect=RuntimeError('SMTP unavailable')):
            with self.assertLogs('apps.agenda.signals', level='ERROR'):
                with self.captureOnCommitCallbacks(execute=True):
                    pk = self.book()
        self.assertTrue(Agendamento.objects.filter(pk=pk).exists())

    def test_professional_cannot_modify_coworker_appointment(self):
        pk = self.book()
        coworker = Usuario.objects.create_user(username='colega', tipo='PROFISSIONAL', empresa=self.company)
        self.client.force_authenticate(coworker)
        self.assertEqual(self.client.patch(f'/api/agendamentos/{pk}/', {'status': 'CONFIRMADO'}, format='json').status_code, 404)

    def test_manager_service_and_hours_validation(self):
        self.client.force_authenticate(self.manager)
        for data in ({'preco': '-1.00'}, {'duracao_minutos': 0}):
            self.assertEqual(self.client.patch(f'/api/servicos/{self.service.pk}/', data, format='json').status_code, 400)
        self.assertEqual(self.client.patch(f'/api/empresas/{self.company.pk}/', {'hora_fechamento': '08:00'}, format='json').status_code, 400)

    def test_django_admin_does_not_allow_tenant_staff_or_history_deletion(self):
        from django.contrib import admin
        from django.test import RequestFactory
        request = RequestFactory().get('/admin/')
        self.manager.is_staff = True
        request.user = self.manager
        for model in (Agendamento, Usuario, Empresa, Servico):
            self.assertFalse(admin.site._registry[model].has_view_permission(request))
            self.assertFalse(admin.site._registry[model].has_delete_permission(request))

    def test_registration_is_rate_limited_even_when_authenticated(self):
        from django.core.cache import cache
        from apps.accounts.views import AuthThrottle
        cache.clear()
        self.addCleanup(cache.clear)
        with patch.object(AuthThrottle, 'rate', '2/min', create=True):
            responses = [self.client.post('/api/clientes/registrar/', {}, format='json') for _ in range(3)]
        self.assertEqual([response.status_code for response in responses], [400, 400, 429])

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.db import connection, connections
from django.test import TransactionTestCase
from rest_framework.test import APIClient


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ConcurrentBookingTests(TransactionTestCase):
    def setUp(self):
        self.company = Empresa.objects.create(nome='Concorrência', slug='concorrencia')
        self.customer = Usuario.objects.create_user(username='cliente')
        self.barber = Usuario.objects.create_user(username='barbeiro', tipo='PROFISSIONAL', empresa=self.company)
        self.service = Servico.objects.create(empresa=self.company, nome='Corte', preco=Decimal('50'), duracao_minutos=30)
        self.start = timezone.make_aware(datetime.combine(timezone.localdate() + timedelta(days=2), time(10)))

    def test_two_simultaneous_requests_reserve_only_once(self):
        if connection.vendor == 'sqlite' and 'memory' in str(connection.settings_dict['NAME']):
            self.skipTest('Execute com TEST_DATABASE_NAME apontando para arquivo SQLite temporário.')
        barrier = Barrier(2)
        def reserve():
            try:
                client = APIClient()
                client.force_authenticate(Usuario.objects.get(pk=self.customer.pk))
                barrier.wait(timeout=10)
                response = client.post('/api/agendamentos/', {
                    'profissional': self.barber.pk, 'servicos': [self.service.pk],
                    'data_hora_inicio': self.start.isoformat(),
                }, format='json')
                return response.status_code
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(reserve)
            second = pool.submit(reserve)
            results = [first.result(timeout=30), second.result(timeout=30)]
        self.assertEqual(sorted(results), [201, 400])
        self.assertEqual(Agendamento.objects.count(), 1)
