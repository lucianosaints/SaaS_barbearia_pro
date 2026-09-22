import os
import runpy
from pathlib import Path
from unittest.mock import patch
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase


class DatabaseConfigurationTests(SimpleTestCase):
    def settings(self, **changes):
        environment = {
            'DJANGO_DEBUG': 'False',
            'DJANGO_SECRET_KEY': 'test-only-key-never-use-in-production-' + 'x' * 50,
            'DJANGO_ALLOWED_HOSTS': 'www.salaopro.site,salaopro.site',
            'DB_ENGINE': 'postgresql', 'DB_NAME': 'test_config',
            'DB_USER': 'test_config', 'DB_HOST': '127.0.0.1',
        }
        environment.update(changes)
        environment = {key: value for key, value in environment.items() if value is not None}
        with patch.dict(os.environ, environment, clear=True):
            return runpy.run_path(str(Path(__file__).with_name('settings.py')))

    def test_production_requires_explicit_database_engine(self):
        with self.assertRaises(ImproperlyConfigured):
            self.settings(DB_ENGINE=None)

    def test_production_cannot_fall_back_to_sqlite(self):
        with self.assertRaises(ImproperlyConfigured):
            self.settings(DB_ENGINE='sqlite')

    def test_missing_production_database_fields_fail_before_connecting(self):
        for field in ('DB_NAME', 'DB_USER', 'DB_HOST'):
            with self.subTest(field=field), self.assertRaises(ImproperlyConfigured):
                self.settings(**{field: ''})

    def test_local_postgresql_preserves_explicit_connection_settings(self):
        config = self.settings(DB_PORT='5544', DB_PASSWORD='unit-test-only')['DATABASES']['default']
        self.assertEqual(config['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(config['HOST'], '127.0.0.1')
        self.assertEqual(config['PORT'], '5544')
        self.assertEqual(config['OPTIONS']['connect_timeout'], 10)
        self.assertTrue(config['CONN_HEALTH_CHECKS'])

    def test_tls_certificate_and_connection_age_are_configurable(self):
        config = self.settings(DB_SSLMODE='verify-full', DB_SSLROOTCERT='/test/ca.crt', DB_CONN_MAX_AGE='0')['DATABASES']['default']
        self.assertEqual(config['OPTIONS']['sslrootcert'], '/test/ca.crt')
        self.assertEqual(config['OPTIONS']['sslmode'], 'verify-full')
        self.assertEqual(config['CONN_MAX_AGE'], 0)

    def test_development_still_supports_sqlite(self):
        config = self.settings(DJANGO_DEBUG='True', DB_ENGINE=None)['DATABASES']['default']
        self.assertEqual(config['ENGINE'], 'django.db.backends.sqlite3')

    def test_production_paths_match_existing_nginx(self):
        config = self.settings(MEDIA_DIRECTORY='/app/media')
        self.assertEqual(config['ADMIN_URL'], 'painel-master/')
        self.assertEqual(config['STATIC_URL'], '/estaticos/')
        self.assertEqual(config['MEDIA_URL'], '/arquivos/')
        self.assertEqual(config['MEDIA_ROOT'], Path('/app/media'))

    def test_admin_resolves_and_reverses_under_both_environments(self):
        from types import ModuleType
        from django.urls import resolve, reverse

        for debug in ('True', 'False'):
            config = self.settings(DJANGO_DEBUG=debug)
            with self.subTest(debug=debug), self.settings_override(config):
                urls = ModuleType('test_routes_' + debug)
                urls.urlpatterns = runpy.run_path(str(Path(__file__).with_name('urls.py')))['urlpatterns']
                login = '/' + config['ADMIN_URL'] + 'login/'
                self.assertEqual(reverse('admin:login', urlconf=urls), login)
                self.assertEqual(resolve(login, urlconf=urls).view_name, 'admin:login')

    def settings_override(self, config):
        from django.test import override_settings
        return override_settings(ADMIN_URL=config['ADMIN_URL'])
