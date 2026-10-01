import os
import django
import requests
from datetime import datetime, timedelta
from urllib.parse import urljoin
import time
import json
from unittest import mock

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.accounts.models import Usuario
from apps.tenants.models import Empresa
from apps.agenda.models import Servico, Agendamento, FilaEspera
from django.utils import timezone

BASE_URL = 'http://127.0.0.1:8000'

def p(msg):
    print(f"\n[QA] {msg}")

def run_tests():
    p("Iniciando bateria de testes de QA - PARTE 2...")

    empresa_ativa = Empresa.objects.get(slug="qa-ativa")
    user_ativo = Usuario.objects.get(username="ativo_qa")
    servico = Servico.objects.get(nome="Corte Teste QA")

    res = requests.post(urljoin(BASE_URL, '/api/token/'), data={"username": "ativo_qa", "password": "senha123"})
    token_ativo = res.json().get('access')

    p("FASE 2: Fluxo de Agendamento e WAHA")
    hoje = timezone.now().date()
    hora = (timezone.now() + timedelta(hours=2)).time()
    hora_str = hora.strftime('%H:%M')
    
    agendamentos_url = urljoin(BASE_URL, '/api/agendamentos/')
    payload_agendamento = {
        "cliente_nome": "Cliente QA WAHA",
        "cliente_telefone": "5511999999999",
        "servicos": [servico.id],
        "profissional": user_ativo.id,
        "data_hora_inicio": f"{hoje.isoformat()}T{hora_str}:00"
    }
    
    res_ag = requests.post(agendamentos_url, json=payload_agendamento, headers={"Authorization": f"Bearer {token_ativo}"})
    agendamento_id = None
    if res_ag.status_code == 201:
        agendamento_id = res_ag.json().get("id")
        p("Agendamento criado com sucesso (201)! Verifique os logs do Django para o sinal.")
    else:
        p(f"Falha ao criar agendamento: {res_ag.status_code} - {res_ag.text}")
        
    p("FASE 3: Cancelamento e Fila de Espera Inteligente")
    if agendamento_id:
        fila_payload = {
            "cliente_nome": "Espera QA",
            "cliente_telefone": "5511988888888",
            "data_desejada": hoje.isoformat(),
            "hora_desejada": hora_str,
            "empresa": empresa_ativa.id
        }
        res_fila = requests.post(urljoin(BASE_URL, '/api/fila-espera/'), json=fila_payload, headers={"Authorization": f"Bearer {token_ativo}"})
        if res_fila.status_code == 201: p("Cliente adicionado à fila de espera (201).")
        else: p(f"Falha ao adicionar na fila: {res_fila.status_code} - {res_fila.text}")
        
        delete_url = urljoin(BASE_URL, f'/api/agendamentos/{agendamento_id}/cancelar/')
        res_del = requests.patch(delete_url, headers={"Authorization": f"Bearer {token_ativo}"})
        if res_del.status_code in [200, 204]: p("Agendamento cancelado (PATCH). Verifique fila de espera/WAHA.")
        else:
            del_real_url = urljoin(BASE_URL, f'/api/agendamentos/{agendamento_id}/')
            res_del_real = requests.delete(del_real_url, headers={"Authorization": f"Bearer {token_ativo}"})
            if res_del_real.status_code == 204: p("Agendamento excluído (DELETE) com sucesso!")
            else: p(f"Falha ao excluir: {res_del.status_code}")
    
    p("FASE 5: Tratamento de Erros Silenciosos (Agendamento sem WAHA)")
    
    import dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', '.env')
    
    try:
        with open(env_path, 'r') as f: backup_env = f.read()
        new_env = backup_env.replace('WAHA_API_URL=http://localhost:3000', 'WAHA_API_URL=http://localhost:9999')
        with open(env_path, 'w') as f: f.write(new_env)
        
        p("Aguardando 3s para o runserver...")
        time.sleep(3)
        
        res_ag_error = requests.post(agendamentos_url, json=payload_agendamento, headers={"Authorization": f"Bearer {token_ativo}"})
        if res_ag_error.status_code == 201:
            p("Agendamento criado com sucesso, mesmo com erro no WAHA (Silencioso). OK.")
        else:
            p(f"FALHA: O sistema retornou erro (esperava-se 201 capturando o erro). Status: {res_ag_error.status_code} - {res_ag_error.text}")
    finally:
        with open(env_path, 'w') as f: f.write(backup_env)
        p("Arquivo .env restaurado.")

    p("Bateria de testes finalizada.")

if __name__ == '__main__':
    run_tests()
