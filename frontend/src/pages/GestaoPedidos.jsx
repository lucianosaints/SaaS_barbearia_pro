import React, { useCallback, useEffect, useState } from 'react';
import api from '../services/api';

const moeda = (valor) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(valor || 0));
const rotulos = { AGUARDANDO_CONFIRMACAO: 'Aguardando confirmação', CONFIRMADO: 'Confirmado', AGUARDANDO_SINAL: 'Aguardando sinal', SINAL_CONFIRMADO: 'Sinal confirmado', PRONTO: 'Pronto para retirada', CONCLUIDO: 'Concluído', CANCELADO: 'Cancelado' };
const acoes = {
  AGUARDANDO_CONFIRMACAO: [['CONFIRMADO', 'Confirmar'], ['AGUARDANDO_SINAL', 'Solicitar sinal PIX'], ['CANCELADO', 'Cancelar']],
  CONFIRMADO: [['AGUARDANDO_SINAL', 'Solicitar sinal PIX'], ['PRONTO', 'Marcar pronto'], ['CANCELADO', 'Cancelar']],
  AGUARDANDO_SINAL: [['SINAL_CONFIRMADO', 'Confirmar sinal'], ['CANCELADO', 'Cancelar']],
  SINAL_CONFIRMADO: [['PRONTO', 'Marcar pronto'], ['CANCELADO', 'Cancelar']],
  PRONTO: [['CONCLUIDO', 'Concluir'], ['CANCELADO', 'Cancelar']],
};

export default function GestaoPedidos() {
  const [pedidos, setPedidos] = useState([]);
  const [mensagem, setMensagem] = useState('');
  const [alterando, setAlterando] = useState(null);
  const carregar = useCallback(async () => {
    try { const { data } = await api.get('/api/pedidos/'); setPedidos(data.results || data); }
    catch { setMensagem('Não foi possível carregar os pedidos.'); }
  }, []);
  useEffect(() => { carregar(); }, [carregar]);
  const mudarStatus = async (pedido, status) => {
    if (status === 'CANCELADO' && !window.confirm(`Cancelar o pedido #${pedido.id} e devolver o estoque?`)) return;
    setAlterando(pedido.id); setMensagem('');
    try { await api.patch(`/api/pedidos/${pedido.id}/status/`, { status }); await carregar(); }
    catch (error) { setMensagem(error.response?.data?.status || 'Não foi possível atualizar o pedido.'); }
    finally { setAlterando(null); }
  };
  const regenerarTicket = async (pedido) => {
    setAlterando(pedido.id); setMensagem('');
    try {
      const { data } = await api.post(`/api/pedidos/${pedido.id}/regenerar-ticket/`);
      const link = `${window.location.origin}${data.ticket_url.replace('/api/pedidos/ticket/', '/pedido/').replace(/\/$/, '')}`;
      await navigator.clipboard.writeText(link);
      setMensagem(`Novo link do pedido #${pedido.id} copiado. O link anterior deixou de funcionar.`);
      await carregar();
    } catch { setMensagem('Não foi possível regenerar e copiar o link do ticket.'); }
    finally { setAlterando(null); }
  };
  return <section className="space-y-4"><div><h2 className="text-xl font-bold">Pedidos para retirada</h2><p className="mt-1 text-xs text-text-muted">Confirme reservas, solicite o sinal PIX de 50% e acompanhe a retirada.</p></div>{mensagem && <p className="rounded-xl border border-gold/20 bg-gold/10 p-3 text-sm text-gold-light">{mensagem}</p>}<div className="grid gap-4 lg:grid-cols-2">{pedidos.map((pedido) => <article key={pedido.id} className="rounded-2xl border border-white/10 bg-background-paper p-5"><div className="flex items-start justify-between gap-3"><div><h3 className="font-bold">Pedido #{pedido.id} · {pedido.cliente_nome}</h3><p className="text-xs text-text-muted">{pedido.cliente_telefone} · {pedido.forma_pagamento}</p></div><span className="rounded-full bg-gold/10 px-3 py-1 text-[10px] font-bold text-gold">{rotulos[pedido.status]}</span></div><div className="my-4 space-y-1 text-sm">{pedido.itens.map((item) => <div key={item.produto} className="flex justify-between"><span>{item.quantidade}x {item.nome_produto}</span><span>{moeda(item.subtotal)}</span></div>)}</div><div className="flex justify-between border-t border-white/10 pt-3"><span>Total</span><strong className="text-gold">{moeda(pedido.total)}</strong></div>{pedido.sinal_solicitado && <p className="mt-2 text-xs text-text-muted">Sinal de 50%: {moeda(pedido.valor_sinal)} · Saldo: {moeda(pedido.saldo_restante)}</p>}<div className="mt-4 flex flex-wrap gap-2">{(acoes[pedido.status] || []).map(([status, texto]) => <button key={status} disabled={alterando === pedido.id} onClick={() => mudarStatus(pedido, status)} className={status === 'CANCELADO' ? 'rounded-lg border border-rose-500/30 px-3 py-2 text-xs text-rose-300' : 'btn-gold-outline px-3 py-2 text-xs'}>{texto}</button>)}<button disabled={alterando === pedido.id} onClick={() => regenerarTicket(pedido)} className="rounded-lg border border-white/15 px-3 py-2 text-xs text-text-muted hover:text-white">Regenerar link</button></div></article>)}{!pedidos.length && <p className="py-8 text-sm text-text-muted">Nenhum pedido recebido ainda.</p>}</div></section>;
}
