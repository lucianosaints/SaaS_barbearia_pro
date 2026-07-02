import React, { useState, useEffect } from 'react';
import api from '../services/api';
import useAgendamentoStore from '../store/useAgendamentoStore';
import carlosImg from '../imagem/carlos_silva.jpg';

/**
 * Passo do Wizard para seleção do Barbeiro / Profissional.
 */
export default function StepBarbeiros() {
  const [barbeiros, setBarbeiros] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Zustand
  const { barbeiroId, setBarbeiroId } = useAgendamentoStore();

  useEffect(() => {
    async function loadBarbeiros() {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get('/api/usuarios/');
        setBarbeiros(response.data.results || response.data);
      } catch (err) {
        console.error('Erro ao buscar barbeiros:', err);
        setError('Falha ao obter lista de profissionais.');
      } finally {
        setLoading(false);
      }
    }
    loadBarbeiros();
  }, []);

  if (loading) {
    return (
      <div className="py-8 text-center text-sm text-text-muted">
        Carregando profissionais...
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
        <h2 className="text-lg font-bold text-gold-light">Escolha o Profissional</h2>
        <p className="text-text-muted text-xs">Selecione quem irá cuidar do seu visual</p>
      </div>

      <div className="grid grid-cols-2 gap-3 max-h-[350px] overflow-y-auto pr-1">
        {barbeiros.map((barbeiro) => {
          const isSelected = barbeiroId === barbeiro.id;
          const nomeCompleto = barbeiro.first_name 
            ? `${barbeiro.first_name} ${barbeiro.last_name || ''}` 
            : barbeiro.username;

          const isCarlos = nomeCompleto.toLowerCase().includes('carlos');

          return (
            <div
              key={barbeiro.id}
              onClick={() => setBarbeiroId(barbeiro.id)}
              className={`p-4 rounded-xl border cursor-pointer text-center transition-all duration-200 flex flex-col items-center gap-2 ${
                isSelected
                  ? 'bg-gold/10 border-gold shadow-md shadow-gold/5'
                  : 'bg-background-darker border-white/5 hover:border-white/20'
              }`}
            >
              {/* Foto real ou Inicial do Profissional */}
              <div className={`w-16 h-16 rounded-full overflow-hidden border flex items-center justify-center transition-colors ${
                isSelected ? 'border-gold' : 'border-white/10 text-gold-light bg-background'
              }`}>
                {isCarlos ? (
                  <img src={carlosImg} alt={nomeCompleto} className="w-full h-full object-cover" />
                ) : (
                  <span className="text-xl font-bold">{nomeCompleto.charAt(0).toUpperCase()}</span>
                )}
              </div>

              <div className="mt-1">
                <h3 className="font-semibold text-xs text-text-primary line-clamp-1">{nomeCompleto}</h3>
                <span className="text-[10px] text-text-muted">Disponível</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
