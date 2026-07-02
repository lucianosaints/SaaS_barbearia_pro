import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from apps.agenda.views import AgendamentoViewSet
from apps.accounts.models import Usuario

try:
    factory = APIRequestFactory()
    request = factory.get('/api/agendamentos/', {'data_hora_inicio': '2026-07-02', 'barbeiro': '1'})
    # Pega o usuário cliente (ex: luciano) que provavelmente não tem empresa
    cliente = Usuario.objects.filter(tipo='CLIENTE').first()
    force_authenticate(request, user=cliente)
    
    view = AgendamentoViewSet.as_view({'get': 'list'})
    response = view(request)
    print("Status Code:", response.status_code)
    print("Data:", response.data)
except Exception as e:
    import traceback
    print("--- TRACEBACK ---", file=sys.stderr)
    traceback.print_exc()
    print("-----------------", file=sys.stderr)
