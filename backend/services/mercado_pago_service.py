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
