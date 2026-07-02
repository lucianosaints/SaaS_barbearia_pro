import React, { useState, useEffect } from 'react';
import api from '../services/api';
import useAgendamentoStore from '../store/useAgendamentoStore';

/**
 * Passo do Wizard para seleção de Serviços.
 * Permite que o cliente selecione múltiplos serviços para agendamento.
 */
export default function StepServicos() {
  const [servicos, setServicos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Zustand
  const { servicosIds, toggleServicoId } = useAgendamentoStore();

  useEffect(() => {
    async function loadServicos() {
      setLoading(false);
      setError(null);
      try {
        const response = await api.get('/api/servicos/');
        setServicos(response.data.results || response.data);
      } catch (err) {
        console.error('Erro ao buscar serviços:', err);
        setError('Falha ao obter lista de serviços.');
      } finally {
        setLoading(false);
      }
    }
    loadServicos();
  }, []);

  if (loading) {
    return (
      <div className="py-8 text-center text-sm text-text-muted">
        Carregando serviços...
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-6 bg-red-500/10 text-red-400 text-sm border border-red-500/20 rounded-xl text-center">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="text-center mb-6">
        <h2 className="text-lg font-bold text-gold-light">Escolha os Serviços</h2>
        <p className="text-text-muted text-xs">Você pode selecionar múltiplos serviços para uma mesma sessão</p>
      </div>

      <div className="grid grid-cols-1 gap-3 max-h-[350px] overflow-y-auto pr-1">
        {servicos.map((servico) => {
          const isSelected = servicosIds.includes(servico.id);
          return (
            <div
              key={servico.id}
              onClick={() => toggleServicoId(servico.id)}
              className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 flex justify-between items-center ${
                isSelected
                  ? 'bg-gold/10 border-gold shadow-md shadow-gold/5'
                  : 'bg-background-darker border-white/5 hover:border-white/20'
              }`}
            >
              <div>
                <h3 className="font-semibold text-sm text-text-primary">{servico.nome}</h3>
                <span className="text-xs text-text-muted">⏱️ {servico.duracao_minutos} minutos</span>
              </div>
              <div className="text-right">
                <span className="font-bold text-sm text-accent-orange">
                  {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(servico.preco)}
                </span>
                <div className={`w-5 h-5 rounded-full border flex items-center justify-center mt-1.5 transition-colors ${
                  isSelected ? 'bg-gold border-gold' : 'border-white/20'
                }`}>
                  {isSelected && <span className="text-[10px] text-background font-bold">✓</span>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
