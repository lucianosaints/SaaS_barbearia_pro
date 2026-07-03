import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function GestaoServicos() {
  const [servicos, setServicos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Form State
  const [formData, setFormData] = useState({
    id: null,
    nome: '',
    preco: '',
    duracao_minutos: '30',
    ativo: true,
  });

  const fetchServicos = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/servicos/');
      setServicos(response.data.results || response.data);
    } catch (err) {
      console.error(err);
      setError('Erro ao carregar serviços.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServicos();
  }, []);

  const openModal = (servico = null) => {
    if (servico) {
      setFormData({
        id: servico.id,
        nome: servico.nome,
        preco: servico.preco,
        duracao_minutos: servico.duracao_minutos,
        ativo: servico.ativo,
      });
    } else {
      setFormData({
        id: null,
        nome: '',
        preco: '',
        duracao_minutos: '30',
        ativo: true,
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      const payload = {
        nome: formData.nome,
        preco: parseFloat(formData.preco),
        duracao_minutos: parseInt(formData.duracao_minutos),
        ativo: formData.ativo,
      };

      if (formData.id) {
        await api.put(`/api/servicos/${formData.id}/`, payload);
      } else {
        await api.post('/api/servicos/', payload);
      }
      
      await fetchServicos();
      setSuccess('Serviço salvo com sucesso!');
      setTimeout(() => setSuccess(null), 3000);
      closeModal();
    } catch (err) {
      console.error(err);
      setError('Erro ao salvar serviço. Verifique seus dados ou permissões.');
      setTimeout(() => setError(null), 5000);
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
  };

  if (loading && servicos.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-16">
        <div className="w-8 h-8 border-4 border-gold border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-4 text-xs text-text-secondary">Carregando serviços...</p>
      </div>
    );
  }

  return (
    <div className="w-full space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-text-primary">Gestão de Serviços</h2>
          <p className="text-text-muted text-xs mt-1">Configure os serviços prestados pela sua barbearia.</p>
        </div>
        <button 
          onClick={() => openModal()}
          className="btn-gold text-xs px-4 py-2"
        >
          + Novo Serviço
        </button>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm flex items-center gap-2">
          <span>⚠️</span> {error}
        </div>
      )}

      {success && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-xl text-sm flex items-center gap-2">
          <span>✅</span> {success}
        </div>
      )}

      {/* Lista de Serviços */}
      <div className="bg-background-paper border border-white/5 rounded-2xl overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-white/5 bg-background-darker/50 text-[10px] uppercase text-text-secondary tracking-wider font-semibold">
              <th className="py-3 px-4">Nome</th>
              <th className="py-3 px-4">Duração</th>
              <th className="py-3 px-4">Preço</th>
              <th className="py-3 px-4 text-center">Status</th>
              <th className="py-3 px-4 text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-sm">
            {servicos.map((servico) => (
              <tr key={servico.id} className="hover:bg-white/[0.02] transition-colors">
                <td className="py-3 px-4 font-medium text-text-primary">{servico.nome}</td>
                <td className="py-3 px-4 text-text-secondary">{servico.duracao_minutos} min</td>
                <td className="py-3 px-4 text-gold-light font-bold">{formatCurrency(servico.preco)}</td>
                <td className="py-3 px-4 text-center">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    servico.ativo ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                  }`}>
                    {servico.ativo ? 'Ativo' : 'Inativo'}
                  </span>
                </td>
                <td className="py-3 px-4 text-right">
                  <button 
                    onClick={() => openModal(servico)}
                    className="text-xs text-text-muted hover:text-gold transition-colors underline"
                  >
                    Editar
                  </button>
                </td>
              </tr>
            ))}
            {servicos.length === 0 && (
              <tr>
                <td colSpan="5" className="py-8 text-center text-text-muted">Nenhum serviço cadastrado ainda.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal de Formulário */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-background-paper border border-white/10 rounded-2xl w-full max-w-md p-6 shadow-2xl animate-in fade-in zoom-in-95">
            <h3 className="text-lg font-bold text-text-primary mb-4">
              {formData.id ? 'Editar Serviço' : 'Novo Serviço'}
            </h3>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-text-secondary uppercase mb-1">Nome do Serviço</label>
                <input
                  type="text"
                  name="nome"
                  required
                  value={formData.nome}
                  onChange={handleInputChange}
                  placeholder="Ex: Barba Completa"
                  className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:border-gold"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-text-secondary uppercase mb-1">Preço (R$)</label>
                  <input
                    type="number"
                    name="preco"
                    required
                    step="0.01"
                    min="0"
                    value={formData.preco}
                    onChange={handleInputChange}
                    placeholder="Ex: 35.00"
                    className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:border-gold"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-text-secondary uppercase mb-1">Duração (min)</label>
                  <input
                    type="number"
                    name="duracao_minutos"
                    required
                    step="5"
                    min="5"
                    value={formData.duracao_minutos}
                    onChange={handleInputChange}
                    placeholder="Ex: 30"
                    className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:border-gold"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 mt-4">
                <input
                  type="checkbox"
                  name="ativo"
                  id="ativo"
                  checked={formData.ativo}
                  onChange={handleInputChange}
                  className="w-4 h-4 rounded bg-background-darker border-white/10 text-gold focus:ring-gold"
                />
                <label htmlFor="ativo" className="text-sm text-text-primary">Serviço ativo e visível para agendamento</label>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="flex-1 py-2 text-sm font-semibold rounded-lg bg-background-darker text-text-primary hover:bg-white/5 transition-colors"
                  disabled={isSubmitting}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 text-sm font-semibold rounded-lg bg-gold text-background-darker hover:bg-gold-light transition-colors"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Salvando...' : 'Salvar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
