import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import api from '../services/api';

const moeda = (valor) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(valor || 0));
const pagamentos = { PIX: 'Pix', DINHEIRO: 'Dinheiro', DEBITO: 'Cartão de débito', CREDITO: 'Cartão de crédito' };
const rotulosStatus = {
  AGUARDANDO_CONFIRMACAO: 'Aguardando confirmação', CONFIRMADO: 'Reserva confirmada',
  AGUARDANDO_SINAL: 'Aguardando sinal', SINAL_CONFIRMADO: 'Sinal confirmado',
  PRONTO: 'Pronto para retirada', CONCLUIDO: 'Concluído', CANCELADO: 'Cancelado',
};

export default function TicketPedido() {
  const { token } = useParams();
  const [pedido, setPedido] = useState(null);
  const [erro, setErro] = useState('');
  useEffect(() => { api.get(`/api/pedidos/ticket/${token}/`).then(({ data }) => setPedido(data)).catch(() => setErro('Ticket não encontrado ou expirado.')); }, [token]);
  if (erro) return <div className="mx-auto max-w-xl p-8 text-center text-rose-400">{erro}</div>;
  if (!pedido) return <div className="p-16 text-center text-text-muted">Carregando ticket...</div>;

  return (
    <main className="mx-auto w-full max-w-2xl p-3 sm:p-8">
      <article className="overflow-hidden rounded-3xl border border-gold/25 bg-background-paper shadow-2xl">
        <header className="bg-gradient-to-br from-gold/20 via-background-paper to-background-darker p-6 sm:p-8">
          <div className="flex items-start justify-between gap-4">
            <div><p className="text-[10px] font-bold uppercase tracking-[0.28em] text-gold">Comprovante de reserva</p><h1 className="mt-2 text-3xl font-black">Pedido #{pedido.id}</h1><p className="mt-1 text-sm text-text-muted">{pedido.empresa_nome}</p></div>
            <span className="rounded-full border border-gold/30 bg-gold/10 px-3 py-2 text-right text-[11px] font-bold text-gold">{rotulosStatus[pedido.status] || pedido.status}</span>
          </div>
        </header>
        <div className="space-y-6 p-5 sm:p-8">
          <section><h2 className="mb-3 text-xs font-bold uppercase tracking-wider text-text-muted">Itens reservados</h2><div className="divide-y divide-white/10 rounded-2xl border border-white/10 bg-background-darker/50 px-4">{pedido.itens.map((item) => <div key={`${item.produto}-${item.nome_produto}`} className="flex items-start justify-between gap-4 py-4"><div className="min-w-0"><span className="mr-2 inline-flex rounded-md bg-gold/10 px-2 py-1 text-xs font-bold text-gold">{item.quantidade}x</span><span className="break-words text-sm">{item.nome_produto}</span></div><strong className="shrink-0 text-sm">{moeda(item.subtotal)}</strong></div>)}</div></section>
          <section className="grid gap-3 sm:grid-cols-2"><div className="rounded-2xl border border-white/10 p-4"><p className="text-xs text-text-muted">Forma de pagamento</p><p className="mt-1 font-bold">{pagamentos[pedido.forma_pagamento] || pedido.forma_pagamento}</p></div><div className="rounded-2xl border border-gold/25 bg-gold/5 p-4"><p className="text-xs text-text-muted">Total do pedido</p><p className="mt-1 text-xl font-black text-gold">{moeda(pedido.total)}</p></div></section>
          {pedido.sinal_solicitado && <section className="rounded-2xl border border-emerald-500/25 bg-emerald-500/10 p-5"><h2 className="font-bold text-emerald-300">Sinal PIX para reservar</h2><div className="mt-4 grid gap-3 sm:grid-cols-2"><div><p className="text-xs text-text-muted">Sinal de 50%</p><strong>{moeda(pedido.valor_sinal)}</strong></div><div><p className="text-xs text-text-muted">Saldo na retirada</p><strong>{moeda(pedido.saldo_restante)}</strong></div></div><div className="mt-4 rounded-xl bg-black/20 p-4"><p className="text-xs text-text-muted">Chave PIX</p><p className="mt-1 break-all font-mono font-bold text-emerald-300">{pedido.chave_pix}</p><p className="mt-3 text-xs text-text-muted">Beneficiário</p><p className="font-semibold">{pedido.beneficiario_pix}</p></div><p className="mt-3 text-xs text-text-muted">Envie o comprovante ao salão para confirmar sua reserva.</p></section>}
          <p className="rounded-xl bg-white/5 p-4 text-xs leading-5 text-text-muted">Guarde este link para acompanhar o pedido. As atualizações também serão enviadas ao WhatsApp informado.</p>
          <Link to="/" className="btn-gold-outline block py-3 text-center text-sm">Voltar ao SalaoPro</Link>
        </div>
      </article>
    </main>
  );
}
