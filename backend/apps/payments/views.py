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
                        parts = str(external_reference).split('_')
                        empresa_id = parts[0]
                        meses_pagos = int(parts[1]) if len(parts) > 1 else 1

                        # Identifica a empresa pelo ID
                        empresa = Empresa.objects.get(id=empresa_id)
                        
                        # Atualiza os dados da assinatura (Renovação ou Ativação)
                        import datetime
                        
                        if empresa.assinatura_ativa and empresa.data_vencimento_assinatura and empresa.data_vencimento_assinatura > datetime.date.today():
                            base_date = empresa.data_vencimento_assinatura
                        else:
                            base_date = datetime.date.today()
                            
                        empresa.assinatura_ativa = True
                        empresa.em_trial = False
                        empresa.data_vencimento_assinatura = base_date + datetime.timedelta(days=30 * meses_pagos)
                        empresa.save(update_fields=['assinatura_ativa', 'em_trial', 'data_vencimento_assinatura'])
                        print(f"[Webhook MP] Assinatura ativada/renovada com sucesso ({meses_pagos} meses) para a empresa: {empresa.nome}. Vencimento: {empresa.data_vencimento_assinatura}")
                        
                    except Empresa.DoesNotExist:
                        print(f"[Webhook MP] Empresa não encontrada com external_reference: {external_reference}")
                        pass
                
        except Exception as e:
            print(f"[Webhook MP] Erro ao processar webhook: {e}")

        # Sempre retorne 200/201 OK para o Mercado Pago não tentar reenviar indefinidamente
        return Response({"status": "success"}, status=status.HTTP_200_OK)

class CriarPagamentoAssinaturaView(APIView):
    """
    Gera o link de pagamento do Mercado Pago para a assinatura da empresa logada.
    """
    def post(self, request, *args, **kwargs):
        from django.http import JsonResponse
        import os
        
        PERMITIR_PAGAMENTOS = os.getenv('PERMITIR_PAGAMENTOS', 'True').lower() == 'true'
        if not PERMITIR_PAGAMENTOS:
            return JsonResponse(
                {"erro": "A página de pagamentos está temporariamente em manutenção. Tente novamente mais tarde."}, 
                status=403
            )

        usuario = request.user
        if not hasattr(usuario, 'empresa') or not usuario.empresa:
            return Response({"error": "Usuário não pertence a nenhuma empresa."}, status=status.HTTP_400_BAD_REQUEST)
            
        empresa = usuario.empresa
        
        meses_str = request.data.get('meses', 1)
        try:
            meses = int(meses_str)
        except (ValueError, TypeError):
            meses = 1
            
        valor_base = 1.00
        valor_total = round(valor_base * meses, 2)
        
        external_reference = f"{empresa.id}_{meses}"
        
        try:
            from services.mercado_pago_service import criar_pagamento_pix
            dados_pix = criar_pagamento_pix(external_reference, empresa.nome, valor_total, usuario.email)
            return Response(dados_pix, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

