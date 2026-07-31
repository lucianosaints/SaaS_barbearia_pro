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
        waha_url = getattr(settings, 'WAHA_API_URL', 'http://waha:3000').rstrip('/')
        
        if hasattr(request.user, 'empresa') and request.user.empresa:
            waha_session = f"tenant_{request.user.empresa.id}"
        else:
            return Response({"error": "Usuário não vinculado a uma empresa."}, status=status.HTTP_400_BAD_REQUEST)
            
        api_key = getattr(settings, 'WAHA_API_KEY', '') or os.getenv('WAHA_API_KEY', '')

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if api_key:
            headers["X-Api-Key"] = api_key

        # 1. Verificar se a sessão já existe antes de tentar criá-la
        try:
            check_url = f"{waha_url}/api/sessions/{waha_session}"
            check_resp = requests.get(check_url, headers=headers, timeout=10)
            
            if check_resp.status_code == 404:
                # Sessão não existe, cria ela
                create_url = f"{waha_url}/api/sessions"
                session_payload = {"name": waha_session}
                requests.post(create_url, json=session_payload, headers=headers, timeout=30)
                # Inicia o motor
                start_url = f"{waha_url}/api/sessions/{waha_session}/start"
                requests.post(start_url, headers=headers, timeout=30)
                return Response({
                    "status": "LOADING",
                    "message": "Sessão criada. O WhatsApp está preparando o seu QR Code, aguarde 5 segundos..."
                }, status=status.HTTP_200_OK)
            
            elif check_resp.ok:
                session_data = check_resp.json()
                current_status = session_data.get('status', '')
                
                if current_status in ['WORKING', 'CONNECTED']:
                    return Response({
                        "status": "WORKING",
                        "message": "O WhatsApp já está conectado e pronto para uso!"
                    }, status=status.HTTP_200_OK)
                
                if current_status in ['FAILED', 'STOPPED']:
                    # Sessão travou, deleta e recria
                    delete_url = f"{waha_url}/api/sessions/{waha_session}"
                    requests.delete(delete_url, headers=headers, timeout=15)
                    create_url = f"{waha_url}/api/sessions"
                    requests.post(create_url, json={"name": waha_session}, headers=headers, timeout=30)
                    start_url = f"{waha_url}/api/sessions/{waha_session}/start"
                    requests.post(start_url, headers=headers, timeout=30)
                    return Response({
                        "status": "LOADING",
                        "message": "Sessão reiniciada. Aguarde 5 segundos..."
                    }, status=status.HTTP_200_OK)
                    
                # Se está STARTING, não faz nada pesado, apenas tenta pegar o QR
                
        except requests.exceptions.ConnectionError:
            logger.error(f"WAHA: Não conseguiu conectar ao container WAHA em {waha_url}")
            return Response(
                {"error": f"Não foi possível conectar ao motor do WhatsApp em {waha_url}. Verifique se o container 'waha' está rodando."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"WAHA: Falha ao verificar sessão {waha_session}. Erro: {str(e)}")
            return Response(
                {"error": "Não foi possível conectar ao motor do WhatsApp. Verifique se o container 'waha' está rodando."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # 2. Capturar o QR Code (Em formato de imagem)
        qr_url = f"{waha_url}/api/{waha_session}/auth/qr?format=image"
        
        try:
            # Requisitando a imagem do QR Code
            qr_headers = headers.copy()
            qr_headers["Accept"] = "image/png"
            qr_response = requests.get(qr_url, headers=qr_headers, timeout=60)
            
            if qr_response.status_code == 200:
                # Verifica se o retorno veio em JSON acidentalmente
                content_type = qr_response.headers.get("Content-Type", "")
                
                if "application/json" in content_type:
                    # Se for JSON, o WAHA provavelmente enviou a string base64 dentro de algum campo
                    data = qr_response.json()
                    # Pode vir em data['qrcode'] ou data['url'] ou etc. Tenta achar o base64
                    base64_encoded = data.get('qrcode', '')
                    # Se já vier com o prefixo 'data:image/png;base64,', vamos limpar para o React colocar depois
                    if "base64," in base64_encoded:
                        base64_encoded = base64_encoded.split("base64,")[1]
                else:
                    # Se for imagem real, converte
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
                status_response = requests.get(status_url, headers=headers, timeout=30)
                if status_response.ok:
                    sessions = status_response.json()
                    # Encontrar a nossa sessão específica
                    my_session = next((s for s in sessions if s.get('name') == waha_session), None)
                    
                    if not my_session or my_session.get('status') in ['FAILED', 'STOPPED']:
                        try:
                            # Auto-healing agressivo: se for FAILED, a sessão travou e precisa ser recriada
                            if my_session and my_session.get('status') == 'FAILED':
                                delete_url = f"{waha_url}/api/sessions/{waha_session}"
                                requests.delete(delete_url, headers=headers, timeout=15)
                                session_payload = {"name": waha_session}
                                requests.post(f"{waha_url}/api/sessions", json=session_payload, headers=headers, timeout=30)
                                
                            start_engine_url = f"{waha_url}/api/sessions/{waha_session}/start"
                            requests.post(start_engine_url, headers=headers, timeout=30)
                        except Exception as e:
                            logger.error(f"WAHA: Erro ao forçar start/delete no fallback. {e}")
                        return Response({
                            "status": "LOADING",
                            "message": "O WhatsApp está preparando o seu QR Code, aguarde 5 segundos..."
                        }, status=status.HTTP_200_OK)

                    current_status = my_session.get('status', 'DESCONHECIDO')
                    if current_status in ['WORKING', 'CONNECTED']:
                        return Response({
                            "status": "WORKING",
                            "message": "O WhatsApp já está conectado e pronto para uso!"
                        }, status=status.HTTP_200_OK)
                    else:
                        # Se não está conectado e não está parado, significa que está inicializando ou esperando QR.
                        # Como o endpoint do QR retornou 404/422, ele ainda está preparando.
                        return Response({
                            "status": "LOADING",
                            "message": "O WhatsApp está preparando o seu QR Code, aguarde 5 segundos..."
                        }, status=status.HTTP_200_OK)
                
                return Response({
                    "status": "LOADING",
                    "message": "O WhatsApp está preparando o seu QR Code, aguarde 5 segundos..."
                }, status=status.HTTP_200_OK)
                
            else:
                erro_txt = f"WAHA retornou {qr_response.status_code}: {qr_response.text}"
                logger.error(erro_txt)
                # Retorna o erro real para facilitar o debug na tela
                return Response({
                    "error": erro_txt
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"WAHA: Falha ao tentar capturar o QR Code. Erro: {str(e)}")
            return Response(
                {"error": "Falha de comunicação interna com o motor de WhatsApp."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    def delete(self, request, *args, **kwargs):
        waha_url = getattr(settings, 'WAHA_API_URL', 'http://waha:3000').rstrip('/')
        
        if hasattr(request.user, 'empresa') and request.user.empresa:
            waha_session = f"tenant_{request.user.empresa.id}"
        else:
            return Response({"error": "Usuário não vinculado a uma empresa."}, status=status.HTTP_400_BAD_REQUEST)
            
        api_key = getattr(settings, 'WAHA_API_KEY', '') or os.getenv('WAHA_API_KEY', '')

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if api_key:
            headers["X-Api-Key"] = api_key

        stop_url = f"{waha_url}/api/sessions/{waha_session}/stop"
        delete_url = f"{waha_url}/api/sessions/{waha_session}"
        logout_url = f"{waha_url}/api/sessions/{waha_session}/logout"
        
        try:
            # 1. Tenta logout suave se estiver conectado (pode falhar se estiver travado)
            requests.post(logout_url, headers=headers, timeout=5)
        except:
            pass

        try:
            # 2. Tenta parar o motor
            requests.post(stop_url, headers=headers, timeout=5)
        except:
            pass

        try:
            # 3. Força a exclusão total da sessão para limpar qualquer estado corrompido
            requests.delete(delete_url, headers=headers, timeout=15)
            return Response({"message": "Sessão resetada e excluída com sucesso."}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"WAHA: Erro ao deletar sessão WhatsApp. Erro: {str(e)}")
            return Response(
                {"error": "Erro ao tentar limpar a sessão do WhatsApp."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class WahaPairingCodeView(APIView):
    """
    View responsável por gerar o código numérico de 8 dígitos para parelhamento.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        waha_url = getattr(settings, 'WAHA_API_URL', 'http://waha:3000').rstrip('/')
        
        if hasattr(request.user, 'empresa') and request.user.empresa:
            waha_session = f"tenant_{request.user.empresa.id}"
        else:
            return Response({"error": "Usuário não vinculado a uma empresa."}, status=status.HTTP_400_BAD_REQUEST)
            
        phone_number = request.data.get("phoneNumber", "")
        if not phone_number:
            return Response({"error": "O número de telefone é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
            
        import re
        clean_phone = re.sub(r'\D', '', str(phone_number))
        if not clean_phone:
            return Response({"error": "Número de telefone inválido."}, status=status.HTTP_400_BAD_REQUEST)
            
        if not clean_phone.startswith('55'):
            clean_phone = f"55{clean_phone}"

        api_key = getattr(settings, 'WAHA_API_KEY', '') or os.getenv('WAHA_API_KEY', '')

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if api_key:
            headers["X-Api-Key"] = api_key

        # Garante que a sessão existe e está iniciada
        start_session_url = f"{waha_url}/api/sessions"
        session_payload = {"name": waha_session}
        
        try:
            resp1 = requests.post(start_session_url, json=session_payload, headers=headers, timeout=30)
            start_engine_url = f"{waha_url}/api/sessions/{waha_session}/start"
            requests.post(start_engine_url, headers=headers, timeout=30)
        except Exception as e:
            logger.error(f"WAHA: Falha ao tentar iniciar sessão {waha_session} no pairing code. Erro: {str(e)}")
            return Response(
                {"error": "Não foi possível conectar ao motor do WhatsApp para gerar o código."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Solicita o código de parelhamento
        request_code_url = f"{waha_url}/api/{waha_session}/auth/request-code"
        payload = {"phoneNumber": clean_phone}
        
        try:
            code_resp = requests.post(request_code_url, json=payload, headers=headers, timeout=30)
            
            if code_resp.status_code in [200, 201]:
                data = code_resp.json()
                return Response({
                    "status": "WAITING_FOR_SCAN",
                    "code": data.get("code", ""),
                    "message": "Código gerado com sucesso. Insira-o no seu WhatsApp."
                }, status=status.HTTP_200_OK)
            elif code_resp.status_code == 422:
                # Sessão provavelmente já conectada
                return Response({
                    "error": "Não é possível gerar o código. O WhatsApp pode já estar conectado ou em outro estado. Desconecte e tente novamente."
                }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            else:
                logger.error(f"WAHA Code Error: {code_resp.status_code} - {code_resp.text}")
                # Retorna o texto original da WAHA para sabermos qual é a limitação do container deles
                error_msg = "Erro ao gerar código."
                try:
                    err_data = code_resp.json()
                    error_msg = err_data.get("message", code_resp.text)
                except:
                    error_msg = code_resp.text
                return Response({
                    "error": f"WAHA Error ({code_resp.status_code}): {error_msg}"
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"WAHA: Falha ao solicitar pairing code. Erro: {str(e)}")
            return Response(
                {"error": "Falha de comunicação interna ao solicitar código."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class WahaSessionStatusView(APIView):
    """
    Retorna apenas o status atual da sessão sem tentar buscar QR Code (para evitar side-effects).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        waha_url = getattr(settings, 'WAHA_API_URL', 'http://waha:3000').rstrip('/')
        
        if hasattr(request.user, 'empresa') and request.user.empresa:
            waha_session = f"tenant_{request.user.empresa.id}"
        else:
            return Response({"error": "Usuário não vinculado a uma empresa."}, status=status.HTTP_400_BAD_REQUEST)

        api_key = getattr(settings, 'WAHA_API_KEY', '') or os.getenv('WAHA_API_KEY', '')

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if api_key:
            headers["X-Api-Key"] = api_key
            
        status_url = f"{waha_url}/api/sessions"
        try:
            status_response = requests.get(status_url, headers=headers, timeout=30)
            if status_response.ok:
                sessions = status_response.json()
                my_session = next((s for s in sessions if s.get('name') == waha_session), None)
                
                if not my_session:
                    return Response({"status": "STOPPED", "message": "Sessão não iniciada."}, status=status.HTTP_200_OK)
                    
                current_status = my_session.get('status', 'DESCONHECIDO')
                return Response({
                    "status": current_status,
                    "message": "Status atual da sessão."
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Falha ao obter status."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"WAHA: Falha ao checar status. {e}")
            return Response({"error": "Falha de comunicação."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
