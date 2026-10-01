import logging

from apps.agenda.background import enqueue_notification
from services.waha_service import enviar_mensagem_whatsapp

from .models import Pedido


logger = logging.getLogger(__name__)


def _moeda(valor):
    return f'R$ {valor:.2f}'.replace('.', ',')


def _resumo(pedido):
    itens = '\n'.join(f'• {item.quantidade}x {item.nome_produto}\n  {_moeda(item.subtotal)}' for item in pedido.itens.all())
    return f'*PEDIDO #{pedido.id}*\n━━━━━━━━━━━━━━\n{itens}\n━━━━━━━━━━━━━━\n*Total:* {_moeda(pedido.total)}\n*Forma de pagamento:* {pedido.get_forma_pagamento_display()}'


def _executar(callback):
    enqueue_notification(callback)


def notificar_novo_pedido(pedido_id):
    def enviar():
        pedido = Pedido.objects.select_related('empresa').prefetch_related('itens').get(pk=pedido_id)
        mensagem = f'🛍️ *NOVO PEDIDO PARA RETIRADA*\n\n{_resumo(pedido)}\n\n*Cliente:* {pedido.cliente_nome}\n*WhatsApp:* {pedido.cliente_telefone}'
        session = f'tenant_{pedido.empresa_id}'
        telefones = pedido.empresa.usuarios.filter(tipo='ADMINISTRADOR', is_active=True).exclude(telefone='').values_list('telefone', flat=True)
        for telefone in set(filter(None, telefones)):
            enviar_mensagem_whatsapp(telefone, mensagem, waha_session=session)

        enviar_mensagem_whatsapp(
            pedido.cliente_telefone,
            f'✅ *RESERVA RECEBIDA*\n\n{_resumo(pedido)}\n\nO salão confirmará a reserva e avisará por aqui quando estiver pronta para retirada.',
            waha_session=session,
        )

    _executar(enviar)


def notificar_status_pedido(pedido_id, _status_anterior=None):
    def enviar():
        pedido = Pedido.objects.select_related('empresa').prefetch_related('itens').get(pk=pedido_id)
        mensagem = f'🔔 *ATUALIZAÇÃO DO PEDIDO #{pedido.id}*\n\n*Status:* {pedido.get_status_display()}'
        if pedido.status == 'AGUARDANDO_SINAL':
            mensagem += f'\n\n💳 *Sinal para reservar*\n*Valor (50%):* {_moeda(pedido.valor_sinal)}\n*Chave PIX:* `{pedido.empresa.chave_pix}`\n*Beneficiário:* {pedido.empresa.beneficiario_pix}\n*Saldo na retirada:* {_moeda(pedido.total - pedido.valor_sinal)}\n\nEnvie o comprovante ao salão para confirmar a reserva.'
        elif pedido.status == 'PRONTO':
            mensagem += '\nSeu pedido está pronto para retirada no salão.'
        elif pedido.status == 'CANCELADO':
            mensagem += '\nA reserva foi cancelada. Fale com o salão se precisar de ajuda.'
        enviar_mensagem_whatsapp(pedido.cliente_telefone, mensagem, waha_session=f'tenant_{pedido.empresa_id}')

    _executar(enviar)
