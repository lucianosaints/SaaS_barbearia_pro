import datetime
from django.http import JsonResponse

class SubscriptionMiddleware:
    """
    Middleware para interceptar requisições e verificar o status da assinatura
    da empresa. Se estiver inadimplente, bloqueia o acesso à API retornando 402.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ignora rotas que não exigem assinatura ou que servem justamente para regularizar
        exempt_paths = [
            '/api/auth/',
            '/api/assinaturas/',
            '/api/accounts/',
            '/admin/',
            '/media/',
            '/static/'
        ]
        
        if any(request.path.startswith(path) for path in exempt_paths):
            return self.get_response(request)

        # Se for requisição de API
        if request.path.startswith('/api/'):
            user = getattr(request, 'user', None)
            
            # Tenta autenticar via JWT caso o user do Django esteja anônimo
            if not user or not user.is_authenticated:
                try:
                    from rest_framework_simplejwt.authentication import JWTAuthentication
                    jwt_auth = JWTAuthentication()
                    auth_result = jwt_auth.authenticate(request)
                    if auth_result:
                        user, _ = auth_result
                except Exception:
                    pass

            if user and user.is_authenticated:
                # Apenas verifica quem tem empresa atrelada
                if hasattr(user, 'empresa') and user.empresa:
                    empresa = user.empresa
                    is_blocked = False
                    
                    if empresa.assinatura_ativa:
                        # Verifica se o vencimento passou
                        if empresa.data_vencimento_assinatura and datetime.date.today() > empresa.data_vencimento_assinatura:
                            empresa.assinatura_ativa = False
                            empresa.save(update_fields=['assinatura_ativa'])
                            is_blocked = True
                    else:
                        if not empresa.em_trial:
                            is_blocked = True
                        elif empresa.data_fim_trial and datetime.date.today() > empresa.data_fim_trial:
                            is_blocked = True
                    
                    if is_blocked:
                        return JsonResponse({
                            "error": "Assinatura inativa ou período de teste expirado.",
                            "code": "SUBSCRIPTION_REQUIRED"
                        }, status=402)
                    
        return self.get_response(request)
