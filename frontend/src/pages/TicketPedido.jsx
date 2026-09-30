import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import api from '../services/api';

const moeda = (valor) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(valor || 0));

export default function TicketPedido() {
  const { token } = useParams();
  const [pedido, setPedido] = useState(null);
  const [erro, setErro] = useState('');
  useEffect(() => { api.get(`/api/pedidos/ticket/${token}/`).then(({ data }) => setPedido(data)).catch(() => setErro('Ticket não encontrado.')); }, [token]);
  if (erro) return <div className="mx-auto max-w-xl p-8 text-center text-rose-400">{erro}</div>;
  if (!pedido) return <div className="p-16 text-center text-text-muted">Carregando ticket...</div>;
  return <section className="mx-auto w-full max-w-2xl p-4 sm:p-8"><article className="rounded-2xl border border-gold/25 bg-background-paper p-6 shadow-2xl"><div className="border-b border-white/10 pb-5"><p className="text-xs uppercase tracking-[0.25em] text-gold">Ticket de retirada</p><h1 className="mt-2 text-2xl font-bold">Pedido #{pedido.id}</h1><p className="mt-1 text-sm text-text-muted">{pedido.empresa_nome} · {pedido.status.replaceAll('_', ' ')}</p></div><div className="my-5 space-y-3">{pedido.itens.map((item) => <div key={item.produto} className="flex justify-between gap-3"><span>{item.quantidade}x {item.nome_produto}</span><strong>{moeda(item.subtotal)}</strong></div>)}</div><div className="space-y-2 border-t border-white/10 pt-5"><div className="flex justify-between text-lg"><span>Total</span><strong className="text-gold">{moeda(pedido.total)}</strong></div><p className="text-sm text-text-muted">Pagamento: {pedido.forma_pagamento}</p>{pedido.sinal_solicitado && <div className="mt-4 rounded-xl border border-gold/20 bg-gold/10 p-4 text-sm"><p><strong>Sinal de 50%:</strong> {moeda(pedido.valor_sinal)}</p><p><strong>Saldo restante:</strong> {moeda(pedido.saldo_restante)}</p><p className="mt-2 break-all"><strong>PIX:</strong> {pedido.chave_pix}</p><p><strong>Beneficiário:</strong> {pedido.beneficiario_pix}</p></div>}</div><p className="mt-6 text-xs text-text-muted">Guarde este link. O salão enviará atualizações também para o WhatsApp informado.</p><Link to="/" className="btn-gold-outline mt-5 block py-3 text-center text-sm">Voltar ao SalaoPro</Link></article></section>;
}
