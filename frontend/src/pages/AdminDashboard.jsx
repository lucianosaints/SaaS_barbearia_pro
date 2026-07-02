import React, { useState, useEffect } from 'react';
import api from '../services/api';
import FilterBar from '../components/FilterBar';
import AgendamentoTable from '../components/AgendamentoTable';

/**
 * Página AdminDashboard.
 * Visualização e controle operacional de todos os agendamentos da barbearia.
 */
export default function AdminDashboard() {
  const [agendamentos, setAgendamentos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentFilters, setCurrentFilters] = useState({
    data: '',
    barbeiro: '',
    status: '',
  });

  // Função para buscar agendamentos na API aplicando filtros
  const fetchAgendamentos = async (filters) => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (filters.data) {
        // Envia a data para filtrar o início do agendamento (adequando à API)
        params.data_hora_inicio = filters.data;
      }
      if (filters.barbeiro) {
        params.barbeiro = filters.barbeiro;
      }
      if (filters.status) {
        params.status = filters.status;
      }

      const response = await api.get('/api/agendamentos/', { params });
      // DRF costuma paginar os dados retornando { results: [...] } ou direto a lista
      setAgendamentos(response.data.results || response.data);
    } catch (err) {
      console.error('Erro ao buscar agendamentos:', err);
      setError('Não foi possível carregar a lista de agendamentos. Verifique sua conexão ou autenticação.');
    } finally {
      setLoading(false);
    }
  };

  // Carrega inicialmente
  useEffect(() => {
    fetchAgendamentos(currentFilters);
  }, []);

  const handleFilterChange = (newFilters) => {
    setCurrentFilters(newFilters);
    fetchAgendamentos(newFilters);
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 py-8">
      {/* Cabeçalho do Painel */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-gold-light via-gold to-gold-dark bg-clip-text text-transparent">
            Painel de Gestão
          </h1>
          <p className="text-text-muted text-sm">Controle completo de horários e atendimento operacional</p>
        </div>
        <button 
          onClick={() => fetchAgendamentos(currentFilters)}
          className="btn-gold-outline text-xs px-4 py-2"
        >
          🔄 Atualizar Tabela
        </button>
      </div>

      {/* Barra de Filtros */}
      <FilterBar onFilterChange={handleFilterChange} />

      {/* Tabela ou Estados de carregamento/erro */}
      {loading ? (
        <div className="bg-background-paper border border-white/5 rounded-xl p-12 text-center">
          <div className="inline-block w-8 h-8 border-4 border-gold border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-text-secondary text-sm">Carregando agendamentos...</p>
        </div>
      ) : error ? (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl p-6 text-center text-sm">
          ❌ {error}
        </div>
      ) : (
        <AgendamentoTable agendamentos={agendamentos} />
      )}
    </div>
  );
}
