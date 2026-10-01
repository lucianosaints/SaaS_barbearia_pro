import React, { useState } from 'react';
import api from '../services/api';

export default function FilaEsperaModal({ isOpen, onClose, data, hora, empresaId }) {
  const [nome, setNome] = useState('');
  const [telefone, setTelefone] = useState('');
  const [loading, setLoading] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!nome || !telefone) {
      setError('Por favor, preencha todos os campos.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await api.post('/api/fila-espera/', {
        empresa: empresaId,
        cliente_nome: nome,
        cliente_telefone: telefone,
        data_desejada: data,
        horario_desejado: hora
      });
      setSucesso(true);
    } catch (err) {
      console.error('Erro ao entrar na fila:', err);
      setError('Ocorreu um erro ao entrar na fila. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setSucesso(false);
    setNome('');
    setTelefone('');
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-background border border-gold/20 rounded-2xl w-full max-w-sm p-6 shadow-2xl animate-in zoom-in-95 duration-200">
        {!sucesso ? (
          <>
            <div className="text-center mb-6">
              <h3 className="text-xl font-bold text-gold">Sniper de Vagas 🎯</h3>
              <p className="text-xs text-text-muted mt-2">
                O horário de {hora} no dia {data.split('-').reverse().join('/')} está ocupado.
                Se a vaga liberar, avisaremos você!
              </p>
            </div>
            {error && (
              <div className="mb-4 text-xs text-rose-400 bg-rose-500/10 p-2 rounded border border-rose-500/20 text-center">
                {error}
              </div>
            )}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-text-secondary uppercase mb-1">Seu Nome</label>
                <input 
                  type="text" 
                  value={nome}
                  onChange={e => setNome(e.target.value)}
                  className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-3 text-sm text-text-primary focus:border-gold outline-none"
                  placeholder="Como devemos chamá-lo?"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-text-secondary uppercase mb-1">Seu WhatsApp</label>
                <input 
                  type="text" 
                  value={telefone}
                  onChange={e => setTelefone(e.target.value)}
                  className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-3 text-sm text-text-primary focus:border-gold outline-none"
                  placeholder="(11) 99999-9999"
                  required
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button 
                  type="button" 
                  onClick={handleClose}
                  className="flex-1 py-3 rounded-lg border border-white/10 text-text-secondary font-semibold hover:text-white hover:border-white/30 transition-colors text-sm"
                >
                  Cancelar
                </button>
                <button 
                  type="submit" 
                  disabled={loading}
                  className="flex-1 py-3 rounded-lg bg-gold text-background-darker font-bold text-sm hover:shadow-lg hover:shadow-gold/20 disabled:opacity-50 transition-all"
                >
                  {loading ? 'Aguarde...' : 'Me Avise!'}
                </button>
              </div>
            </form>
          </>
        ) : (
          <div className="text-center py-6">
            <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-green-500/20">
              <span className="text-3xl">✅</span>
            </div>
            <h3 className="text-xl font-bold text-green-400 mb-2">Pronto!</h3>
            <p className="text-sm text-text-secondary mb-6">
              Você está na fila para o dia {data.split('-').reverse().join('/')} às {hora}. Se alguém desistir, te mandaremos uma mensagem no WhatsApp!
            </p>
            <button 
              onClick={handleClose}
              className="w-full py-3 rounded-lg bg-background-paper border border-white/10 text-text-primary font-semibold hover:bg-white/5 transition-colors text-sm"
            >
              Fechar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
