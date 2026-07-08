import os
import mercadopago
from django.conf import settings

def criar_preferencia_assinatura(empresa_id: str, empresa_nome: str, valor: float) -> str:
    """
    Cria uma preferência de pagamento no Mercado Pago e retorna o link de inicialização (init_point).
    """
    mp_access_token = getattr(settings, 'MERCADOPAGO_ACCESS_TOKEN', os.environ.get('MERCADOPAGO_ACCESS_TOKEN', ''))
    
    if not mp_access_token:
        raise ValueError("MERCADOPAGO_ACCESS_TOKEN não está configurado.")
        
    sdk = mercadopago.SDK(mp_access_token)
    
    preference_data = {
        "items": [
            {
                "title": f"Assinatura Mensal - {empresa_nome}",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(valor)
            }
        ],
        "external_reference": str(empresa_id),
        "back_urls": {
            "success": "http://localhost:3000/admin/assinatura?status=success",
            "failure": "http://localhost:3000/admin/assinatura?status=failure",
            "pending": "http://localhost:3000/admin/assinatura?status=pending"
        }
    }
    
    preference_response = sdk.preference().create(preference_data)
    
    if "response" in preference_response and "init_point" in preference_response["response"]:
        return preference_response["response"]["init_point"]
    
    raise Exception(f"Erro ao criar preferência no Mercado Pago: {preference_response}")


def criar_pagamento_pix(empresa_id: str, empresa_nome: str, valor: float, email: str) -> dict:
    """
    Cria um pagamento via PIX no Mercado Pago e retorna o QR Code em Base64 e o link do ticket.
    """
    mp_access_token = getattr(settings, 'MERCADOPAGO_ACCESS_TOKEN', os.environ.get('MERCADOPAGO_ACCESS_TOKEN', ''))
    
    if not mp_access_token:
        raise ValueError("MERCADOPAGO_ACCESS_TOKEN não está configurado.")
        
    sdk = mercadopago.SDK(mp_access_token)
    
    payment_data = {
        "transaction_amount": float(valor),
        "description": f"Assinatura Mensal - {empresa_nome}",
        "payment_method_id": "pix",
        "payer": {
            "email": email,
            "first_name": "Usuário",
            "last_name": "Teste",
            "identification": {
                "type": "CPF",
                "number": "19119119100"
            }
        },
        "external_reference": str(empresa_id),
    }
    
    payment_response = sdk.payment().create(payment_data)
    
    if "response" in payment_response and payment_response["status"] == 201:
        res = payment_response["response"]
        poi = res.get("point_of_interaction", {}).get("transaction_data", {})
        return {
            "ticket_url": poi.get("ticket_url"),
            "qr_code_base64": poi.get("qr_code_base64"),
            "qr_code": poi.get("qr_code"),
            "payment_id": res.get("id")
        }
    
    raise Exception(f"Erro ao criar pagamento PIX no Mercado Pago: {payment_response}")
