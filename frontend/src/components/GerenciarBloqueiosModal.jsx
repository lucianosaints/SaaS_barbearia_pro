import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function GerenciarBloqueiosModal({ isOpen, onClose, onBlocksChanged }) {
  const [bloqueios, setBloqueios] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetchBloqueios();
    }
  }, [isOpen]);

  const fetchBloqueios = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/api/bloqueios/');
      // Filtra para mostrar todos os bloqueios a partir do dia atual (00:00)
      const startOfDay = new Date();
      startOfDay.setHours(0, 0, 0, 0);
      const filtered = res.data.filter(b => new Date(b.data_hora_fim) >= startOfDay);
      // Ordena por data mais próxima
      filtered.sort((a, b) => new Date(a.data_hora_inicio) - new Date(b.data_hora_inicio));
      setBloqueios(filtered);
    } catch (err) {
      console.error('Erro ao buscar bloqueios:', err);
      setError('Não foi possível carregar a lista de bloqueios.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Tem certeza que deseja apagar este bloqueio? Os horários voltarão a ficar disponíveis.")) return;
    
    try {
      await api.delete(`/api/bloqueios/${id}/`);
      fetchBloqueios();
      if (onBlocksChanged) onBlocksChanged();
    } catch (err) {
      console.error('Erro ao excluir bloqueio:', err);
      alert('Erro ao excluir o bloqueio.');
    }
  };

  const formatDateTime = (isoString) => {
    const d = new Date(isoString);
    return `${d.toLocaleDateString('pt-BR')} às ${d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#1a1a1a] border border-gold/20 rounded-2xl w-full max-w-2xl p-6 shadow-2xl animate-in zoom-in-95 duration-200 max-h-[85vh] flex flex-col">
        <div className="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
          <div>
            <h3 className="text-xl font-bold text-gold">Gerenciar Bloqueios</h3>
            <p className="text-sm text-gray-400 mt-1">Veja e remova os bloqueios ativos na agenda.</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl font-bold">
            &times;
          </button>
        </div>
        
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-xs p-3 rounded-lg mb-4 text-center">
            ❌ {error}
          </div>
        )}

        <div className="flex-1 overflow-y-auto pr-2 space-y-3">
          {loading ? (
            <div className="text-center py-8 text-gold text-sm font-semibold">
              <div className="inline-block w-6 h-6 border-2 border-gold border-t-transparent rounded-full animate-spin mb-2"></div>
              <p>Carregando...</p>
            </div>
          ) : bloqueios.length === 0 ? (
            <div className="text-center py-10 bg-black/30 rounded-xl border border-white/5">
              <span className="text-4xl mb-3 block opacity-50">📅</span>
              <p className="text-gray-400 text-sm">Nenhum bloqueio futuro encontrado.</p>
            </div>
          ) : (
            bloqueios.map(b => (
              <div key={b.id} className="bg-black/50 border border-white/10 rounded-xl p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 hover:border-white/20 transition-colors">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="bg-red-500/20 text-red-400 text-[10px] font-bold px-2 py-0.5 rounded uppercase">
                      Bloqueado
                    </span>
                    <span className="text-sm font-semibold text-white">
                      {formatDateTime(b.data_hora_inicio)} até {formatDateTime(b.data_hora_fim)}
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 flex flex-col gap-1">
                    <span><strong className="text-gray-300">Profissional:</strong> {b.profissional_nome || 'Todos (Barbearia Inteira)'}</span>
                    {b.motivo && <span><strong className="text-gray-300">Motivo:</strong> {b.motivo}</span>}
                  </div>
                </div>
                
                <button 
                  onClick={() => handleDelete(b.id)}
                  className="bg-red-500/10 text-red-400 hover:bg-red-500 hover:text-white border border-red-500/20 px-3 py-1.5 rounded-lg text-xs font-bold transition-all w-full sm:w-auto"
                >
                  Excluir
                </button>
              </div>
            ))
          )}
        </div>

        <div className="pt-4 mt-4 border-t border-white/10">
          <button 
            onClick={onClose}
            className="w-full py-2.5 rounded-lg bg-transparent border border-white/20 text-gray-300 font-semibold text-sm hover:bg-white/5 transition-colors"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
