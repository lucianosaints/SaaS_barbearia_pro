import os
import mercadopago
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.conf import settings
from apps.tenants.models import Empresa

class MercadoPagoWebhookView(APIView):
    """
    Recebe as notificações (webhooks) do Mercado Pago sobre atualizações de pagamento.
    Se um pagamento de assinatura for aprovado, atualiza o status da Empresa.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        topic = request.query_params.get('topic') or request.data.get('type')
        action = request.data.get('action')
        data = request.data.get('data', {})
        payment_id = data.get('id')
        
        # O MP manda webhooks para criar pagamentos (payment.created) ou atualizar (payment.updated)
        # Vamos focar apenas no ID fornecido para buscar diretamente na API deles.
        if not payment_id:
            # Em alguns formatos, o ID vem em lugares diferentes.
            payment_id = request.query_params.get('data.id') or request.query_params.get('id')
            
        if not payment_id:
            return Response({"status": "ignored", "reason": "no payment id provided"}, status=status.HTTP_200_OK)

        # 1. Configurar SDK do Mercado Pago
        mp_access_token = getattr(settings, 'MERCADOPAGO_ACCESS_TOKEN', os.environ.get('MERCADOPAGO_ACCESS_TOKEN', ''))
        if not mp_access_token:
            print("Erro: MERCADOPAGO_ACCESS_TOKEN não configurado no backend.")
            return Response({"status": "error", "message": "MP token not configured"}, status=status.HTTP_200_OK)
            
        sdk = mercadopago.SDK(mp_access_token)

        try:
            # 2. Consultar o pagamento real na API do Mercado Pago (Prevenção de Fraudes)
            payment_info = sdk.payment().get(payment_id)
            
            if payment_info["status"] == 200:
                payment_data = payment_info["response"]
                payment_status = payment_data.get("status")
                external_reference = payment_data.get("external_reference")
                
                # 3. Se estiver aprovado e tiver a referência da empresa
                if payment_status == "approved" and external_reference:
                    try:
                        # Identifica a empresa pelo ID ou slug (assumindo ID neste caso)
                        empresa = Empresa.objects.get(id=external_reference)
                        
                        # Atualiza os dados da assinatura
                        if not empresa.assinatura_ativa or empresa.em_trial:
                            empresa.assinatura_ativa = True
                            empresa.em_trial = False
                            empresa.save(update_fields=['assinatura_ativa', 'em_trial'])
                            print(f"[Webhook MP] Assinatura ativada com sucesso para a empresa: {empresa.nome}")
                        
                    except Empresa.DoesNotExist:
                        print(f"[Webhook MP] Empresa não encontrada com external_reference: {external_reference}")
                        pass
                
        except Exception as e:
            print(f"[Webhook MP] Erro ao processar webhook: {e}")

        # Sempre retorne 200/201 OK para o Mercado Pago não tentar reenviar indefinidamente
        return Response({"status": "success"}, status=status.HTTP_200_OK)
