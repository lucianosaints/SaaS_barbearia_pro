import logging

from apps.agenda.background import enqueue_notification
from services.waha_service import enviar_mensagem_whatsapp

from .models import Pedido


logger = logging.getLogger(__name__)


def _moeda(valor):
    return f'R$ {valor:.2f}'.replace('.', ',')


def _resumo(pedido):
    itens = '\n'.join(f'- {item.quantidade}x {item.nome_produto}: {_moeda(item.subtotal)}' for item in pedido.itens.all())
    return f'Pedido #{pedido.id}\n{itens}\nTotal: {_moeda(pedido.total)}\nPagamento: {pedido.get_forma_pagamento_display()}'


def _executar(callback):
    enqueue_notification(callback)


def notificar_novo_pedido(pedido_id):
    def enviar():
        pedido = Pedido.objects.select_related('empresa').prefetch_related('itens').get(pk=pedido_id)
        mensagem = f'Novo pedido para retirada!\n\n{_resumo(pedido)}\nCliente: {pedido.cliente_nome}\nWhatsApp: {pedido.cliente_telefone}'
        session = f'tenant_{pedido.empresa_id}'
        telefones = pedido.empresa.usuarios.filter(tipo='ADMINISTRADOR', is_active=True).exclude(telefone='').values_list('telefone', flat=True)
        for telefone in set(filter(None, telefones)):
            enviar_mensagem_whatsapp(telefone, mensagem, waha_session=session)

        enviar_mensagem_whatsapp(
            pedido.cliente_telefone,
            f'Recebemos sua reserva de produtos.\n\n{_resumo(pedido)}\nO salão confirmará a retirada pelo WhatsApp.',
            waha_session=session,
        )

    _executar(enviar)


def notificar_status_pedido(pedido_id, _status_anterior=None):
    def enviar():
        pedido = Pedido.objects.select_related('empresa').prefetch_related('itens').get(pk=pedido_id)
        mensagem = f'Atualização do pedido #{pedido.id}: {pedido.get_status_display()}.'
        if pedido.status == 'AGUARDANDO_SINAL':
            mensagem += f'\nSinal de 50%: {_moeda(pedido.valor_sinal)}\nPIX: {pedido.empresa.chave_pix}\nBeneficiário: {pedido.empresa.beneficiario_pix}\nSaldo na retirada: {_moeda(pedido.total - pedido.valor_sinal)}'
        elif pedido.status == 'PRONTO':
            mensagem += '\nSeu pedido está pronto para retirada no salão.'
        elif pedido.status == 'CANCELADO':
            mensagem += '\nA reserva foi cancelada. Fale com o salão se precisar de ajuda.'
        enviar_mensagem_whatsapp(pedido.cliente_telefone, mensagem, waha_session=f'tenant_{pedido.empresa_id}')

    _executar(enviar)
