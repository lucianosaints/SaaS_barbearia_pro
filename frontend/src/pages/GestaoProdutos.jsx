import React, { useCallback, useEffect, useState } from 'react';
import api from '../services/api';
import GestaoPedidos from './GestaoPedidos';

const vazio = { id: null, nome: '', descricao: '', preco: '', preco_promocional: '', estoque: 0, controlar_estoque: true, disponivel: true, destaque: false, foto: null };
const moeda = (valor) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(valor || 0));

export default function GestaoProdutos() {
  const [produtos, setProdutos] = useState([]);
  const [form, setForm] = useState(vazio);
  const [aberto, setAberto] = useState(false);
  const [loading, setLoading] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [mensagem, setMensagem] = useState('');
  const [pagina, setPagina] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(1);

  const carregar = useCallback(async () => {
    try {
      setLoading(true);
      const { data } = await api.get('/api/produtos/', { params: { page: pagina, page_size: 9 } });
      setProdutos(data.results || data);
      setTotalPaginas(data.count ? Math.max(1, Math.ceil(data.count / 9)) : 1);
    } catch {
      setMensagem('Não foi possível carregar os produtos.');
    } finally {
      setLoading(false);
    }
  }, [pagina]);

  useEffect(() => { carregar(); }, [carregar]);

  const editar = (produto = null) => {
    setForm(produto ? { ...produto, foto: null, preco_promocional: produto.preco_promocional || '' } : { ...vazio });
    setMensagem('');
    setAberto(true);
  };

  const alterar = (event) => {
    const { name, type, checked, value, files } = event.target;
    setForm((atual) => ({ ...atual, [name]: type === 'checkbox' ? checked : type === 'file' ? files[0] : value }));
  };

  const salvar = async (event) => {
    event.preventDefault();
    setSalvando(true);
    setMensagem('');
    const dados = new FormData();
    ['nome', 'descricao', 'preco', 'estoque'].forEach((campo) => dados.append(campo, form[campo]));
    dados.append('preco_promocional', form.preco_promocional || '');
    ['controlar_estoque', 'disponivel', 'destaque'].forEach((campo) => dados.append(campo, String(form[campo])));
    if (form.foto) dados.append('foto', form.foto);
    try {
      const config = { headers: { 'Content-Type': 'multipart/form-data' } };
      if (form.id) await api.patch(`/api/produtos/${form.id}/`, dados, config);
      else await api.post('/api/produtos/', dados, config);
      setAberto(false);
      setMensagem('Produto salvo com sucesso.');
      await carregar();
    } catch (erro) {
      const dadosErro = erro.response?.data;
      setMensagem(dadosErro && typeof dadosErro === 'object' ? Object.values(dadosErro).flat().join(' ') : 'Não foi possível salvar o produto.');
    } finally {
      setSalvando(false);
    }
  };

  return <div className="space-y-10">
    <GestaoPedidos />
    <div className="border-t border-white/10 pt-8 space-y-6">
    <div className="flex flex-col sm:flex-row justify-between gap-4">
      <div><h2 className="text-xl font-bold">Vitrine do Salão</h2><p className="text-xs text-text-muted mt-1">Cadastre os produtos exibidos no catálogo público.</p></div>
      <button className="btn-gold text-xs px-4 py-2" onClick={() => editar()}>+ Novo Produto</button>
    </div>
    {mensagem && <div className="rounded-xl border border-gold/20 bg-gold/10 p-3 text-sm text-gold-light">{mensagem}</div>}
    {loading ? <p className="py-12 text-center text-text-muted">Carregando produtos...</p> :
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {produtos.map((produto) => <article key={produto.id} className="overflow-hidden rounded-2xl border border-white/10 bg-background-paper">
          <div className="h-40 bg-background-darker flex items-center justify-center overflow-hidden">
            {produto.foto ? <img src={produto.foto} alt={produto.nome} className="h-full w-full object-cover" /> : <span className="text-5xl">🛍️</span>}
          </div>
          <div className="p-4 space-y-2">
            <div className="flex justify-between gap-2"><h3 className="font-bold">{produto.nome}</h3><span className={produto.disponivel && produto.em_estoque ? 'text-emerald-400 text-xs' : 'text-rose-400 text-xs'}>{produto.disponivel && produto.em_estoque ? 'Disponível' : 'Indisponível'}</span></div>
            <p className="text-xs text-text-muted line-clamp-2">{produto.descricao || 'Sem descrição.'}</p>
            <div className="flex items-end justify-between"><div>{produto.preco_promocional && <span className="mr-2 text-xs line-through text-text-muted">{moeda(produto.preco)}</span>}<strong className="text-gold">{moeda(produto.preco_atual)}</strong></div><span className="text-xs text-text-muted">Estoque: {produto.controlar_estoque ? produto.estoque : 'livre'}</span></div>
            <button onClick={() => editar(produto)} className="w-full rounded-lg border border-white/10 py-2 text-xs hover:border-gold/50">Editar</button>
          </div>
        </article>)}
        {!produtos.length && <p className="col-span-full py-12 text-center text-text-muted">Nenhum produto cadastrado.</p>}
      </div>}
      {totalPaginas > 1 && <div className="flex items-center justify-center gap-3 text-xs"><button disabled={pagina === 1} onClick={() => setPagina((valor) => valor - 1)} className="rounded-lg border border-white/10 px-3 py-2 disabled:opacity-30">Anterior</button><span>{pagina} de {totalPaginas}</span><button disabled={pagina === totalPaginas} onClick={() => setPagina((valor) => valor + 1)} className="rounded-lg border border-white/10 px-3 py-2 disabled:opacity-30">Próxima</button></div>}

    {aberto && <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
      <form onSubmit={salvar} className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-2xl border border-white/10 bg-background-paper p-6 space-y-4">
        <div className="flex justify-between"><h3 className="text-lg font-bold">{form.id ? 'Editar produto' : 'Novo produto'}</h3><button type="button" onClick={() => setAberto(false)}>✕</button></div>
        <label className="block text-xs">Nome<input name="nome" required maxLength="150" value={form.nome} onChange={alterar} className="mt-1 w-full rounded-lg border border-white/10 bg-background-darker p-3" /></label>
        <label className="block text-xs">Descrição<textarea name="descricao" rows="3" value={form.descricao} onChange={alterar} className="mt-1 w-full rounded-lg border border-white/10 bg-background-darker p-3" /></label>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <label className="text-xs">Preço<input name="preco" required type="number" min="0" step="0.01" value={form.preco} onChange={alterar} className="mt-1 w-full rounded-lg border border-white/10 bg-background-darker p-3" /></label>
          <label className="text-xs">Promoção<input name="preco_promocional" type="number" min="0" step="0.01" value={form.preco_promocional} onChange={alterar} className="mt-1 w-full rounded-lg border border-white/10 bg-background-darker p-3" /></label>
          <label className="text-xs">Estoque<input name="estoque" required type="number" min="0" value={form.estoque} onChange={alterar} className="mt-1 w-full rounded-lg border border-white/10 bg-background-darker p-3" /></label>
        </div>
        <label className="block text-xs">Foto<input name="foto" type="file" accept="image/png,image/jpeg,image/webp" onChange={alterar} className="mt-1 block w-full text-xs" /></label>
        <div className="grid gap-2 sm:grid-cols-3 text-sm">{[['controlar_estoque','Controlar estoque'],['disponivel','Disponível'],['destaque','Destacar']].map(([nome, texto]) => <label key={nome} className="flex gap-2"><input name={nome} type="checkbox" checked={form[nome]} onChange={alterar} />{texto}</label>)}</div>
        <div className="flex gap-3 pt-2"><button type="button" onClick={() => setAberto(false)} className="flex-1 rounded-lg border border-white/10 py-3">Cancelar</button><button disabled={salvando} className="btn-gold flex-1 py-3">{salvando ? 'Salvando...' : 'Salvar'}</button></div>
      </form>
    </div>}
    </div>
  </div>;
}
