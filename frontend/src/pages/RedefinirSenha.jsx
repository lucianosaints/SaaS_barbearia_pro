import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../services/api';
import PasswordRequirements, { isPasswordReady } from '../components/PasswordRequirements';
import { formatApiError } from '../utils/apiError';

export default function RedefinirSenha() {
  const [params] = useSearchParams();
  const [senha, setSenha] = useState('');
  const [confirmacao, setConfirmacao] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const uid = params.get('uid') || '';
  const token = params.get('token') || '';
  const linkCompleto = Boolean(uid && token);

  const submit = async (event) => {
    event.preventDefault();
    if (!isPasswordReady(senha) || senha !== confirmacao) return;
    setLoading(true);
    setError(null);
    try {
      await api.post('/api/senha/redefinir/', {
        uid,
        token,
        nova_senha: senha,
        confirmar_senha: confirmacao,
      });
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setSuccess(true);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-[70vh] w-full max-w-md items-center px-4 py-10">
      <div className="card-premium w-full space-y-5">
        <div>
          <h1 className="text-2xl font-bold text-gold-light">Redefinir senha</h1>
          <p className="mt-1 text-sm text-text-muted">Crie uma nova senha para acessar sua conta.</p>
        </div>

        {!linkCompleto ? (
          <div className="space-y-4">
            <p className="rounded-lg border border-rose-500/20 bg-rose-500/10 p-3 text-sm text-rose-300">Link incompleto. Solicite uma nova recuperação na tela de login.</p>
            <Link to="/" className="btn-gold block w-full py-3 text-center text-sm">Voltar ao início</Link>
          </div>
        ) : success ? (
          <div className="space-y-4">
            <p className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-sm text-emerald-300">Senha redefinida com sucesso. Agora você pode entrar com a nova senha.</p>
            <Link to="/" className="btn-gold block w-full py-3 text-center text-sm">Ir para o login</Link>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-4">
            {error && <p className="rounded-lg border border-rose-500/20 bg-rose-500/10 p-3 text-sm text-rose-300">⚠️ {error}</p>}
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase text-text-secondary">Nova senha</label>
              <input type="password" required value={senha} onChange={(e) => setSenha(e.target.value)} className="w-full rounded-lg border border-white/10 bg-background-darker px-4 py-2 text-sm text-text-primary focus:border-gold focus:outline-none" />
              <PasswordRequirements password={senha} confirmation={confirmacao} />
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase text-text-secondary">Confirmar nova senha</label>
              <input type="password" required value={confirmacao} onChange={(e) => setConfirmacao(e.target.value)} className="w-full rounded-lg border border-white/10 bg-background-darker px-4 py-2 text-sm text-text-primary focus:border-gold focus:outline-none" />
            </div>
            <button type="submit" disabled={loading || !isPasswordReady(senha) || senha !== confirmacao} className="btn-accent w-full py-3 text-sm disabled:opacity-50">
              {loading ? 'Salvando...' : 'Definir nova senha'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
