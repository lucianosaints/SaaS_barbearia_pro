import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import RequestFactory
from apps.agenda.views import obter_disponibilidade
from django.contrib.auth.models import AnonymousUser

try:
    rf = RequestFactory()
    request = rf.get('/api/disponibilidade/', {'data': '2026-07-12', 'barbeiro_id': '1', 'servicos': '2'})
    request.user = AnonymousUser()
    response = obter_disponibilidade(request)
    print("Status Code:", response.status_code)
    print("Data:", response.data)
except Exception as e:
    import traceback
    print("--- TRACEBACK ---", file=sys.stderr)
    traceback.print_exc()
    print("-----------------", file=sys.stderr)
