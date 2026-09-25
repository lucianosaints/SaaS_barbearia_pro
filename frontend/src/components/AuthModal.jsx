import React, { useState } from 'react';
import { FaWhatsapp } from 'react-icons/fa';
import useAgendamentoStore from '../store/useAgendamentoStore';
import api from '../services/api';
import PasswordRequirements, { isPasswordReady } from './PasswordRequirements';
import TermsModal from './TermsModal';

/**
 * Componente AuthModal.
 * Interface flutuante para Login e Cadastro Rápido do cliente final.
 */
export default function AuthModal({ onAuthSuccess }) {
  const { authModalOpen, setAuthModalOpen, login, empresaId } = useAgendamentoStore();
  const [activeTab, setActiveTab] = useState('login'); // 'login' ou 'cadastro'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Estados dos inputs
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [nome, setNome] = useState('');
  const [telefone, setTelefone] = useState('');
  const [confirmarSenha, setConfirmarSenha] = useState('');
  const [aceitouTermos, setAceitouTermos] = useState(false);
  const [termsOpen, setTermsOpen] = useState(false);

  if (!authModalOpen) return null;

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/api/token/', {
        username: email,
        password: senha,
      });
      const token = response.data.access;
      const refresh = response.data.refresh;
      const user = response.data.user;

      localStorage.setItem('access_token', token);
      localStorage.setItem('refresh_token', refresh);

      login(token, user.id, user.nome || email, user.tipo, user.empresa);
      if (onAuthSuccess) onAuthSuccess();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'E-mail ou senha incorretos.');
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      setLoading(false);
    }
  };

  const handleCadastro = async (e) => {
    e.preventDefault();
    if (!isPasswordReady(senha) || senha !== confirmarSenha || !aceitouTermos) {
      setError('Complete os requisitos da senha, confirme-a e aceite os Termos de Uso.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/api/clientes/registrar/', {
        nome,
        email,
        senha,
        telefone,
        empresa_id: empresaId || null,
        aceitou_termos: aceitouTermos,
      });

      const token = response.data.access;
      const refresh = response.data.refresh;

      localStorage.setItem('access_token', token);
      localStorage.setItem('refresh_token', refresh);
      login(token, response.data.user.id, response.data.user.nome, response.data.user.tipo, response.data.user.empresa);

      if (onAuthSuccess) onAuthSuccess();
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.error || 
        err.response?.data?.email?.[0] || 
        err.response?.data?.senha?.[0] ||
        'Erro ao realizar o cadastro. Verifique os dados inseridos.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-background-darker/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-background-paper border border-white/5 rounded-2xl w-full max-w-md overflow-hidden relative shadow-2xl shadow-gold/5">
        
        {/* Botão de Fechar */}
        <button
          onClick={() => setAuthModalOpen(false)}
          className="absolute top-4 right-4 text-text-muted hover:text-text-primary transition-colors text-lg"
        >
          ✕
        </button>

        {/* Abas */}
        <div className="flex border-b border-white/5">
          <button
            onClick={() => { setActiveTab('login'); setError(null); }}
            className={`flex-1 py-4 text-sm font-semibold transition-all ${
              activeTab === 'login'
                ? 'border-b-2 border-gold text-gold bg-white/[0.01]'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            Acessar Conta
          </button>
          <button
            onClick={() => { setActiveTab('cadastro'); setError(null); }}
            className={`flex-1 py-4 text-sm font-semibold transition-all ${
              activeTab === 'cadastro'
                ? 'border-b-2 border-gold text-gold bg-white/[0.01]'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            Cadastro Rápido
          </button>
        </div>

        <div className="p-6">
          {error && (
            <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs p-3 rounded-lg mb-4 text-center">
              ⚠️ {error}
            </div>
          )}

          {activeTab === 'login' ? (
            /* Formulário de Login */
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-text-secondary uppercase mb-2">E-mail ou Usuário</label>
                <input
                  type="text"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="exemplo@gmail.com ou usuario"
                  className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:border-gold transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-secondary uppercase mb-2">Senha</label>
                <input
                  type="password"
                  required
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:border-gold transition-colors"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-gold w-full py-3 mt-2 text-sm"
              >
                {loading ? 'Carregando...' : 'Entrar e Continuar'}
              </button>
            </form>
          ) : (
            /* Formulário de Cadastro Rápido */
            <form onSubmit={handleCadastro} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-text-secondary uppercase mb-2">Nome Completo</label>
                <input
                  type="text"
                  required
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  placeholder="Seu nome completo"
                  className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:border-gold transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-secondary uppercase mb-2">Telefone</label>
                <div className="relative">
                  <FaWhatsapp className="absolute left-3 top-1/2 -translate-y-1/2 text-emerald-500 text-lg" />
                  <input
                    type="tel"
                    required
                    value={telefone}
                    onChange={(e) => setTelefone(e.target.value)}
                    placeholder="(11) 99999-9999"
                    className="w-full bg-background-darker border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-text-primary focus:outline-none focus:border-gold transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-secondary uppercase mb-2">E-mail</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="exemplo@gmail.com"
                  className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:border-gold transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-secondary uppercase mb-2">Senha</label>
                <input
                  type="password"
                  required
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                  minLength={8}
                  placeholder="Mínimo 8 caracteres"
                  className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:border-gold transition-colors"
                />
                <PasswordRequirements password={senha} confirmation={confirmarSenha} />
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-secondary uppercase mb-2">Confirmar senha</label>
                <input type="password" required value={confirmarSenha} onChange={(e) => setConfirmarSenha(e.target.value)} placeholder="Digite a senha novamente" className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:border-gold transition-colors" />
              </div>

              <label className="flex items-start gap-3 text-xs text-text-secondary">
                <input type="checkbox" checked={aceitouTermos} onChange={(e) => setAceitouTermos(e.target.checked)} required className="mt-0.5 h-4 w-4 accent-amber-400" />
                <span>Li e concordo com os <button type="button" onClick={() => setTermsOpen(true)} className="font-semibold text-gold underline">Termos de Uso e o Aviso de Privacidade</button>.</span>
              </label>

              <button
                type="submit"
                disabled={loading || !isPasswordReady(senha) || senha !== confirmarSenha || !aceitouTermos}
                className="btn-accent w-full py-3 mt-2 text-sm"
              >
                {loading ? 'Carregando...' : 'Cadastrar e Continuar'}
              </button>
            </form>
          )}
        </div>
      </div>
      <TermsModal isOpen={termsOpen} onClose={() => setTermsOpen(false)} />
    </div>
  );
}
