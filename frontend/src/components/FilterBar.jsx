import React, { useState, useEffect } from 'react';
import api from '../services/api';

/**
 * Componente FilterBar.
 * Barra de filtragem de agendamentos.
 * 
 * @param {object} props
 * @param {function} props.onFilterChange - Função callback invocada na alteração de filtros
 */
export default function FilterBar({ onFilterChange }) {
  const [barbeiros, setBarbeiros] = useState([]);
  const [filters, setFilters] = useState({
    data: '',
    barbeiro: '',
    status: '',
  });

  // Busca a lista de barbeiros (operadores/funcionários da empresa)
  useEffect(() => {
    async function loadBarbeiros() {
      try {
        const response = await api.get('/api/usuarios/');
        // Filtra simplificadamente por usuários ativos da empresa
        setBarbeiros(response.data.results || response.data);
      } catch (err) {
        console.error('Erro ao carregar profissionais para filtros:', err);
      }
    }
    loadBarbeiros();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    const updatedFilters = { ...filters, [name]: value };
    setFilters(updatedFilters);
    onFilterChange(updatedFilters);
  };

  return (
    <div className="bg-background-paper border border-white/5 p-4 rounded-xl flex flex-wrap gap-4 items-end mb-6">
      {/* Filtro de Data */}
      <div className="flex-1 min-w-[200px]">
        <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
          Filtrar por Data
        </label>
        <input
          type="date"
          name="data"
          value={filters.data}
          onChange={handleChange}
          className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:border-gold transition-colors"
        />
      </div>

      {/* Filtro de Profissional */}
      <div className="flex-1 min-w-[200px]">
        <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
          Profissional / Barbeiro
        </label>
        <select
          name="barbeiro"
          value={filters.barbeiro}
          onChange={handleChange}
          className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:border-gold transition-colors"
        >
          <option value="">Todos os profissionais</option>
          {barbeiros.map((barbeiro) => (
            <option key={barbeiro.id} value={barbeiro.id}>
              {barbeiro.first_name ? `${barbeiro.first_name} ${barbeiro.last_name || ''}` : barbeiro.username}
            </option>
          ))}
        </select>
      </div>

      {/* Filtro de Status */}
      <div className="flex-1 min-w-[200px]">
        <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
          Status do Agendamento
        </label>
        <select
          name="status"
          value={filters.status}
          onChange={handleChange}
          className="w-full bg-background-darker border border-white/10 rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:border-gold transition-colors"
        >
          <option value="">Todos os status</option>
          <option value="PENDENTE">Pendente</option>
          <option value="CONFIRMADO">Confirmado</option>
          <option value="CONCLUIDO">Concluído</option>
          <option value="CANCELADO">Cancelado</option>
        </select>
      </div>

      {/* Botão de Limpeza rápida */}
      <button
        onClick={() => {
          const cleared = { data: '', barbeiro: '', status: '' };
          setFilters(cleared);
          onFilterChange(cleared);
        }}
        className="btn-gold-outline text-xs py-2 px-4 whitespace-nowrap h-[38px] flex items-center justify-center"
      >
        Limpar Filtros
      </button>
    </div>
  );
}
