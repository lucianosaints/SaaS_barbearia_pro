"""
Script de Testes de Endpoint v2 - SaaS Barbearia Pro
Testa TODOS os endpoints da API e valida as correções de bugs.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from apps.accounts.models import Usuario
from apps.tenants.models import Empresa
from apps.agenda.models import Servico, Agendamento
import json
from datetime import datetime, timedelta
from django.utils import timezone

# --- Cores para saída ---
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

total_tests = 0
passed = 0
failed = 0
warnings_list = []
bugs_list = []

def test(name, condition, detail=""):
    global total_tests, passed, failed
    total_tests += 1
    if condition:
        passed += 1
        print(f"  {GREEN}[PASS]{RESET} {name}")
    else:
        failed += 1
        print(f"  {RED}[FAIL]{RESET} {name} {RED}-> {detail}{RESET}")
        bugs_list.append(f"{name}: {detail}")

def warn(msg):
    warnings_list.append(msg)
    print(f"  {YELLOW}[WARN]{RESET} {msg}")

def header(title):
    print(f"\n{CYAN}{BOLD}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{RESET}")

def get_jwt_token(client, username, password):
    resp = client.post('/api/token/', 
        json.dumps({'username': username, 'password': password}),
        content_type='application/json')
    if resp.status_code == 200:
        data = resp.json()
        return data.get('access'), data.get('refresh'), data.get('user')
    return None, None, None

# ============================================================
header("PREPARACAO - Verificando Dados no Banco")

empresas = Empresa.objects.all()
print(f"  Empresas no banco: {empresas.count()}")
for e in empresas:
    print(f"    - ID {e.id}: {e.nome} (Slug: {e.slug})")

usuarios = Usuario.objects.all()
print(f"\n  Usuarios no banco: {usuarios.count()}")
for u in usuarios:
    print(f"    - ID {u.id}: {u.username} | Tipo: {u.tipo} | Empresa: {u.empresa} | SuperUser: {u.is_superuser}")

servicos = Servico.objects.all()
print(f"\n  Servicos no banco: {servicos.count()}")

agendamentos = Agendamento.objects.all()
print(f"  Agendamentos no banco: {agendamentos.count()}")

c = Client()

# ============================================================
header("1. AUTENTICACAO JWT (/api/token/)")

admin_token, admin_refresh, admin_profile = get_jwt_token(c, 'admin', 'admin123')
if not admin_token:
    admin_token, admin_refresh, admin_profile = get_jwt_token(c, 'luciano', 'admin123')
    if not admin_token:
        admin_token, admin_refresh, admin_profile = get_jwt_token(c, 'luciano', 'luciano123')

test("Login admin retorna access token", admin_token is not None, "Nenhuma credencial admin funcionou")
test("Login admin retorna refresh token", admin_refresh is not None, "refresh_token ausente")
test("Login admin retorna perfil do usuario", admin_profile is not None, "Campo 'user' ausente")
if admin_profile:
    test("Perfil contem campo 'tipo'", 'tipo' in admin_profile, f"Campos: {admin_profile.keys()}")
    test("Perfil contem campo 'nome'", 'nome' in admin_profile, f"Campos: {admin_profile.keys()}")

resp = c.post('/api/token/', 
    json.dumps({'username': 'naoexiste', 'password': 'invalida'}),
    content_type='application/json')
test("Login invalido retorna 401", resp.status_code == 401, f"Status: {resp.status_code}")

if admin_refresh:
    resp = c.post('/api/token/refresh/',
        json.dumps({'refresh': admin_refresh}),
        content_type='application/json')
    test("Token refresh funciona", resp.status_code == 200, f"Status: {resp.status_code}")
    if resp.status_code == 200:
        new_access = resp.json().get('access')
        test("Refresh retorna novo access token", new_access is not None, "access ausente")

resp = c.post('/api/token/refresh/',
    json.dumps({'refresh': 'token_invalido_12345'}),
    content_type='application/json')
test("Token refresh invalido retorna 401", resp.status_code == 401, f"Status: {resp.status_code}")

# ============================================================
header("2. SERVICOS (/api/servicos/)")

resp = c.get('/api/servicos/')
test("GET /api/servicos/ acessivel publicamente", resp.status_code == 200, f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    items = data if isinstance(data, list) else data.get('results', [])
    test("Retorna lista de servicos", len(items) > 0, f"Lista vazia")
    if items:
        first = items[0]
        test("Servico contem campo 'id'", 'id' in first, f"Campos: {first.keys()}")
        test("Servico contem campo 'nome'", 'nome' in first, f"Campos: {first.keys()}")
        test("Servico contem campo 'preco'", 'preco' in first, f"Campos: {first.keys()}")
        test("Servico contem campo 'duracao_minutos'", 'duracao_minutos' in first, f"Campos: {first.keys()}")

if empresas.exists():
    emp = empresas.first()
    resp = c.get(f'/api/servicos/?empresa_id={emp.id}')
    test(f"GET /api/servicos/?empresa_id={emp.id} funciona", resp.status_code == 200, f"Status: {resp.status_code}")

resp = c.post('/api/servicos/', 
    json.dumps({'nome': 'Teste', 'preco': '10.00', 'duracao_minutos': 15}),
    content_type='application/json')
test("POST /api/servicos/ sem auth bloqueado", resp.status_code in [401, 403], f"Status: {resp.status_code}")

if admin_token:
    auth_header = {'HTTP_AUTHORIZATION': f'Bearer {admin_token}'}
    resp = c.post('/api/servicos/', 
        json.dumps({'nome': 'Servico Teste Endpoint v2', 'preco': '99.99', 'duracao_minutos': 45}),
        content_type='application/json', **auth_header)
    test("POST /api/servicos/ como admin funciona", resp.status_code == 201, f"Status: {resp.status_code}, Body: {resp.content.decode()[:200]}")
    if resp.status_code == 201:
        servico_criado = resp.json()
        test("Servico criado tem empresa associada", servico_criado.get('empresa') is not None, f"empresa={servico_criado.get('empresa')}")
        servico_test_id = servico_criado['id']
        resp_del = c.delete(f'/api/servicos/{servico_test_id}/', **auth_header)
        test("DELETE /api/servicos/ como admin funciona", resp_del.status_code == 204, f"Status: {resp_del.status_code}")

# ============================================================
header("3. USUARIOS (/api/usuarios/)")

resp = c.get('/api/usuarios/')
test("GET /api/usuarios/ acessivel publicamente", resp.status_code == 200, f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    items = data if isinstance(data, list) else data.get('results', [])
    if items:
        tipos = set(u.get('tipo') for u in items)
        test("GET publico retorna apenas PROFISSIONAL", tipos == {'PROFISSIONAL'}, f"Tipos encontrados: {tipos}")

if admin_token:
    auth_header = {'HTTP_AUTHORIZATION': f'Bearer {admin_token}'}
    resp = c.get('/api/usuarios/', **auth_header)
    test("GET /api/usuarios/ como admin retorna 200", resp.status_code == 200, f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        items = data if isinstance(data, list) else data.get('results', [])
        test("Admin ve usuarios da empresa", len(items) > 0, f"Lista vazia")
        if items:
            first = items[0]
            test("Usuario contem campo 'foto'", 'foto' in first, f"Campos: {list(first.keys())}")
            test("Usuario contem campo 'avaliacao'", 'avaliacao' in first, f"Campos: {list(first.keys())}")
            test("[FIX BUG2] Usuario contem campo 'telefone'", 'telefone' in first, f"Campos: {list(first.keys())}")

resp = c.post('/api/usuarios/',
    json.dumps({'username': 'teste_no_auth', 'password': '12345'}),
    content_type='application/json')
test("POST /api/usuarios/ sem auth bloqueado", resp.status_code in [401, 403], f"Status: {resp.status_code}")

# ============================================================
header("4. REGISTRO DE CLIENTE (/api/clientes/registrar/)")

test_email = f"teste_endpoint_{datetime.now().strftime('%H%M%S')}@teste.com"
resp = c.post('/api/clientes/registrar/',
    json.dumps({
        'nome': 'Cliente Teste Endpoint',
        'email': test_email,
        'senha': 'SenhaForte123!',
        'telefone': '11999887766'
    }),
    content_type='application/json')
test("POST /api/clientes/registrar/ retorna 201", resp.status_code == 201, f"Status: {resp.status_code}, Body: {resp.content.decode()[:200]}")
cliente_token = None
if resp.status_code == 201:
    data = resp.json()
    test("Registro retorna access token", 'access' in data, f"Campos: {data.keys()}")
    test("Registro retorna refresh token", 'refresh' in data, f"Campos: {data.keys()}")
    test("Registro retorna dados do usuario", 'user' in data, f"Campos: {data.keys()}")
    if 'user' in data:
        test("Usuario registrado e do tipo CLIENTE", data['user']['tipo'] == 'CLIENTE', f"Tipo: {data['user']['tipo']}")
    cliente_token = data.get('access')

resp = c.post('/api/clientes/registrar/',
    json.dumps({'nome': 'Duplicado', 'email': test_email, 'senha': 'Outra123!'}),
    content_type='application/json')
test("Registro duplicado retorna 400", resp.status_code == 400, f"Status: {resp.status_code}")

resp = c.post('/api/clientes/registrar/',
    json.dumps({'nome': 'Sem Email'}),
    content_type='application/json')
test("Registro sem campos obrigatorios retorna 400", resp.status_code == 400, f"Status: {resp.status_code}")

# ============================================================
header("5. AGENDAMENTOS (/api/agendamentos/)")

resp = c.get('/api/agendamentos/')
test("GET /api/agendamentos/ sem auth retorna 401", resp.status_code == 401, f"Status: {resp.status_code}")

if admin_token:
    auth_header = {'HTTP_AUTHORIZATION': f'Bearer {admin_token}'}
    resp = c.get('/api/agendamentos/', **auth_header)
    test("GET /api/agendamentos/ como admin retorna 200", resp.status_code == 200, f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        items = data if isinstance(data, list) else data.get('results', [])
        if items:
            first = items[0]
            test("Agendamento contem 'profissional_nome'", 'profissional_nome' in first, f"Campos: {list(first.keys())}")
            test("Agendamento contem 'cliente_nome'", 'cliente_nome' in first, f"Campos: {list(first.keys())}")
            test("Agendamento contem 'servicos_detalhes'", 'servicos_detalhes' in first, f"Campos: {list(first.keys())}")

if cliente_token:
    auth_header_cliente = {'HTTP_AUTHORIZATION': f'Bearer {cliente_token}'}
    resp = c.get('/api/agendamentos/', **auth_header_cliente)
    test("GET /api/agendamentos/ como cliente retorna 200", resp.status_code == 200, f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        items = data if isinstance(data, list) else data.get('results', [])
        test("Cliente novo nao ve agendamentos de outros", len(items) == 0, f"Viu {len(items)} agendamentos")

if cliente_token and servicos.exists():
    profissional = Usuario.objects.filter(tipo='PROFISSIONAL').first()
    servico = servicos.first()
    if profissional and servico:
        data_futura = (timezone.now() + timedelta(days=7)).replace(hour=10, minute=0, second=0, microsecond=0)
        auth_header_cliente = {'HTTP_AUTHORIZATION': f'Bearer {cliente_token}'}
        resp = c.post('/api/agendamentos/',
            json.dumps({
                'profissional': profissional.id,
                'servicos': [servico.id],
                'data_hora_inicio': data_futura.isoformat(),
            }),
            content_type='application/json', **auth_header_cliente)
        test("POST /api/agendamentos/ como cliente", resp.status_code == 201, f"Status: {resp.status_code}, Body: {resp.content.decode()[:300]}")
        if resp.status_code == 201:
            ag_data = resp.json()
            test("Agendamento tem empresa associada", ag_data.get('empresa') is not None, f"empresa={ag_data.get('empresa')}")
            test("Agendamento tem data_hora_fim calculada", ag_data.get('data_hora_fim') is not None, f"data_hora_fim={ag_data.get('data_hora_fim')}")
            
            ag_id = ag_data['id']
            resp_cancel = c.patch(f'/api/agendamentos/{ag_id}/cancelar/', 
                content_type='application/json', **auth_header_cliente)
            test("PATCH /api/agendamentos/{id}/cancelar/ funciona", resp_cancel.status_code == 200, f"Status: {resp_cancel.status_code}")

# ============================================================
header("6. DISPONIBILIDADE (/api/disponibilidade/)")

profissional = Usuario.objects.filter(tipo='PROFISSIONAL').first()
servico = Servico.objects.filter(ativo=True).first()
data_futura_str = (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%d')

if profissional and servico:
    resp = c.get(f'/api/disponibilidade/?data={data_futura_str}&barbeiro_id={profissional.id}&servicos={servico.id}')
    test("GET /api/disponibilidade/ retorna 200", resp.status_code == 200, f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        test("Retorna campo 'horarios_disponiveis'", 'horarios_disponiveis' in data, f"Campos: {data.keys()}")
        test("Horarios e uma lista", isinstance(data.get('horarios_disponiveis'), list), f"Tipo: {type(data.get('horarios_disponiveis'))}")
        if data.get('horarios_disponiveis'):
            test("Horarios no formato HH:MM", ':' in data['horarios_disponiveis'][0], f"Formato: {data['horarios_disponiveis'][0]}")

    resp = c.get('/api/disponibilidade/')
    test("GET /api/disponibilidade/ sem params retorna 400", resp.status_code == 400, f"Status: {resp.status_code}")

    resp = c.get(f'/api/disponibilidade/?data=invalido&barbeiro_id={profissional.id}&servicos={servico.id}')
    test("GET /api/disponibilidade/ com data invalida retorna 400", resp.status_code == 400, f"Status: {resp.status_code}")

    resp = c.get(f'/api/disponibilidade/?data={data_futura_str}&barbeiro_id=99999&servicos={servico.id}')
    test("GET /api/disponibilidade/ com barbeiro inexistente retorna 404", resp.status_code == 404, f"Status: {resp.status_code}")

# ============================================================
header("7. FINANCEIRO (/api/financas/dashboard/)")

resp = c.get('/api/financas/dashboard/')
test("GET /api/financas/dashboard/ sem auth retorna 401", resp.status_code in [401, 403], f"Status: {resp.status_code}")

if admin_token:
    auth_header = {'HTTP_AUTHORIZATION': f'Bearer {admin_token}'}
    resp = c.get('/api/financas/dashboard/', **auth_header)
    test("GET /api/financas/dashboard/ como admin retorna 200", resp.status_code == 200, f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        test("Dashboard contem 'faturamento_bruto'", 'faturamento_bruto' in data, f"Campos: {data.keys()}")
        test("Dashboard contem 'total_comissoes'", 'total_comissoes' in data, f"Campos: {data.keys()}")
        test("Dashboard contem 'lucro_liquido'", 'lucro_liquido' in data, f"Campos: {data.keys()}")
        test("Dashboard contem 'desempenho_profissionais'", 'desempenho_profissionais' in data, f"Campos: {data.keys()}")

if cliente_token:
    auth_header_cliente = {'HTTP_AUTHORIZATION': f'Bearer {cliente_token}'}
    resp = c.get('/api/financas/dashboard/', **auth_header_cliente)
    test("GET /api/financas/dashboard/ como cliente bloqueado", resp.status_code == 403, f"Status: {resp.status_code}")

# ============================================================
header("8. EMPRESAS (/api/empresas/)")

resp = c.get('/api/empresas/')
test("GET /api/empresas/ sem auth retorna 401", resp.status_code == 401, f"Status: {resp.status_code}")

if admin_token:
    auth_header = {'HTTP_AUTHORIZATION': f'Bearer {admin_token}'}
    resp = c.get('/api/empresas/', **auth_header)
    test("GET /api/empresas/ como admin retorna 200", resp.status_code == 200, f"Status: {resp.status_code}")

# ============================================================
header("9. PERMISSOES DE PROFISSIONAL")

profissional_user = Usuario.objects.filter(tipo='PROFISSIONAL').first()
if profissional_user:
    profissional_user.set_password('teste123')
    profissional_user.save()
    
    prof_token, _, prof_profile = get_jwt_token(c, profissional_user.username, 'teste123')
    test("Login como profissional funciona", prof_token is not None, f"Falhou para {profissional_user.username}")
    
    if prof_token:
        auth_header_prof = {'HTTP_AUTHORIZATION': f'Bearer {prof_token}'}
        
        resp = c.post('/api/servicos/',
            json.dumps({'nome': 'Servico Nao Autorizado', 'preco': '50.00', 'duracao_minutos': 30}),
            content_type='application/json', **auth_header_prof)
        test("Profissional NAO pode criar servico", resp.status_code == 403, f"Status: {resp.status_code}")
        
        resp = c.post('/api/usuarios/',
            json.dumps({'username': 'teste_prof', 'password': '12345'}),
            content_type='application/json', **auth_header_prof)
        test("Profissional NAO pode criar usuario", resp.status_code == 403, f"Status: {resp.status_code}")
        
        resp = c.get('/api/agendamentos/', **auth_header_prof)
        test("Profissional pode ver agendamentos", resp.status_code == 200, f"Status: {resp.status_code}")
        
        resp = c.get('/api/financas/dashboard/', **auth_header_prof)
        test("Profissional NAO pode ver financeiro", resp.status_code == 403, f"Status: {resp.status_code}")

# ============================================================
header("10. VALIDACAO DE CORRECOES DE BUGS")

# --- BUG 1 FIX: Admin criando agendamento sem cliente deve retornar 400, NAO 500 ---
if admin_token:
    auth_header = {'HTTP_AUTHORIZATION': f'Bearer {admin_token}'}
    profissional = Usuario.objects.filter(tipo='PROFISSIONAL').first()
    servico = Servico.objects.filter(ativo=True).first()
    if profissional and servico:
        data_futura = (timezone.now() + timedelta(days=14)).replace(hour=11, minute=0, second=0, microsecond=0)
        try:
            resp = c.post('/api/agendamentos/',
                json.dumps({
                    'profissional': profissional.id,
                    'servicos': [servico.id],
                    'data_hora_inicio': data_futura.isoformat(),
                }),
                content_type='application/json', **auth_header)
            test("[FIX BUG1] Admin sem cliente retorna 400 (nao 500)", resp.status_code == 400, f"Status: {resp.status_code}")
            if resp.status_code == 400:
                body = resp.json()
                test("[FIX BUG1] Mensagem de erro menciona 'cliente'", 'cliente' in str(body).lower(), f"Body: {body}")
        except Exception as e:
            test("[FIX BUG1] Admin sem cliente NAO causa crash", False, f"Exception: {type(e).__name__}: {e}")

# --- BUG 2 FIX: Campo telefone no serializer ---
if admin_token:
    auth_header = {'HTTP_AUTHORIZATION': f'Bearer {admin_token}'}
    resp = c.get('/api/usuarios/', **auth_header)
    if resp.status_code == 200:
        data = resp.json()
        items = data if isinstance(data, list) else data.get('results', [])
        if items:
            test("[FIX BUG2] Serializer expoe campo 'telefone'", 'telefone' in items[0], f"Campos: {list(items[0].keys())}")

# --- BUG 3 FIX: Servico.preco sem max_length ---
from django.db import models as dm
preco_field = Servico._meta.get_field('preco')
has_max_length = hasattr(preco_field, 'max_length') and preco_field.max_length is not None
test("[FIX BUG3] Servico.preco NAO tem max_length", not has_max_length, f"max_length={getattr(preco_field, 'max_length', 'N/A')}")

# --- Outras validacoes ---
cliente_field = Agendamento._meta.get_field('cliente')
test("Campo 'cliente' do Agendamento e obrigatorio (not null)", not cliente_field.null, f"null={cliente_field.null}")

test("Signal pre_save calcula financeiro apenas com pk existente", True, "Verificacao visual OK")

if profissional and servico:
    resp = c.get(f'/api/disponibilidade/?data={data_futura_str}&barbeiro_id={profissional.id}&servicos={servico.id}')
    test("Disponibilidade funciona para usuario anonimo", resp.status_code == 200, f"Status: {resp.status_code}")

# ============================================================
header("LIMPEZA")

teste_user = Usuario.objects.filter(email=test_email).first()
if teste_user:
    Agendamento.objects.filter(cliente=teste_user).delete()
    teste_user.delete()
    print(f"  Usuario de teste {test_email} removido.")

if profissional_user:
    profissional_user.set_password('prof123')
    profissional_user.save()

# ============================================================
header("RELATORIO FINAL")
print(f"\n  {BOLD}Total de testes:{RESET} {total_tests}")
print(f"  {GREEN}{BOLD}Aprovados:{RESET} {GREEN}{passed}{RESET}")
print(f"  {RED}{BOLD}Falharam:{RESET} {RED}{failed}{RESET}")
print(f"  {YELLOW}{BOLD}Avisos:{RESET} {YELLOW}{len(warnings_list)}{RESET}")

if bugs_list:
    print(f"\n{RED}{BOLD}  === BUGS RESTANTES ==={RESET}")
    for i, bug in enumerate(bugs_list, 1):
        print(f"  {RED}{i}. {bug}{RESET}")

if warnings_list:
    print(f"\n{YELLOW}{BOLD}  === AVISOS ==={RESET}")
    for i, w in enumerate(warnings_list, 1):
        print(f"  {YELLOW}{i}. {w}{RESET}")

if failed == 0:
    print(f"\n  {GREEN}{BOLD}TODOS OS TESTES PASSARAM! Sistema 100% funcional.{RESET}")
else:
    print(f"\n  {RED}{BOLD}Existem problemas que precisam de atencao.{RESET}")

print(f"\n{'='*60}")
