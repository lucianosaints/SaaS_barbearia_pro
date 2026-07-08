import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.accounts.models import Usuario

def p(msg):
    print(f"[TEST MP] {msg}")

user = Usuario.objects.filter(email="ativo@qa.com").first()
if not user:
    # try getting any admin user that has an empresa
    user = Usuario.objects.filter(tipo='ADMINISTRADOR', empresa__isnull=False).first()

if not user:
    p("Nenhum usuario para teste")
    exit()

res = requests.post('http://127.0.0.1:8000/api/token/', data={"username": user.username, "password": "senha123"})
if res.status_code != 200:
    # Try another password or just print error
    p(f"Token error: {res.text}")
    
    # Let's bypass token by creating a token directly
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)
else:
    token = res.json().get('access')

res_mp = requests.post(
    'http://127.0.0.1:8000/api/assinaturas/criar-assinatura/', 
    headers={"Authorization": f"Bearer {token}"}
)

p(f"Status: {res_mp.status_code}")
p(f"Response: {res_mp.text}")
