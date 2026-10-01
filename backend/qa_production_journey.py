"""QA controlada de produção. Requer QA_CLIENT_PHONE no ambiente.

Cria uma empresa de homologação, percorre gestor/cliente e a desativa. Também
faz uma reserva futura na empresa informada para validar o WhatsApp conectado.
Nunca imprime tokens, senhas, telefone ou dados privados.
"""
import json
import os
import secrets
import sys
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import requests


BASE = os.getenv("QA_BASE_URL", "https://www.salaopro.site").rstrip("/")
PHONE = os.environ["QA_CLIENT_PHONE"]
CONNECTED_COMPANY_ID = int(os.getenv("QA_CONNECTED_COMPANY_ID", "3"))
TIMEOUT = 30
PASSWORD = f"Qa!{secrets.token_urlsafe(14)}aA1"
SUFFIX = datetime.now().strftime("%Y%m%d%H%M%S")


def request(method, path, token=None, expected=(200,), **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.request(method, f"{BASE}{path}", headers=headers, timeout=TIMEOUT, **kwargs)
    if response.status_code not in expected:
        body = response.text[:500]
        raise RuntimeError(f"{method} {path}: HTTP {response.status_code}: {body}")
    return response.json() if response.content else None


def first_available(company_id, professional_id, service_id, start_days=5):
    for offset in range(start_days, start_days + 20):
        target = date.today() + timedelta(days=offset)
        data = request("GET", "/api/disponibilidade/", expected=(200,), params={
            "data": target.isoformat(), "barbeiro_id": professional_id, "servicos": service_id,
        })
        if data["horarios_disponiveis"]:
            return target, data["horarios_disponiveis"][0]
    raise RuntimeError(f"Nenhum horário disponível para a empresa {company_id}")


def iso_start(target_date, hhmm):
    local = datetime.combine(target_date, time.fromisoformat(hhmm), tzinfo=ZoneInfo("America/Sao_Paulo"))
    return local.isoformat()


def main():
    result = {"homologacao": {}, "whatsapp": {}}

    # Parte A: empresa nova e jornada completa.
    manager_email = f"qa.gestor.{SUFFIX}@example.test"
    signup = request("POST", "/api/saas/registrar/", expected=(201,), json={
        "nome_barbearia": f"QA Homologação {SUFFIX}",
        "nome_admin": "Gestor QA Produção",
        "email": manager_email,
        "senha": PASSWORD,
        "whatsapp": "00000000000",
        "aceitou_termos": True,
    })
    manager_token = signup["access"]
    company_id = signup["user"]["empresa"]["id"]
    result["homologacao"]["empresa_id"] = company_id

    service = request("POST", "/api/servicos/", token=manager_token, expected=(201,), json={
        "nome": "Corte QA Produção", "preco": "47.00", "duracao_minutos": 30, "ativo": True,
    })
    professional = request("POST", "/api/usuarios/", token=manager_token, expected=(201,), json={
        "username": f"qa.profissional.{SUFFIX}@example.test",
        "email": f"qa.profissional.{SUFFIX}@example.test",
        "first_name": "Profissional", "last_name": "QA",
        "password": PASSWORD, "telefone": "00000000000", "taxa_comissao": "40.00", "status": "ATIVO",
    })
    customer = request("POST", "/api/clientes/registrar/", expected=(201,), json={
        "nome": "Cliente QA Produção", "email": f"qa.cliente.{SUFFIX}@example.test",
        "senha": PASSWORD, "telefone": "00000000000", "empresa_id": company_id, "aceitou_termos": True,
    })
    customer_token = customer["access"]
    target, slot = first_available(company_id, professional["id"], service["id"])
    booking = request("POST", "/api/agendamentos/", token=customer_token, expected=(201,), json={
        "profissional": professional["id"], "servicos": [service["id"]],
        "data_hora_inicio": iso_start(target, slot), "metodo_pagamento": "PIX",
    })
    occupied = request("GET", "/api/disponibilidade/", expected=(200,), params={
        "data": target.isoformat(), "barbeiro_id": professional["id"], "servicos": service["id"],
    })
    if slot not in occupied["horarios_ocupados"]:
        raise RuntimeError("A reserva de homologação não ocupou o horário")
    request("PATCH", f"/api/agendamentos/{booking['id']}/", token=manager_token, expected=(200,), json={"status": "CONFIRMADO"})
    customer_view = request("GET", "/api/agendamentos/", token=customer_token, expected=(200,))
    if customer_view[0]["status"] != "CONFIRMADO":
        raise RuntimeError("Cliente não visualizou o status confirmado")
    request("PATCH", f"/api/agendamentos/{booking['id']}/cancelar/", token=customer_token, expected=(200,))
    released = request("GET", "/api/disponibilidade/", expected=(200,), params={
        "data": target.isoformat(), "barbeiro_id": professional["id"], "servicos": service["id"],
    })
    if slot not in released["horarios_disponiveis"] or slot in released["horarios_ocupados"]:
        raise RuntimeError("Cancelamento de homologação não liberou o horário")
    request("PATCH", f"/api/servicos/{service['id']}/", token=manager_token, expected=(200,), json={"ativo": False})
    request("PATCH", f"/api/usuarios/{professional['id']}/", token=manager_token, expected=(200,), json={"is_active": False})
    request("PATCH", f"/api/empresas/{company_id}/", token=manager_token, expected=(200,), json={"ativo": False})
    result["homologacao"].update({
        "cadastro": "OK", "servico": "OK", "profissional": "OK", "cliente": "OK",
        "agendamento": "OK", "confirmacao": "OK", "cancelamento_libera_horario": "OK",
        "empresa_desativada": True,
    })

    # Parte B: empresa existente com WAHA conectado; reserva e cancela.
    services = request("GET", "/api/servicos/", expected=(200,), params={"empresa_id": CONNECTED_COMPANY_ID})
    professionals = request("GET", "/api/usuarios/", expected=(200,), params={"empresa_id": CONNECTED_COMPANY_ID})
    if not services or not professionals:
        raise RuntimeError("Empresa conectada não possui serviço/profissional público")
    service_live, professional_live = services[0], professionals[0]
    live_customer = request("POST", "/api/clientes/registrar/", expected=(201,), json={
        "nome": "Cliente QA WhatsApp", "email": f"qa.whatsapp.{SUFFIX}@example.test",
        "senha": PASSWORD, "telefone": PHONE, "empresa_id": CONNECTED_COMPANY_ID, "aceitou_termos": True,
    })
    live_token = live_customer["access"]
    target_live, slot_live = first_available(CONNECTED_COMPANY_ID, professional_live["id"], service_live["id"], 7)
    live_booking = request("POST", "/api/agendamentos/", token=live_token, expected=(201,), json={
        "profissional": professional_live["id"], "servicos": [service_live["id"]],
        "data_hora_inicio": iso_start(target_live, slot_live), "metodo_pagamento": "PIX",
    })
    request("PATCH", f"/api/agendamentos/{live_booking['id']}/cancelar/", token=live_token, expected=(200,))
    released_live = request("GET", "/api/disponibilidade/", expected=(200,), params={
        "data": target_live.isoformat(), "barbeiro_id": professional_live["id"], "servicos": service_live["id"],
    })
    if slot_live not in released_live["horarios_disponiveis"]:
        raise RuntimeError("Cancelamento na empresa conectada não liberou o horário")
    result["whatsapp"] = {
        "empresa_id": CONNECTED_COMPANY_ID, "agendamento_id": live_booking["id"],
        "data": target_live.isoformat(), "horario": slot_live,
        "mensagem_agendamento_disparada": True, "mensagem_cancelamento_disparada": True,
        "horario_liberado": True,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"erro": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise
