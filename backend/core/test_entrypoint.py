"""Testa o fluxo shell com comandos simulados, sem banco ou servidor reais."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class EntrypointTests(unittest.TestCase):
    def setUp(self):
        if os.name == 'nt':
            shell = Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Git/bin/bash.exe'
            self.shell = str(shell) if shell.is_file() else None
        else:
            self.shell = shutil.which('sh')
        if not self.shell:
            self.skipTest('Shell POSIX não disponível; executar estes testes em Linux ou com Git Bash.')
        self.temp = tempfile.TemporaryDirectory(prefix='salaopro-entrypoint-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.log = self.root / 'commands.log'
        self.entrypoint = Path(__file__).resolve().parents[1] / 'entrypoint.sh'
        self.env = os.environ.copy()
        self.env.update({
            'PATH': str(self.bin) + os.pathsep + self.env.get('PATH', ''),
            'ENTRYPOINT_CALL_LOG': self.log.as_posix(),
            'MEDIA_DIRECTORY': (self.root / 'media').as_posix(),
            'RUN_MIGRATIONS': '1',
            'MOCK_FAIL_COMMAND': '',
        })
        for name in ('python', 'gunicorn'):
            path = self.bin / name
            path.write_text(
                '#!/bin/sh\n'
                f'printf "%s\\n" "{name} $*" >> "$ENTRYPOINT_CALL_LOG"\n'
                'if [ -n "$MOCK_FAIL_COMMAND" ] && [ "$*" = "$MOCK_FAIL_COMMAND" ]; then exit 17; fi\n',
                encoding='utf-8', newline='\n',
            )
            path.chmod(0o755)

    def run_entrypoint(self, args=None, **environment):
        env = {**self.env, **environment}
        args = ['gunicorn', 'core.wsgi:application', '--workers', '3'] if args is None else args
        result = subprocess.run(
            [self.shell, self.entrypoint.as_posix(), *args], env=env,
            cwd=self.root, capture_output=True, text=True, timeout=20,
        )
        commands = self.log.read_text(encoding='utf-8').splitlines() if self.log.exists() else []
        return result, commands

    def test_success_starts_server_only_after_migration_and_statics(self):
        result, commands = self.run_entrypoint()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(commands, [
            'python manage.py check', 'python manage.py migrate --noinput',
            'python manage.py collectstatic --noinput', 'gunicorn core.wsgi:application --workers 3',
        ])

    def test_failed_migration_prevents_server_start(self):
        result, commands = self.run_entrypoint(MOCK_FAIL_COMMAND='manage.py migrate --noinput')
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertEqual(commands, ['python manage.py check', 'python manage.py migrate --noinput'])

    def test_failed_static_collection_prevents_server_start(self):
        result, commands = self.run_entrypoint(MOCK_FAIL_COMMAND='manage.py collectstatic --noinput')
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertEqual(commands[-1], 'python manage.py collectstatic --noinput')

    def test_disabled_migrations_check_schema_before_starting(self):
        result, commands = self.run_entrypoint(RUN_MIGRATIONS='0')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('python manage.py migrate --check', commands)
        self.assertNotIn('python manage.py migrate --noinput', commands)

    def test_pending_migrations_prevent_start_when_auto_migration_disabled(self):
        result, commands = self.run_entrypoint(RUN_MIGRATIONS='0', MOCK_FAIL_COMMAND='manage.py migrate --check')
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertEqual(commands[-1], 'python manage.py migrate --check')

    def test_invalid_flag_fails_before_any_management_command(self):
        result, commands = self.run_entrypoint(RUN_MIGRATIONS='invalid')
        self.assertEqual(result.returncode, 64, result.stderr)
        self.assertEqual(commands, [])

    def test_migration_plan_does_not_apply_migrations_implicitly(self):
        result, commands = self.run_entrypoint(args=['python', 'manage.py', 'migrate', '--plan'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(commands, ['python manage.py migrate --plan'])

    def test_missing_command_is_rejected(self):
        result, commands = self.run_entrypoint(args=[])
        self.assertEqual(result.returncode, 64, result.stderr)
        self.assertEqual(commands, [])
