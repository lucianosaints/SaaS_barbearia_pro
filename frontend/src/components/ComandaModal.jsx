import React, { useEffect, useState } from 'react';
import api from '../services/api';

const moeda = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(v || 0));

export default function ComandaModal({ agendamento, onClose, onUpdated }) {
  const [comanda, setComanda] = useState(null);
  const [produtos, setProdutos] = useState([]);
  const [produto, setProduto] = useState('');
  const [quantidade, setQuantidade] = useState(1);
  const [pagamento, setPagamento] = useState(agendamento?.metodo_pagamento || 'PIX');
  const [desconto, setDesconto] = useState('0');
  const [erro, setErro] = useState('');
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    Promise.all([api.post('/api/comandas/', { agendamento: agendamento.id }), api.get('/api/produtos/', { params: { page_size: 24 } })])
      .then(([c, p]) => { setComanda(c.data); setDesconto(c.data.desconto); setProdutos(p.data.results || p.data); })
      .catch((e) => setErro(e.response?.data?.detail || 'Não foi possível abrir a comanda.'));
  }, [agendamento.id]);

  const executar = async (acao) => { setSalvando(true); setErro(''); try { const { data } = await acao(); setComanda(data); onUpdated?.(); } catch (e) { const d = e.response?.data; setErro(typeof d === 'object' ? Object.values(d).flat().join(' ') : 'Operação não concluída.'); } finally { setSalvando(false); } };
  const adicionar = () => executar(() => api.post(`/api/comandas/${comanda.id}/adicionar-produto/`, { produto: Number(produto), quantidade: Number(quantidade) }));
  const aplicarDesconto = () => executar(() => api.patch(`/api/comandas/${comanda.id}/`, { desconto }));
  const remover = (id) => executar(() => api.delete(`/api/comandas/${comanda.id}/produtos/${id}/`));
  const fechar = () => { if (window.confirm(`Fechar a comanda por ${moeda(comanda.total)}?`)) executar(() => api.post(`/api/comandas/${comanda.id}/fechar/`, { metodo_pagamento: pagamento })); };

  return <div className="fixed inset-0 z-[130] flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm"><div className="max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-gold/20 bg-background-paper p-5"><div className="flex justify-between"><div><h2 className="text-xl font-bold text-gold">Comanda #{comanda?.id || '...'}</h2><p className="text-xs text-text-muted">{agendamento.cliente_nome} · {agendamento.profissional_nome}</p></div><button onClick={onClose}>✕</button></div>{erro && <p className="my-3 rounded-lg bg-rose-500/10 p-3 text-xs text-rose-300">{erro}</p>}{!comanda ? <p className="py-10 text-center text-sm">Carregando...</p> : <div className="mt-5 space-y-5"><div><h3 className="mb-2 text-xs font-bold uppercase text-text-muted">Serviços</h3>{comanda.itens_servico.map(i => <div key={i.id} className="flex justify-between border-b border-white/5 py-2 text-sm"><span>{i.quantidade}x {i.nome}</span><span>{moeda(i.subtotal)}</span></div>)}</div><div><h3 className="mb-2 text-xs font-bold uppercase text-text-muted">Produtos</h3>{comanda.itens_produto.map(i => <div key={i.id} className="flex items-center justify-between border-b border-white/5 py-2 text-sm"><span>{i.quantidade}x {i.nome}</span><div className="flex items-center gap-3"><span>{moeda(i.subtotal)}</span>{comanda.status === 'ABERTA' && <button onClick={() => remover(i.id)} className="text-xs text-rose-400">Remover</button>}</div></div>)}{comanda.status === 'ABERTA' && <div className="mt-3 flex gap-2"><select value={produto} onChange={e => setProduto(e.target.value)} className="min-w-0 flex-1 rounded-lg bg-background-darker p-2 text-sm"><option value="">Selecionar produto</option>{produtos.map(p => <option key={p.id} value={p.id}>{p.nome} · {moeda(p.preco_atual)}</option>)}</select><input type="number" min="1" value={quantidade} onChange={e => setQuantidade(e.target.value)} className="w-16 rounded-lg bg-background-darker p-2"/><button disabled={!produto || salvando} onClick={adicionar} className="btn-gold px-3 text-xs">Adicionar</button></div>}</div><div className="grid gap-3 sm:grid-cols-2"><label className="text-xs">Desconto<input type="number" min="0" step="0.01" disabled={comanda.status !== 'ABERTA'} value={desconto} onChange={e => setDesconto(e.target.value)} className="mt-1 w-full rounded-lg bg-background-darker p-3"/></label><label className="text-xs">Pagamento<select disabled={comanda.status !== 'ABERTA'} value={pagamento} onChange={e => setPagamento(e.target.value)} className="mt-1 w-full rounded-lg bg-background-darker p-3"><option value="PIX">PIX</option><option value="DINHEIRO">Dinheiro</option><option value="DEBITO">Débito</option><option value="CREDITO">Crédito</option></select></label></div><div className="rounded-xl bg-background-darker p-4 text-sm"><div className="flex justify-between"><span>Serviços</span><span>{moeda(comanda.subtotal_servicos)}</span></div><div className="flex justify-between"><span>Produtos</span><span>{moeda(comanda.subtotal_produtos)}</span></div><div className="mt-2 flex justify-between border-t border-white/10 pt-2 text-lg font-bold"><span>Total</span><span className="text-gold">{moeda(comanda.total)}</span></div></div>{comanda.status === 'ABERTA' && <div className="flex gap-2"><button onClick={aplicarDesconto} disabled={salvando} className="flex-1 rounded-lg border border-white/15 py-3 text-sm">Aplicar desconto</button><button onClick={fechar} disabled={salvando} className="btn-gold flex-1 py-3 text-sm">Fechar comanda</button></div>}<p className="text-center text-xs text-text-muted">Situação: {comanda.status}</p></div>}</div></div>;
}
