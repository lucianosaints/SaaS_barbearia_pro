import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function GestaoEquipe() {
  const [profissionais, setProfissionais] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Form State
  const [formData, setFormData] = useState({
    id: null,
    first_name: '',
    last_name: '',
    email: '',
    telefone: '',
    password: '',
    is_active: true,
    avaliacao: 5.0,
    taxa_comissao: 40.0,
    comissao_percentual: 50.0,
    foto: null,
  });

  const fetchProfissionais = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/usuarios/');
      // Filtramos caso venha algo diferente, mas a API já deve retornar os profissionais da empresa
      const list = response.data.results || response.data;
      // Garante que mostremos apenas profissionais (e administradores), ocultando clientes finais
      setProfissionais(list.filter(u => u.tipo !== 'CLIENTE'));
    } catch (err) {
      console.error(err);
      setError('Erro ao carregar equipe.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfissionais();
  }, []);

  const openModal = (profissional = null) => {
    if (profissional) {
      setFormData({
        id: profissional.id,
        first_name: profissional.first_name || '',
        last_name: profissional.last_name || '',
        email: profissional.email || '',
        telefone: profissional.telefone || '',
        password: '', // Não carrega senha na edição
        is_active: profissional.is_active,
        avaliacao: profissional.avaliacao || 5.0,
        taxa_comissao: profissional.taxa_comissao || 40.0,
        comissao_percentual: profissional.comissao_percentual || 50.0,
        foto: profissional.foto || null, // Carregar a foto existente para preview
      });
    } else {
      setFormData({
        id: null,
        first_name: '',
        last_name: '',
        email: '',
        telefone: '',
        password: '',
        is_active: true,
        avaliacao: 5.0,
        taxa_comissao: 40.0,
        comissao_percentual: 50.0,
        foto: null,
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked, files } = e.target;
    if (type === 'file') {
      setFormData(prev => ({ ...prev, [name]: files[0] }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: type === 'checkbox' ? checked : value
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      const payload = new FormData();
      payload.append('first_name', formData.first_name);
      payload.append('last_name', formData.last_name);
      payload.append('email', formData.email);
      payload.append('username', formData.email);
      payload.append('telefone', formData.telefone);
      payload.append('is_active', formData.is_active);
      payload.append('avaliacao', formData.avaliacao);
      payload.append('taxa_comissao', formData.taxa_comissao);
      payload.append('comissao_percentual', formData.comissao_percentual);

      if (formData.password) {
        payload.append('password', formData.password);
      }
      
      // Só envia a foto se ela for de fato um novo arquivo (File) selecionado no input
      if (formData.foto && formData.foto instanceof File) {
        payload.append('foto', formData.foto);
      }

      const config = {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      };

      if (formData.id) {
        await api.patch(`/api/usuarios/${formData.id}/`, payload, config);
      } else {
        await api.post('/api/usuarios/', payload, config);
      }
      
      await fetchProfissionais();
      setSuccess('Profissional salvo com sucesso!');
      setTimeout(() => setSuccess(null), 3000);
      closeModal();
    } catch (err) {
      console.error(err);
      const erroMsg = err.response?.data ? JSON.stringify(err.response.data) : 'Erro ao salvar profissional. Verifique os dados.';
      setError(`Erro: ${erroMsg}`);
      setTimeout(() => setError(null), 5000);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading && profissionais.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-16">
        <div className="w-8 h-8 border-4 border-gold border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-4 text-xs text-text-secondary">Carregando equipe...</p>
      </div>
    );
  }

  return (
    <div className="w-full space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-text-primary">Gestão de Equipe</h2>
          <p className="text-text-muted text-xs mt-1">Gerencie os profissionais que atendem na sua barbearia.</p>
        </div>
        <button 
          onClick={() => openModal()}
          className="btn-gold text-xs px-4 py-2 w-full sm:w-auto"
        >
          + Adicionar Profissional
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

      {/* Lista de Profissionais */}
      <div className="bg-background-paper border border-white/5 rounded-2xl overflow-x-auto">
        <table className="w-full text-left border-collapse min-w-[600px]">
          <thead>
            <tr className="border-b border-white/5 bg-background-darker/50 text-[10px] uppercase text-text-secondary tracking-wider font-semibold whitespace-nowrap">
              <th className="py-3 px-4">Nome</th>
              <th className="py-3 px-4">E-mail (Login)</th>
              <th className="py-3 px-4">Telefone</th>
              <th className="py-3 px-4 text-center">Status</th>
              <th className="py-3 px-4 text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-sm">
            {profissionais.map((prof) => (
              <tr key={prof.id} className="hover:bg-white/[0.02] transition-colors">
                <td className="py-3 px-4 font-medium text-text-primary">
                  {prof.first_name} {prof.last_name}
                </td>
                <td className="py-3 px-4 text-text-secondary">{prof.email}</td>
                <td className="py-3 px-4 text-text-secondary">{prof.telefone || '—'}</td>
                <td className="py-3 px-4 text-center">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    prof.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                  }`}>
                    {prof.is_active ? 'Ativo' : 'Inativo'}
                  </span>
                </td>
                <td className="py-3 px-4 text-right">
                  <button 
                    onClick={() => openModal(prof)}
                    className="text-xs text-text-muted hover:text-gold transition-colors underline"
                  >
                    Editar
                  </button>
                </td>
              </tr>
            ))}
            {profissionais.length === 0 && (
              <tr>
                <td colSpan="5" className="py-8 text-center text-text-muted">Nenhum profissional cadastrado na equipe.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal de Formulário (Cartão Focado) */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-background-paper border border-gold/30 rounded-2xl w-full max-w-md p-6 shadow-2xl animate-in fade-in zoom-in-95 max-h-[90vh] overflow-y-auto">
            {/* O cabeçalho agora está integrado ao design do cartão centralizado abaixo */}
            <form onSubmit={handleSubmit} className="space-y-6">
              
              {/* SECTION: PERFIL (Centralizado) */}
              <div className="flex flex-col items-center text-center space-y-4 pb-6 border-b border-white/10">
                {/* Avatar Interativo */}
                <div className="relative w-28 h-28 rounded-full overflow-hidden border-[3px] border-gold shadow-[0_0_20px_rgba(212,175,55,0.2)] bg-background-darker flex items-center justify-center group">
                  {formData.foto ? (
                    typeof formData.foto === 'string' ? (
                      <img src={formData.foto.startsWith('http') ? formData.foto : `${import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '' : 'http://localhost:8000')}${formData.foto}`} alt="Perfil" className="w-full h-full object-cover" />
                    ) : (
                      <img src={URL.createObjectURL(formData.foto)} alt="Perfil" className="w-full h-full object-cover" />
                    )
                  ) : (
                    <span className="text-4xl font-bold text-gold-light">
                      {(formData.first_name?.[0] || '?').toUpperCase()}
                    </span>
                  )}
                  <label className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity">
                    <span className="text-[11px] text-white font-bold uppercase tracking-wider">Mudar Foto</span>
                    <input type="file" name="foto" accept="image/*" onChange={handleInputChange} className="hidden" />
                  </label>
                </div>
                
                {/* Textos Principais */}
                <div>
                  <h3 className="text-2xl font-bold text-white tracking-tight">
                    {formData.first_name || 'Nome'} {formData.last_name || 'do Profissional'}
                  </h3>
                  <p className="text-gold text-sm font-semibold mt-1 uppercase tracking-wider">Especialista Premium</p>
                  <p className="text-text-muted text-xs mt-1">Serviços oferecidos: Corte, Barba e Tratamentos</p>
                </div>

                {/* Dropdown / Checkbox de Visibilidade */}
                <div className="mt-2 w-full max-w-[280px]">
                  <div className="flex items-center justify-between gap-3 bg-background border border-gold/20 px-4 py-3 rounded-xl shadow-inner transition-colors hover:border-gold/40">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        name="is_active"
                        id="is_active"
                        checked={formData.is_active}
                        onChange={handleInputChange}
                        className="w-4 h-4 rounded bg-background border-gold/50 text-gold focus:ring-gold focus:ring-offset-background"
                      />
                      <label htmlFor="is_active" className="text-xs font-bold text-text-primary cursor-pointer">
                        Exibir meu perfil na agenda
                      </label>
                    </div>
                    <span className="text-gold text-[10px] border border-gold/30 rounded-full w-4 h-4 flex items-center justify-center cursor-help" title="Se desmarcado, os clientes não poderão ver nem agendar com você.">
                      ?
                    </span>
                  </div>
                </div>
              </div>

              {/* SECTION: DADOS TÉCNICOS */}
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] font-bold text-text-secondary uppercase mb-1">Nome</label>
                    <input
                      type="text"
                      name="first_name"
                      required
                      value={formData.first_name}
                      onChange={handleInputChange}
                      placeholder="Ex: Carlos"
                      className="w-full bg-background border border-white/10 rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-gold"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-text-secondary uppercase mb-1">Sobrenome</label>
                    <input
                      type="text"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleInputChange}
                      placeholder="Ex: Silva"
                      className="w-full bg-background border border-white/10 rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-gold"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-text-secondary uppercase mb-1">E-mail (Login)</label>
                  <input
                    type="email"
                    name="email"
                    required
                    value={formData.email}
                    onChange={handleInputChange}
                    placeholder="Ex: carlos@barbearia.com"
                    className="w-full bg-background border border-white/10 rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-gold"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] font-bold text-text-secondary uppercase mb-1">Telefone</label>
                    <input
                      type="tel"
                      name="telefone"
                      value={formData.telefone}
                      onChange={handleInputChange}
                      placeholder="(11) 99999-9999"
                      className="w-full bg-background border border-white/10 rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-gold"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-text-secondary uppercase mb-1">Avaliação (Estrelas)</label>
                    <input
                      type="number"
                      name="avaliacao"
                      min="1.0"
                      max="5.0"
                      step="0.1"
                      value={formData.avaliacao}
                      onChange={handleInputChange}
                      className="w-full bg-background border border-white/10 rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-gold"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-text-secondary uppercase mb-1">
                    {formData.id ? 'Nova Senha (deixe em branco para não mudar)' : 'Senha Inicial'}
                  </label>
                  <input
                    type="password"
                    name="password"
                    required={!formData.id}
                    value={formData.password}
                    onChange={handleInputChange}
                    placeholder="******"
                    className="w-full bg-background border border-white/10 rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-gold"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] font-bold text-text-secondary uppercase mb-1">Comissão Antiga (%)</label>
                    <input
                      type="number"
                      name="taxa_comissao"
                      min="0"
                      max="100"
                      step="0.5"
                      value={formData.taxa_comissao}
                      onChange={handleInputChange}
                      placeholder="Ex: 40.0"
                      className="w-full bg-background border border-white/10 rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-gold"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-text-secondary uppercase mb-1">Comissão Nova (%)</label>
                    <input
                      type="number"
                      name="comissao_percentual"
                      min="0"
                      max="100"
                      step="0.5"
                      value={formData.comissao_percentual}
                      onChange={handleInputChange}
                      placeholder="Ex: 50.0"
                      className="w-full bg-background border border-white/10 rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-gold"
                    />
                  </div>
                </div>
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
