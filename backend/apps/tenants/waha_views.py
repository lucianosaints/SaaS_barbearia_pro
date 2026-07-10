import os
import requests
import base64
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings

logger = logging.getLogger(__name__)

class WahaQRCodeView(APIView):
    """
    View responsável por interagir com o container do WAHA para:
    1. Garantir que a sessão 'default' esteja iniciada.
    2. Obter o QR Code atual para conexão do WhatsApp.
    """
    # Protege a rota, apenas usuários autenticados (administradores do painel) podem acessar
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        waha_url = getattr(settings, 'WAHA_API_URL', 'http://localhost:3000').rstrip('/')
        waha_session = getattr(settings, 'WAHA_SESSION', 'default')
        api_key = getattr(settings, 'WAHA_API_KEY', '') or os.getenv('WAHA_API_KEY', '')

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if api_key:
            headers["X-Api-Key"] = api_key

        # 1. Iniciar a Sessão (garante que ela existe ou acorda ela)
        start_session_url = f"{waha_url}/api/sessions/start"
        session_payload = {"name": waha_session}
        
        try:
            # Chama o endpoint para iniciar/garantir a sessão.
            # Timeout aumentado para 45s porque o motor do WAHA pode demorar muito
            requests.post(start_session_url, json=session_payload, headers=headers, timeout=45)
            
            # Garante que a sessão vai iniciar mesmo que já existisse mas estivesse parada (STOPPED)
            start_engine_url = f"{waha_url}/api/sessions/{waha_session}/start"
            requests.post(start_engine_url, headers=headers, timeout=15)
        except Exception as e:
            logger.error(f"WAHA: Falha ao tentar iniciar sessão {waha_session}. Erro: {str(e)}")
            return Response(
                {"error": "Não foi possível conectar ao motor do WhatsApp. Verifique se o container 'waha' está rodando."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # 2. Capturar o QR Code (Em formato de imagem)
        qr_url = f"{waha_url}/api/{waha_session}/auth/qr?format=image"
        
        try:
            # Requisitando a imagem do QR Code
            qr_response = requests.get(qr_url, headers=headers, timeout=45)
            
            if qr_response.status_code == 200:
                # Retorna o status 200 OK do WAHA e a imagem no body em bytes
                # Vamos converter para base64 para facilitar a exibição no React
                image_bytes = qr_response.content
                base64_encoded = base64.b64encode(image_bytes).decode('utf-8')
                
                return Response({
                    "status": "WAITING_FOR_SCAN",
                    "qrcode_base64": base64_encoded,
                    "message": "Leia o QR Code com o seu WhatsApp para conectar."
                }, status=status.HTTP_200_OK)
                
            elif qr_response.status_code in [404, 422]:
                # O endpoint retorna 404 quando o motor ainda está inicializando.
                # Retorna 422 quando a sessão já está conectada (WORKING) e não tem QR code.
                # Vamos verificar o status real da sessão
                status_url = f"{waha_url}/api/sessions"
                status_response = requests.get(status_url, headers=headers, timeout=15)
                if status_response.ok:
                    sessions = status_response.json()
                    # Encontrar a nossa sessão específica
                    my_session = next((s for s in sessions if s.get('name') == waha_session), None)
                    # No WAHA o status pode ser WORKING, CONNECTED, etc.
                    if my_session and my_session.get('status') in ['WORKING', 'CONNECTED']:
                        return Response({
                            "status": "WORKING",
                            "message": "O WhatsApp já está conectado e pronto para uso!"
                        }, status=status.HTTP_200_OK)
                
                return Response({
                    "status": "STARTING",
                    "message": "A sessão do WhatsApp está inicializando, tente novamente em alguns segundos..."
                }, status=status.HTTP_200_OK)
                
            else:
                logger.error(f"WAHA retornou erro ao buscar QR Code: {qr_response.status_code} - {qr_response.text}")
                return Response({
                    "error": "Erro ao buscar QR Code do WhatsApp."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"WAHA: Falha ao tentar capturar o QR Code. Erro: {str(e)}")
            return Response(
                {"error": "Falha de comunicação interna com o motor de WhatsApp."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    def delete(self, request, *args, **kwargs):
        waha_url = getattr(settings, 'WAHA_API_URL', 'http://localhost:3000').rstrip('/')
        waha_session = getattr(settings, 'WAHA_SESSION', 'default')
        api_key = getattr(settings, 'WAHA_API_KEY', '') or os.getenv('WAHA_API_KEY', '')

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if api_key:
            headers["X-Api-Key"] = api_key

        logout_url = f"{waha_url}/api/sessions/{waha_session}/logout"
        
        try:
            requests.post(logout_url, headers=headers, timeout=15)
            return Response({"message": "WhatsApp desconectado com sucesso."}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"WAHA: Erro ao desconectar WhatsApp. Erro: {str(e)}")
            return Response(
                {"error": "Erro ao tentar desconectar o WhatsApp."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
