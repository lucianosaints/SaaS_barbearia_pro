import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import useAgendamentoStore from '../store/useAgendamentoStore';

export default function OnboardingModal({ isOpen, onClose }) {
  const { login } = useAgendamentoStore();
  const [formData, setFormData] = useState({
    nome_barbearia: '',
    nome_admin: '',
    email: '',
    senha: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/saas/registrar/', formData);
      const token = response.data.access;
      const user = response.data.user;
      
      // Salva os tokens no local storage
      localStorage.setItem('access_token', token);
      localStorage.setItem('refresh_token', response.data.refresh);
      
      // Se sucesso, faz login automaticamente passando todos os argumentos
      login(token, user.id, user.nome || user.email, user.tipo, { id: user.empresa_id });
      onClose(); // Fecha o modal e deixa o App.jsx redirecionar
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || 'Erro ao criar conta. Verifique os dados e tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="bg-bg-secondary w-full max-w-lg rounded-2xl shadow-premium border border-border-color overflow-hidden flex flex-col"
          >
            <div className="p-6 border-b border-border-color flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-white">Criar conta da Barbearia</h2>
                <p className="text-sm text-text-muted mt-1">Crie sua barbearia e teste grátis por 7 dias</p>
              </div>
              <button onClick={onClose} className="text-text-muted hover:text-white transition-colors" disabled={loading}>
                ✕
              </button>
            </div>
            
            <div className="p-6">
              {error && (
                <div className="mb-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 p-3 rounded-xl text-sm flex items-center gap-2">
                  <span>⚠️</span> {error}
                </div>
              )}
              <form className="space-y-4" onSubmit={handleSubmit}>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Nome da Barbearia</label>
                  <input 
                    type="text" 
                    name="nome_barbearia"
                    value={formData.nome_barbearia}
                    onChange={handleChange}
                    required
                    className="input-premium w-full" 
                    placeholder="Ex: Golden Barber" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Seu Nome</label>
                  <input 
                    type="text" 
                    name="nome_admin"
                    value={formData.nome_admin}
                    onChange={handleChange}
                    required
                    className="input-premium w-full" 
                    placeholder="Ex: João Silva" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">E-mail Administrativo</label>
                  <input 
                    type="email" 
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="input-premium w-full" 
                    placeholder="seu@email.com" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Senha</label>
                  <input 
                    type="password" 
                    name="senha"
                    value={formData.senha}
                    onChange={handleChange}
                    required
                    className="input-premium w-full" 
                    placeholder="••••••••" 
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-6 bg-primary hover:bg-primary-hover text-bg-primary font-bold py-3 px-4 rounded-xl transition-all shadow-[0_0_15px_rgba(212,175,55,0.4)] disabled:opacity-50"
                >
                  {loading ? 'Criando Conta...' : 'Criar Conta e Iniciar Teste Grátis'}
                </button>
              </form>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
