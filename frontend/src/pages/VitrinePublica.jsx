import React, { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import api from '../services/api';

const moeda = (valor) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(valor));

export default function VitrinePublica() {
  const { empresaSlug } = useParams();
  const chaveCarrinho = `vitrine_carrinho_${empresaSlug}`;
  const [produtos, setProdutos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [carrinhoAberto, setCarrinhoAberto] = useState(false);
  const [aviso, setAviso] = useState('');
  const [carrinho, setCarrinho] = useState(() => {
    try { return JSON.parse(localStorage.getItem(chaveCarrinho)) || []; }
    catch { return []; }
  });

  useEffect(() => {
    api.get('/api/produtos/', { params: { empresa_slug: empresaSlug } })
      .then(({ data }) => setProdutos(data.results || data))
      .catch(() => setErro('Não foi possível abrir esta vitrine.'))
      .finally(() => setLoading(false));
  }, [empresaSlug]);

  useEffect(() => { localStorage.setItem(chaveCarrinho, JSON.stringify(carrinho)); }, [carrinho, chaveCarrinho]);

  const totalItens = useMemo(() => carrinho.reduce((total, item) => total + item.quantidade, 0), [carrinho]);
  const subtotal = useMemo(() => carrinho.reduce((total, item) => total + Number(item.preco_atual) * item.quantidade, 0), [carrinho]);

  const adicionar = (produto) => {
    setCarrinho((atual) => {
      const existente = atual.find((item) => item.id === produto.id);
      if (existente) return atual.map((item) => item.id === produto.id ? { ...item, quantidade: Math.min(item.quantidade + 1, produto.controlar_estoque ? produto.estoque : 99) } : item);
      return [...atual, { id: produto.id, nome: produto.nome, preco_atual: produto.preco_atual, foto: produto.foto, quantidade: 1, estoque: produto.estoque, controlar_estoque: produto.controlar_estoque }];
    });
    setAviso(`${produto.nome} adicionado ao carrinho.`);
    window.setTimeout(() => setAviso(''), 2200);
  };

  const alterarQuantidade = (id, delta) => setCarrinho((atual) => atual.flatMap((item) => {
    if (item.id !== id) return [item];
    const quantidade = Math.min(item.quantidade + delta, item.controlar_estoque ? item.estoque : 99);
    return quantidade > 0 ? [{ ...item, quantidade }] : [];
  }));
  const remover = (id) => setCarrinho((atual) => atual.filter((item) => item.id !== id));

  return <section className="mx-auto w-full max-w-6xl px-4 py-8 sm:py-12">
    <div className="mb-8 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
      <div><span className="text-xs uppercase tracking-[0.25em] text-gold">Vitrine do Salão</span><h1 className="mt-2 text-3xl font-bold">Produtos para cuidar do seu estilo</h1><p className="mt-2 text-sm text-text-muted">Escolha online e retire diretamente no salão.</p></div>
      <div className="flex flex-wrap gap-2"><Link to={`/agendar/${empresaSlug}`} className="btn-gold-outline px-4 py-2 text-center text-sm">Agendar horário</Link><button onClick={() => setCarrinhoAberto(true)} className="btn-gold px-4 py-2 text-sm">🛒 Carrinho{totalItens > 0 && <span className="ml-2 rounded-full bg-black/25 px-2 py-0.5 text-xs">{totalItens}</span>}</button></div>
    </div>
    {aviso && <div className="fixed left-1/2 top-5 z-[130] -translate-x-1/2 rounded-xl border border-emerald-400/30 bg-emerald-950 px-5 py-3 text-sm text-emerald-300 shadow-2xl">✓ {aviso}</div>}
    {loading && <p className="py-20 text-center text-text-muted">Carregando vitrine...</p>}
    {erro && <p className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-4 text-rose-400">{erro}</p>}
    {!loading && !erro && <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {produtos.map((produto) => <article key={produto.id} className="overflow-hidden rounded-2xl border border-white/10 bg-background-paper shadow-xl transition hover:-translate-y-1 hover:border-gold/30">
        <div className="h-56 bg-background-darker flex items-center justify-center overflow-hidden">{produto.foto ? <img src={produto.foto} alt={produto.nome} className="h-full w-full object-cover" /> : <span className="text-6xl">🛍️</span>}</div>
        <div className="p-5"><div className="flex items-start justify-between gap-3"><h2 className="text-lg font-bold">{produto.nome}</h2>{produto.destaque && <span className="rounded-full bg-gold/15 px-2 py-1 text-[10px] font-bold text-gold">DESTAQUE</span>}</div><p className="mt-2 min-h-10 text-sm text-text-muted">{produto.descricao}</p><div className="mt-5 flex items-end gap-2">{produto.preco_promocional && <span className="text-sm line-through text-text-muted">{moeda(produto.preco)}</span>}<strong className="text-xl text-gold">{moeda(produto.preco_atual)}</strong></div><p className="mt-3 text-xs text-emerald-400">Disponível para retirada no salão</p><button onClick={() => adicionar(produto)} disabled={!produto.em_estoque} className="btn-gold mt-4 w-full py-3 text-sm disabled:cursor-not-allowed disabled:opacity-40">{produto.em_estoque ? '🛒 Adicionar ao carrinho' : 'Produto esgotado'}</button></div>
      </article>)}
      {!produtos.length && <p className="col-span-full py-20 text-center text-text-muted">Este salão ainda não publicou produtos.</p>}
    </div>}
    {carrinhoAberto && <div className="fixed inset-0 z-[120] flex justify-end bg-black/70 backdrop-blur-sm" onClick={() => setCarrinhoAberto(false)}>
      <aside className="flex h-full w-full max-w-md flex-col border-l border-white/10 bg-background-paper shadow-2xl" onClick={(event) => event.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-white/10 p-5"><div><h2 className="text-xl font-bold">Seu carrinho</h2><p className="text-xs text-text-muted">{totalItens} {totalItens === 1 ? 'item selecionado' : 'itens selecionados'}</p></div><button onClick={() => setCarrinhoAberto(false)} className="rounded-lg p-2 text-xl hover:bg-white/5" aria-label="Fechar carrinho">✕</button></div>
        <div className="flex-1 space-y-3 overflow-y-auto p-5">
          {carrinho.map((item) => <div key={item.id} className="flex gap-3 rounded-xl border border-white/10 p-3"><div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-background-darker">{item.foto ? <img src={item.foto} alt="" className="h-full w-full object-cover" /> : '🛍️'}</div><div className="min-w-0 flex-1"><h3 className="truncate text-sm font-bold">{item.nome}</h3><p className="text-sm text-gold">{moeda(Number(item.preco_atual) * item.quantidade)}</p><div className="mt-2 flex items-center gap-2"><button onClick={() => alterarQuantidade(item.id, -1)} className="h-7 w-7 rounded border border-white/15">−</button><span className="w-5 text-center text-sm">{item.quantidade}</span><button onClick={() => alterarQuantidade(item.id, 1)} disabled={item.controlar_estoque && item.quantidade >= item.estoque} className="h-7 w-7 rounded border border-white/15 disabled:opacity-30">+</button><button onClick={() => remover(item.id)} className="ml-auto text-xs text-rose-400">Remover</button></div></div></div>)}
          {!carrinho.length && <div className="py-20 text-center"><div className="text-5xl">🛒</div><p className="mt-4 text-text-muted">Seu carrinho está vazio.</p><button onClick={() => setCarrinhoAberto(false)} className="mt-4 text-sm text-gold underline">Continuar escolhendo</button></div>}
        </div>
        {carrinho.length > 0 && <div className="border-t border-white/10 p-5"><div className="mb-4 flex justify-between"><span className="text-text-muted">Subtotal</span><strong className="text-xl text-gold">{moeda(subtotal)}</strong></div><p className="mb-3 text-xs text-text-muted">Os itens ficam salvos neste navegador. A confirmação do pedido para retirada será adicionada na próxima etapa.</p><button className="w-full cursor-not-allowed rounded-lg border border-white/10 py-3 text-sm text-text-muted" disabled>Finalizar pedido — em breve</button></div>}
      </aside>
    </div>}
  </section>;
}
