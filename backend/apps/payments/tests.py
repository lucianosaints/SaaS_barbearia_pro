import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import override_settings
from rest_framework.test import APITestCase

from apps.accounts.models import Usuario
from apps.tenants.models import Empresa
from .models import CobrancaAssinatura


@override_settings(MERCADOPAGO_ACCESS_TOKEN='TEST-token-never-real')
class MercadoPagoHomologationTests(APITestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome='Pagamento Teste', slug='pagamento-teste')
        self.admin = Usuario.objects.create_user(
            username='admin-pagamento', email='admin@example.test', password='Test!12345',
            tipo='ADMINISTRADOR', empresa=self.empresa,
        )
        self.profissional = Usuario.objects.create_user(
            username='pro-pagamento', email='pro@example.test', password='Test!12345',
            tipo='PROFISSIONAL', empresa=self.empresa,
        )

    @patch.dict('os.environ', {'PERMITIR_PAGAMENTOS': 'true'})
    @patch('services.mercado_pago_service.mercadopago.SDK')
    def test_admin_creates_tracked_charge_with_opaque_reference(self, sdk_class):
        sdk_class.return_value.payment.return_value.create.return_value = {
            'status': 201,
            'response': {'id': 123, 'point_of_interaction': {'transaction_data': {'qr_code': 'safe-code'}}},
        }
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/assinaturas/criar-assinatura/', {'meses': 3}, format='json')
        self.assertEqual(response.status_code, 201)
        charge = CobrancaAssinatura.objects.get()
        self.assertEqual(charge.valor, Decimal('149.97'))
        payload = sdk_class.return_value.payment.return_value.create.call_args.args[0]
        self.assertEqual(payload['external_reference'], str(charge.external_reference))

    @patch.dict('os.environ', {'PERMITIR_PAGAMENTOS': 'true'})
    @patch('services.mercado_pago_service.mercadopago.SDK')
    def test_admin_can_pay_for_two_months(self, sdk_class):
        sdk_class.return_value.payment.return_value.create.return_value = {
            'status': 201,
            'response': {'id': 124, 'point_of_interaction': {'transaction_data': {'qr_code': 'safe-code'}}},
        }
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/assinaturas/criar-assinatura/', {'meses': 2}, format='json')
        self.assertEqual(response.status_code, 201)
        charge = CobrancaAssinatura.objects.get()
        self.assertEqual(charge.meses, 2)
        self.assertEqual(charge.valor, Decimal('99.98'))

    @patch.dict('os.environ', {'PERMITIR_PAGAMENTOS': 'true'})
    def test_professional_cannot_create_subscription_charge(self):
        self.client.force_authenticate(self.profissional)
        response = self.client.post('/api/assinaturas/criar-assinatura/', {'meses': 1}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(CobrancaAssinatura.objects.exists())

    @patch.dict('os.environ', {'PERMITIR_PAGAMENTOS': 'true'})
    def test_invalid_month_count_is_rejected(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/assinaturas/criar-assinatura/', {'meses': 99}, format='json')
        self.assertEqual(response.status_code, 400)

    @patch.dict('os.environ', {'PERMITIR_PAGAMENTOS': 'False'})
    def test_charge_creation_stays_blocked_until_homologation(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/assinaturas/criar-assinatura/', {'meses': 1}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(CobrancaAssinatura.objects.exists())

    @patch('apps.payments.views.mercadopago.SDK')
    def test_webhook_is_idempotent(self, sdk_class):
        charge = CobrancaAssinatura.objects.create(
            empresa=self.empresa, meses=1, valor=Decimal('49.99')
        )
        sdk_class.return_value.payment.return_value.get.return_value = {
            'status': 200,
            'response': {
                'status': 'approved', 'external_reference': str(charge.external_reference),
                'transaction_amount': 49.99, 'currency_id': 'BRL',
            },
        }
        payload = {'type': 'payment', 'data': {'id': 'mp-123'}}
        first = self.client.post('/api/assinaturas/webhook/', payload, format='json')
        self.empresa.refresh_from_db()
        first_due_date = self.empresa.data_vencimento_assinatura
        second = self.client.post('/api/assinaturas/webhook/', payload, format='json')
        self.empresa.refresh_from_db()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first_due_date, datetime.date.today() + datetime.timedelta(days=30))
        self.assertEqual(self.empresa.data_vencimento_assinatura, first_due_date)

    @patch('apps.payments.views.mercadopago.SDK')
    def test_webhook_rejects_wrong_amount(self, sdk_class):
        charge = CobrancaAssinatura.objects.create(
            empresa=self.empresa, meses=1, valor=Decimal('49.99')
        )
        sdk_class.return_value.payment.return_value.get.return_value = {
            'status': 200,
            'response': {
                'status': 'approved', 'external_reference': str(charge.external_reference),
                'transaction_amount': 1, 'currency_id': 'BRL',
            },
        }
        response = self.client.post('/api/assinaturas/webhook/', {'data': {'id': 'mp-low'}}, format='json')
        charge.refresh_from_db()
        self.empresa.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(charge.status, 'REJEITADA')
        self.assertFalse(self.empresa.assinatura_ativa)


class WahaAndSmtpHomologationTests(APITestCase):
    @override_settings(WAHA_API_URL='http://waha:3000', WAHA_API_KEY='test-key')
    @patch('services.waha_service.requests.post')
    def test_waha_uses_internal_url_key_session_and_timeout(self, post):
        from services.waha_service import enviar_mensagem_whatsapp
        post.return_value = Mock(ok=True)
        self.assertTrue(enviar_mensagem_whatsapp('(11) 99999-0000', 'Teste', 'tenant_7'))
        args, kwargs = post.call_args
        self.assertEqual(args[0], 'http://waha:3000/api/sendText?session=tenant_7')
        self.assertEqual(kwargs['headers']['X-Api-Key'], 'test-key')
        self.assertEqual(kwargs['json']['chatId'], '5511999990000@c.us')
        self.assertEqual(kwargs['timeout'], 10)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='alertas@example.test', EMAIL_ALERT_TO=['ops@example.test'],
    )
    @patch('apps.agenda.management.commands.check_waha_status.requests.get')
    def test_disconnected_waha_sends_smtp_alert(self, get):
        from django.core import mail
        from django.core.management import call_command
        get.return_value = Mock(ok=False, status_code=503, text='unavailable')
        call_command('check_waha_status')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['ops@example.test'])
