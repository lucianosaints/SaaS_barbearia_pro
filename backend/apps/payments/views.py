import datetime
import logging
import os
from decimal import Decimal, InvalidOperation

import mercadopago
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsTenantAdmin
from .models import CobrancaAssinatura

logger = logging.getLogger(__name__)


class MercadoPagoWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data.get('data', {})
        payment_id = data.get('id') or request.query_params.get('data.id') or request.query_params.get('id')
        if not payment_id:
            return Response({'status': 'ignored', 'reason': 'no payment id provided'})

        token = getattr(settings, 'MERCADOPAGO_ACCESS_TOKEN', '') or os.environ.get('MERCADOPAGO_ACCESS_TOKEN', '')
        if not token:
            logger.error('MERCADOPAGO_ACCESS_TOKEN nao configurado no backend.')
            return Response({'status': 'error'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            payment_info = mercadopago.SDK(token).payment().get(payment_id)
            if payment_info.get('status') != 200:
                logger.warning('[Webhook MP] Consulta do pagamento falhou: HTTP %s', payment_info.get('status'))
                return Response({'status': 'retry'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            payment_data = payment_info.get('response', {})
            if payment_data.get('status') != 'approved':
                return Response({'status': 'ignored'})

            external_reference = payment_data.get('external_reference')
            amount = Decimal(str(payment_data.get('transaction_amount'))).quantize(Decimal('0.01'))
            currency = payment_data.get('currency_id')

            with transaction.atomic():
                cobranca = CobrancaAssinatura.objects.select_for_update().select_related('empresa').get(
                    external_reference=external_reference
                )
                if cobranca.status == 'APROVADA':
                    return Response({'status': 'success'})
                if amount != cobranca.valor or currency != cobranca.moeda:
                    logger.warning('[Webhook MP] Valor ou moeda divergente para cobranca %s', cobranca.pk)
                    cobranca.status = 'REJEITADA'
                    cobranca.save(update_fields=['status'])
                    return Response({'status': 'ignored'})

                empresa = cobranca.empresa
                today = datetime.date.today()
                base_date = (
                    empresa.data_vencimento_assinatura
                    if empresa.assinatura_ativa and empresa.data_vencimento_assinatura and empresa.data_vencimento_assinatura > today
                    else today
                )
                empresa.assinatura_ativa = True
                empresa.em_trial = False
                empresa.data_vencimento_assinatura = base_date + datetime.timedelta(days=30 * cobranca.meses)
                empresa.save(update_fields=['assinatura_ativa', 'em_trial', 'data_vencimento_assinatura'])
                cobranca.status = 'APROVADA'
                cobranca.mercado_pago_payment_id = str(payment_id)
                cobranca.processada_em = timezone.now()
                cobranca.save(update_fields=['status', 'mercado_pago_payment_id', 'processada_em'])
        except (CobrancaAssinatura.DoesNotExist, InvalidOperation, TypeError):
            logger.warning('[Webhook MP] Cobranca invalida ou desconhecida.')
            return Response({'status': 'ignored'})
        except Exception:
            logger.exception('[Webhook MP] Erro ao processar webhook.')
            return Response({'status': 'retry'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({'status': 'success'})


class CriarPagamentoAssinaturaView(APIView):
    permission_classes = [IsTenantAdmin]

    def post(self, request, *args, **kwargs):
        if os.getenv('PERMITIR_PAGAMENTOS', 'False').lower() != 'true':
            return Response(
                {'erro': 'A pagina de pagamentos esta temporariamente em manutencao.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            meses = int(request.data.get('meses', 1))
        except (ValueError, TypeError):
            return Response({'error': 'Quantidade de meses invalida.'}, status=status.HTTP_400_BAD_REQUEST)
        if meses not in (1, 2, 3, 6, 12):
            return Response({'error': 'Escolha 1, 2, 3, 6 ou 12 meses.'}, status=status.HTTP_400_BAD_REQUEST)

        empresa = request.user.empresa
        valor_total = Decimal('49.99') * meses
        cobranca = CobrancaAssinatura.objects.create(empresa=empresa, meses=meses, valor=valor_total)
        try:
            from services.mercado_pago_service import criar_pagamento_pix
            dados_pix = criar_pagamento_pix(
                str(cobranca.external_reference), empresa.nome, valor_total, request.user.email
            )
            return Response(dados_pix, status=status.HTTP_201_CREATED)
        except Exception:
            cobranca.status = 'ERRO'
            cobranca.save(update_fields=['status'])
            logger.exception('Falha ao criar pagamento no Mercado Pago para cobranca %s', cobranca.pk)
            return Response({'error': 'Nao foi possivel iniciar o pagamento.'}, status=status.HTTP_502_BAD_GATEWAY)
