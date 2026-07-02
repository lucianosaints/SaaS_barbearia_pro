import React, { useState, useEffect } from 'react';
import useAgendamentoStore from '../store/useAgendamentoStore';
import api from '../services/api';

/**
 * Passo do Wizard para seleção de Data e Hora.
 * Consome o endpoint dinâmico de disponibilidade do backend.
 */
export default function StepDataHora() {
  // Zustand State
  const { dataHora, setDataHora, barbeiroId, servicosIds } = useAgendamentoStore();
  
  // Estados locais auxiliares para separar data e hora
  const [selectedDate, setSelectedDate] = useState(dataHora ? dataHora.split('T')[0] : '');
  const [selectedTime, setSelectedTime] = useState(dataHora && dataHora.includes('T') ? dataHora.split('T')[1].substring(0, 5) : '');
  
  // Estados para dados da API
  const [horariosDisponiveis, setHorariosDisponiveis] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Busca os horários livres sempre que a data selecionada mudar
  useEffect(() => {
    async function loadDisponibilidade() {
      if (!selectedDate || !barbeiroId || servicosIds.length === 0) {
        setHorariosDisponiveis([]);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const servicosParam = servicosIds.join(',');
        const response = await api.get('/api/disponibilidade/', {
          params: {
            data: selectedDate,
            barbeiro_id: barbeiroId,
            servicos: servicosParam,
          },
        });
        setHorariosDisponiveis(response.data.horarios_disponiveis || []);
      } catch (err) {
        console.error('Erro ao carregar disponibilidade:', err);
        setError('Ocorreu um erro ao carregar os horários disponíveis.');
        setHorariosDisponiveis([]);
      } finally {
        setLoading(false);
      }
    }

    loadDisponibilidade();
  }, [selectedDate, barbeiroId, servicosIds]);

  const handleDateChange = (e) => {
    const date = e.target.value;
    setSelectedDate(date);
    setSelectedTime(''); // Limpa a hora selecionada ao trocar de dia
    setDataHora(null);   // Reseta data/hora no estado global
  };

  const handleTimeSelect = (time) => {
    setSelectedTime(time);
    if (selectedDate && time) {
      // Salva no formato ISO com fuso local que o backend espera
      setDataHora(`${selectedDate}T${time}:00`);
    } else {
      setDataHora(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="text-center mb-6">
        <h2 className="text-lg font-bold text-gold-light">Escolha Data e Hora</h2>
        <p className="text-text-muted text-xs">Selecione o dia e o horário do seu atendimento</p>
      </div>

      <div className="space-y-4">
        {/* Seletor de Data */}
        <div>
          <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
            Escolher Dia
          </label>
          <input
            type="date"
            value={selectedDate}
            onChange={handleDateChange}
            min={new Date().toISOString().split('T')[0]} // Impede datas retroativas
            className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:border-gold transition-colors"
          />
        </div>

        {/* Grade de Horários ou Indicador de Status */}
        {selectedDate && (
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
              Horários Disponíveis
            </label>

            {loading ? (
              <div className="py-6 text-center text-xs text-gold">
                <div className="inline-block w-4 h-4 border-2 border-gold border-t-transparent rounded-full animate-spin mr-2 align-middle"></div>
                Carregando horários livres...
              </div>
            ) : error ? (
              <div className="py-4 text-center text-xs text-rose-400 bg-rose-500/5 rounded-lg border border-rose-500/10">
                ⚠️ {error}
              </div>
            ) : horariosDisponiveis.length > 0 ? (
              <div className="grid grid-cols-4 gap-2 max-h-[220px] overflow-y-auto pr-1">
                {horariosDisponiveis.map((time) => {
                  const isSelected = selectedTime === time;
                  return (
                    <button
                      key={time}
                      type="button"
                      onClick={() => handleTimeSelect(time)}
                      className={`py-2 text-xs font-semibold rounded-lg border transition-all duration-200 ${
                        isSelected
                          ? 'bg-gold border-gold text-background shadow-md shadow-gold/10'
                          : 'bg-background-darker border-white/5 text-text-primary hover:border-white/20'
                      }`}
                    >
                      {time}
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-text-secondary bg-background-darker/35 rounded-xl border border-white/5">
                Nenhum horário disponível para esta data. Por favor, selecione outro dia.
              </div>
            )}
          </div>
        )}

        {!selectedDate && (
          <div className="py-6 text-center text-xs text-text-muted bg-background-darker/50 rounded-xl border border-white/5">
            Selecione uma data acima para carregar os horários disponíveis.
          </div>
        )}
      </div>
    </div>
  );
}
