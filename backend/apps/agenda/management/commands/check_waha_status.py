import os
import requests
from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.conf import settings

class Command(BaseCommand):
    help = 'Verifica o status da sessão do WAHA e envia alerta se estiver desconectado'

    def handle(self, *args, **kwargs):
        waha_url = getattr(settings, 'WAHA_API_URL', 'http://localhost:3000').rstrip('/')
        waha_session = getattr(settings, 'WAHA_SESSION', 'default')
        api_key = getattr(settings, 'WAHA_API_KEY', '') or os.environ.get('WAHA_API_KEY', '')
        
        endpoint = f"{waha_url}/api/sessions/"
        
        headers = {
            "Accept": "application/json"
        }
        if api_key:
            headers["X-Api-Key"] = api_key
            
        is_connected = False
        error_msg = ""
        
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            if response.ok:
                sessions = response.json()
                # Verifica se existe a sessão com o nome configurado e se está com status WORKING ou CONNECTED
                for session in sessions:
                    if session.get('name') == waha_session:
                        status = session.get('status', '').upper()
                        if status in ['WORKING', 'CONNECTED', 'STARTING']:
                            is_connected = True
                            break
                        else:
                            error_msg = f"Sessão '{waha_session}' encontrada, mas status é '{status}'."
                
                if not is_connected and not error_msg:
                    error_msg = f"Sessão '{waha_session}' não foi encontrada na lista de sessões."
            else:
                error_msg = f"A API do WAHA retornou erro HTTP {response.status_code}: {response.text}"
                
        except Exception as e:
            error_msg = f"Falha de conexão com a API do WAHA: {str(e)}"
            
        if not is_connected:
            self.stderr.write(f"WAHA Desconectado/Erro: {error_msg}")
            
            # Envia o e-mail de alerta
            email_to = 'infor@salaopro.site'
            subject = "🚨 URGENTE: WhatsApp Desconectado no Salão_PRO!"
            body = (
                "Olá Administrador,\n\n"
                "O sistema de monitoramento automático detectou que a conexão com a API do WhatsApp (WAHA) falhou ou está desconectada.\n\n"
                f"Detalhes do erro: {error_msg}\n\n"
                "Isso significa que o sistema PAROU de enviar mensagens automáticas (lembretes, cancelamentos, etc.).\n"
                "Por favor, acesse o servidor ou o painel do WAHA imediatamente para ler o QR Code e reestabelecer a conexão.\n\n"
                "Atenciosamente,\n"
                "Robô de Monitoramento do Salão_PRO"
            )
            
            try:
                email = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email_to]
                )
                email.send(fail_silently=False)
                self.stdout.write(self.style.SUCCESS(f"Alerta enviado com sucesso para {email_to}"))
            except Exception as e_mail:
                self.stderr.write(f"Erro ao tentar enviar o e-mail de alerta: {str(e_mail)}")
        else:
            self.stdout.write(self.style.SUCCESS(f"WAHA está operando normalmente. Sessão '{waha_session}' conectada."))
