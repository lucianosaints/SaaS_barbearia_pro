import React, { useCallback, useEffect, useState } from 'react';
import api from '../services/api';

const moeda = (valor) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(valor || 0));
const rotulos = { AGUARDANDO_CONFIRMACAO: 'Aguardando confirmação', CONFIRMADO: 'Confirmado', AGUARDANDO_SINAL: 'Aguardando sinal', SINAL_CONFIRMADO: 'Sinal confirmado', PRONTO: 'Pronto para retirada', CONCLUIDO: 'Concluído', CANCELADO: 'Cancelado' };
const periodos = [['diario', 'Hoje'], ['mensal', 'Este mês'], ['anual', 'Este ano']];
const acoes = {
  AGUARDANDO_CONFIRMACAO: [['CONFIRMADO', 'Confirmar'], ['AGUARDANDO_SINAL', 'Solicitar sinal'], ['CANCELADO', 'Cancelar']],
  CONFIRMADO: [['AGUARDANDO_SINAL', 'Solicitar sinal'], ['PRONTO', 'Marcar pronto'], ['CANCELADO', 'Cancelar']],
  AGUARDANDO_SINAL: [['SINAL_CONFIRMADO', 'Confirmar sinal'], ['CANCELADO', 'Cancelar']],
  SINAL_CONFIRMADO: [['PRONTO', 'Marcar pronto'], ['CANCELADO', 'Cancelar']],
  PRONTO: [['CONCLUIDO', 'Concluir'], ['CANCELADO', 'Cancelar']],
};

function Paginacao({ pagina, totalPaginas, mudar }) {
  if (totalPaginas <= 1) return null;
  return <div className="flex items-center justify-center gap-3 pt-2 text-xs"><button disabled={pagina === 1} onClick={() => mudar(pagina - 1)} className="rounded-lg border border-white/10 px-3 py-2 disabled:opacity-30">Anterior</button><span>{pagina} de {totalPaginas}</span><button disabled={pagina === totalPaginas} onClick={() => mudar(pagina + 1)} className="rounded-lg border border-white/10 px-3 py-2 disabled:opacity-30">Próxima</button></div>;
}

export default function GestaoPedidos() {
  const [pedidos, setPedidos] = useState([]);
  const [periodo, setPeriodo] = useState('mensal');
  const [pagina, setPagina] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(1);
  const [dashboard, setDashboard] = useState(null);
  const [mensagem, setMensagem] = useState('');
  const [alterando, setAlterando] = useState(null);
  const [aberto, setAberto] = useState(null);

  const carregar = useCallback(async () => {
    try {
      const [lista, resumo] = await Promise.all([
        api.get('/api/pedidos/', { params: { periodo, page: pagina, page_size: 8 } }),
        api.get('/api/pedidos/dashboard/', { params: { periodo } }),
      ]);
      const dados = lista.data;
      setPedidos(dados.results || dados);
      setTotalPaginas(dados.count ? Math.max(1, Math.ceil(dados.count / 8)) : 1);
      setDashboard(resumo.data);
    } catch { setMensagem('Não foi possível carregar os pedidos e as vendas.'); }
  }, [pagina, periodo]);
  useEffect(() => { carregar(); }, [carregar]);

  const selecionarPeriodo = (valor) => { setPeriodo(valor); setPagina(1); setAberto(null); };
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
      setMensagem(`Novo link do pedido #${pedido.id} copiado.`);
    } catch { setMensagem('Não foi possível regenerar e copiar o link.'); }
    finally { setAlterando(null); }
  };

  return <section className="space-y-5">
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><h2 className="text-xl font-bold">Pedidos e vendas da Vitrine</h2><p className="mt-1 text-xs text-text-muted">Acompanhe reservas, retiradas e o resultado financeiro dos produtos.</p></div><div className="flex rounded-xl border border-white/10 bg-background-darker p-1">{periodos.map(([valor, texto]) => <button key={valor} onClick={() => selecionarPeriodo(valor)} className={`rounded-lg px-3 py-2 text-xs font-semibold ${periodo === valor ? 'bg-gold text-background-darker' : 'text-text-muted hover:text-white'}`}>{texto}</button>)}</div></div>
    {mensagem && <p className="rounded-xl border border-gold/20 bg-gold/10 p-3 text-sm text-gold-light">{mensagem}</p>}
    {dashboard && <div className="grid grid-cols-2 gap-3 lg:grid-cols-4"><div className="rounded-xl border border-white/10 bg-background-paper p-4"><p className="text-[11px] uppercase text-text-muted">Vendas concluídas</p><strong className="mt-1 block text-xl text-gold">{moeda(dashboard.total_vendas)}</strong></div><div className="rounded-xl border border-white/10 bg-background-paper p-4"><p className="text-[11px] uppercase text-text-muted">Pedidos concluídos</p><strong className="mt-1 block text-xl">{dashboard.pedidos_concluidos}</strong></div><div className="rounded-xl border border-white/10 bg-background-paper p-4"><p className="text-[11px] uppercase text-text-muted">Itens vendidos</p><strong className="mt-1 block text-xl">{dashboard.itens_vendidos}</strong></div><div className="rounded-xl border border-white/10 bg-background-paper p-4"><p className="text-[11px] uppercase text-text-muted">Ticket médio</p><strong className="mt-1 block text-xl">{moeda(dashboard.ticket_medio)}</strong></div></div>}
    <div className="space-y-2">{pedidos.map((pedido) => { const expandido = aberto === pedido.id; return <article key={pedido.id} className="rounded-xl border border-white/10 bg-background-paper px-4 py-3"><button onClick={() => setAberto(expandido ? null : pedido.id)} className="flex w-full items-center gap-3 text-left"><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><strong className="truncate text-sm">#{pedido.id} · {pedido.cliente_nome}</strong><span className="rounded-full bg-gold/10 px-2 py-1 text-[9px] font-bold text-gold">{rotulos[pedido.status]}</span></div><p className="mt-1 truncate text-[11px] text-text-muted">{pedido.cliente_telefone} · {pedido.forma_pagamento} · {new Date(pedido.criado_em).toLocaleString('pt-BR')}</p></div><strong className="text-sm text-gold">{moeda(pedido.total)}</strong><span className="text-text-muted">{expandido ? '▲' : '▼'}</span></button>{expandido && <div className="mt-3 border-t border-white/10 pt-3"><div className="space-y-1 text-xs">{pedido.itens.map((item) => <div key={`${item.produto}-${item.nome_produto}`} className="flex justify-between gap-3"><span className="min-w-0 truncate">{item.quantidade}x {item.nome_produto}</span><span>{moeda(item.subtotal)}</span></div>)}</div>{pedido.sinal_solicitado && <p className="mt-2 text-[11px] text-text-muted">Sinal: {moeda(pedido.valor_sinal)} · Saldo: {moeda(pedido.saldo_restante)}</p>}<div className="mt-3 flex flex-wrap gap-2">{(acoes[pedido.status] || []).map(([status, texto]) => <button key={status} disabled={alterando === pedido.id} onClick={() => mudarStatus(pedido, status)} className={status === 'CANCELADO' ? 'rounded-lg border border-rose-500/30 px-3 py-1.5 text-[11px] text-rose-300' : 'btn-gold-outline px-3 py-1.5 text-[11px]'}>{texto}</button>)}<button disabled={alterando === pedido.id} onClick={() => regenerarTicket(pedido)} className="rounded-lg border border-white/15 px-3 py-1.5 text-[11px] text-text-muted">Regenerar link</button></div></div>}</article>; })}{!pedidos.length && <p className="py-8 text-center text-sm text-text-muted">Nenhum pedido neste período.</p>}</div>
    <Paginacao pagina={pagina} totalPaginas={totalPaginas} mudar={setPagina} />
  </section>;
}
