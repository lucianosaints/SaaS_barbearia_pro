import os
import requests
import logging
import re
from django.conf import settings

logger = logging.getLogger(__name__)

def format_waha_phone(phone: str) -> str:
    """
    Formata o telefone para o formato aceito pela WAHA.
    Remove não-dígitos. Adiciona o código do país (55) se não houver.
    Retorna o número seguido de '@c.us'.
    """
    if not phone:
        return ""
    
    phone_number = str(phone)
    
    # Remove caracteres especiais (parênteses, traços, espaços), preservando letras caso já tenha @c.us
    # Mas para ser mais seguro conforme a sua instrução, vamos aplicar a regra:
    clean_phone = re.sub(r'\D', '', phone_number)
    
    if not clean_phone.startswith('55'):
        clean_phone = f"55{clean_phone}"
        
    phone_number = f"{clean_phone}@c.us"
        
    return phone_number

def enviar_mensagem_whatsapp(telefone: str, mensagem: str) -> bool:
    """
    Envia uma mensagem de texto utilizando a WAHA API.
    A falha no envio não deve interromper a execução do fluxo (fail_silently).
    """
    waha_url = getattr(settings, 'WAHA_API_URL', 'http://localhost:3000').rstrip('/')
    waha_session = getattr(settings, 'WAHA_SESSION', 'default')
    
    if not telefone:
        logger.warning("Tentativa de envio de WhatsApp falhou: Telefone não fornecido.")
        return False
        
    waha_phone = format_waha_phone(telefone)
    
    endpoint = f"{waha_url}/api/sendText"
    
    payload = {
        "chatId": waha_phone,
        "text": mensagem,
        "session": waha_session
    }
    
    api_key = getattr(settings, 'WAHA_API_KEY', '') or os.getenv('WAHA_API_KEY', '')
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if api_key:
        headers["X-Api-Key"] = api_key

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        if not response.ok:
            logger.error(f"WAHA retornou erro [Telefone Formatado: {waha_phone}]: {response.status_code} - JSON: {response.text}")
            return False
            
        logger.info(f"Mensagem WhatsApp enviada com sucesso para {waha_phone} na sessão {waha_session}")
        return True
    except Exception as e:
        logger.error(f"Erro inesperado ao enviar WhatsApp via WAHA para {waha_phone}: {str(e)}")
        return False
