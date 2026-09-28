from django.core.cache import cache
from django.core import mail
from django.test import override_settings
from rest_framework.test import APIClient, APITestCase
from urllib.parse import parse_qs, urlparse

from apps.accounts.models import Usuario
from apps.tenants.models import Empresa


class SecurityHardeningTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.company = Empresa.objects.create(
            nome='Segura', slug='segura', cnpj='00000000000100',
            chave_pix='pix@example.test', beneficiario_pix='Titular Privado',
            ativo=True, em_trial=True,
        )
        self.manager = Usuario.objects.create_user(
            username='manager@example.test', email='manager@example.test',
            password='SecurityTest!2026', tipo='ADMINISTRADOR', empresa=self.company,
        )
        self.professional = Usuario.objects.create_user(
            username='professional@example.test', password='SecurityTest!2026',
            tipo='PROFISSIONAL', empresa=self.company,
        )

    def test_public_company_response_contains_no_private_or_billing_fields(self):
        response = self.client.get('/api/empresas/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data[0]), {'id', 'nome', 'slug'})
        response = self.client.get('/api/empresas/por-slug/segura/')
        self.assertEqual(set(response.data), {'id', 'nome', 'slug'})

    def test_manager_still_receives_full_company_configuration(self):
        self.client.force_authenticate(self.manager)
        response = self.client.get(f'/api/empresas/{self.company.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['chave_pix'], self.company.chave_pix)

    def test_logout_revokes_current_access_token_immediately(self):
        login = self.client.post('/api/token/', {
            'username': self.manager.username, 'password': 'SecurityTest!2026'
        }, format='json')
        authenticated = APIClient()
        authenticated.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        self.assertEqual(authenticated.get('/api/usuarios/me/').status_code, 200)
        response = authenticated.post('/api/logout/', {'refresh_token': login.data['refresh']}, format='json')
        self.assertEqual(response.status_code, 205)
        self.assertEqual(authenticated.get('/api/usuarios/me/').status_code, 401)

    def test_registration_does_not_confirm_that_email_exists(self):
        response = self.client.post('/api/clientes/registrar/', {
            'nome': 'Outro Nome', 'email': self.manager.email,
            'senha': 'AnotherStrong!2026', 'telefone': '11999999999',
            'aceitou_termos': True,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('existe', str(response.data).casefold())
        self.assertIn('não foi possível concluir', str(response.data).casefold())

    def test_registration_requires_terms_and_records_acceptance(self):
        payload = {
            'nome': 'Cliente LGPD', 'email': 'lgpd@example.test',
            'senha': 'PrivacyTest!2026', 'telefone': '11999999999',
        }
        denied = self.client.post('/api/clientes/registrar/', payload, format='json')
        self.assertEqual(denied.status_code, 400)
        self.assertIn('aceitou_termos', denied.data)

        payload['aceitou_termos'] = True
        accepted = self.client.post('/api/clientes/registrar/', payload, format='json', REMOTE_ADDR='10.20.30.40')
        self.assertEqual(accepted.status_code, 201, accepted.data)
        user = Usuario.objects.get(email='lgpd@example.test')
        self.assertTrue(user.aceitou_termos)
        self.assertIsNotNone(user.data_aceite_termos)
        self.assertEqual(user.ip_aceite_termos, '10.20.30.40')

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        PUBLIC_FRONTEND_URL='https://www.salaopro.site',
        PASSWORD_RESET_TIMEOUT=1800,
    )
    def test_password_reset_email_is_neutral_single_use_and_revokes_sessions(self):
        login = self.client.post('/api/token/', {
            'username': self.manager.username, 'password': 'SecurityTest!2026'
        }, format='json')
        old_access = APIClient()
        old_access.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        requested = self.client.post('/api/senha/recuperar/', {'email': self.manager.email}, format='json')
        self.assertEqual(requested.status_code, 200)
        self.assertNotIn('existe', requested.data['detail'].casefold())
        self.assertEqual(len(mail.outbox), 1)
        link = next(line for line in mail.outbox[0].body.splitlines() if line.startswith('https://'))
        query = parse_qs(urlparse(link).query)
        payload = {
            'uid': query['uid'][0], 'token': query['token'][0],
            'nova_senha': 'NewSecurity!2027', 'confirmar_senha': 'NewSecurity!2027',
        }
        changed = self.client.post('/api/senha/redefinir/', payload, format='json')
        self.assertEqual(changed.status_code, 200, changed.data)
        self.assertEqual(old_access.get('/api/usuarios/me/').status_code, 401)
        self.assertEqual(self.client.post('/api/token/refresh/', {'refresh': login.data['refresh']}, format='json').status_code, 401)
        self.assertEqual(self.client.post('/api/token/', {'username': self.manager.username, 'password': 'SecurityTest!2026'}, format='json').status_code, 401)
        self.assertEqual(self.client.post('/api/token/', {'username': self.manager.username, 'password': 'NewSecurity!2027'}, format='json').status_code, 200)
        self.assertEqual(self.client.post('/api/senha/redefinir/', payload, format='json').status_code, 400)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_unknown_email_has_same_response(self):
        response = self.client.post('/api/senha/recuperar/', {'email': 'unknown@example.test'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_rejects_invalid_link_and_weak_password(self):
        invalid = self.client.post('/api/senha/redefinir/', {
            'uid': 'invalid', 'token': 'invalid',
            'nova_senha': 'Weak!1aa', 'confirmar_senha': 'Weak!1aa',
        }, format='json')
        self.assertEqual(invalid.status_code, 400)

    def test_waha_requires_tenant_manager(self):
        self.client.force_authenticate(self.professional)
        self.assertEqual(self.client.get('/api/whatsapp/status/').status_code, 403)

    def test_manager_created_team_member_defaults_to_professional(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post('/api/usuarios/', {
            'username': 'team@example.test', 'email': 'team@example.test',
            'first_name': 'Equipe', 'password': 'TeamMember!2026',
            'telefone': '11999999999', 'is_active': True,
        }, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        member = Usuario.objects.get(pk=response.data['id'])
        self.assertEqual(member.tipo, 'PROFISSIONAL')
        self.assertEqual(member.empresa, self.company)

    def test_cors_allowlist_and_clickjacking_header(self):
        denied = self.client.get('/api/empresas/', HTTP_ORIGIN='https://evil.example')
        allowed = self.client.get('/api/empresas/', HTTP_ORIGIN='http://127.0.0.1:3000')
        self.assertNotIn('Access-Control-Allow-Origin', denied)
        self.assertEqual(allowed['Access-Control-Allow-Origin'], 'http://127.0.0.1:3000')
        self.assertEqual(denied['X-Frame-Options'], 'DENY')

    @override_settings(REST_FRAMEWORK={
        'DEFAULT_AUTHENTICATION_CLASSES': ('apps.accounts.authentication.RevocableJWTAuthentication',),
        'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
        'DEFAULT_THROTTLE_RATES': {
            'auth_ip': '100/min', 'auth_account': '1/min',
            'anon': '100/min', 'user': '1000/day', 'fila_espera': '100/min',
        },
    })
    def test_login_account_limit_applies_across_source_ips(self):
        first = self.client.post('/api/token/', {'username': 'target', 'password': 'wrong'}, REMOTE_ADDR='10.0.0.1')
        second = self.client.post('/api/token/', {'username': 'target', 'password': 'wrong'}, REMOTE_ADDR='10.0.0.2')
        self.assertEqual(first.status_code, 401)
        self.assertEqual(second.status_code, 429)

    @override_settings(REST_FRAMEWORK={
        'DEFAULT_AUTHENTICATION_CLASSES': ('apps.accounts.authentication.RevocableJWTAuthentication',),
        'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
        'DEFAULT_THROTTLE_RATES': {
            'auth_ip': '1/min', 'auth_account': '100/min',
            'anon': '100/min', 'user': '1000/day', 'fila_espera': '100/min',
        },
    })
    def test_login_ip_limit_applies_across_accounts(self):
        first = self.client.post('/api/token/', {'username': 'one', 'password': 'wrong'}, REMOTE_ADDR='10.0.0.3')
        second = self.client.post('/api/token/', {'username': 'two', 'password': 'wrong'}, REMOTE_ADDR='10.0.0.3')
        self.assertEqual(first.status_code, 401)
        self.assertEqual(second.status_code, 429)
