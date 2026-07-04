import React, { useState, useEffect } from 'react';
import api from '../services/api';
import FilterBar from '../components/FilterBar';
import AgendamentoTable from '../components/AgendamentoTable';

// Importando as novas abas
import GestaoServicos from './GestaoServicos';
import GestaoEquipe from './GestaoEquipe';
import FinanceiroDashboard from './FinanceiroDashboard';
import LockoutScreen from '../components/LockoutScreen';
import useAgendamentoStore from '../store/useAgendamentoStore';

/**
 * Página AdminDashboard.
 * Funciona como um container de abas para a gestão completa da barbearia.
 */
export default function AdminDashboard() {
  const { userEmpresa, userTipo } = useAgendamentoStore();
  const [activeTab, setActiveTab] = useState('agenda'); // 'agenda', 'servicos', 'equipe', 'financeiro'
  
  // ==========================================
  // ESTADOS E FUNÇÕES DA ABA AGENDA (Padrão)
  // ==========================================
  const [agendamentos, setAgendamentos] = useState([]);
  const [loadingAgenda, setLoadingAgenda] = useState(true);
  const [errorAgenda, setErrorAgenda] = useState(null);
  const [currentFilters, setCurrentFilters] = useState({
    data: '',
    barbeiro: '',
    status: '',
  });

  const fetchAgendamentos = async (filters) => {
    setLoadingAgenda(true);
    setErrorAgenda(null);
    try {
      const params = {};
      if (filters.data) params.data_hora_inicio = filters.data;
      if (filters.barbeiro) params.barbeiro = filters.barbeiro;
      if (filters.status) params.status = filters.status;

      const response = await api.get('/api/agendamentos/', { params });
      setAgendamentos(response.data.results || response.data);
    } catch (err) {
      console.error('Erro ao buscar agendamentos:', err);
      setErrorAgenda('Não foi possível carregar a lista de agendamentos. Verifique sua conexão ou autenticação.');
    } finally {
      setLoadingAgenda(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'agenda') {
      fetchAgendamentos(currentFilters);
    }
  }, [activeTab]); // Recarrega se voltar pra agenda (opcional)

  const handleFilterChange = (newFilters) => {
    setCurrentFilters(newFilters);
    fetchAgendamentos(newFilters);
  };

  // ==========================================
  // RENDERIZAÇÃO
  // ==========================================
  
  if (userEmpresa && userEmpresa.em_trial === false && userEmpresa.assinatura_ativa === false) {
    if (userTipo !== 'CLIENTE' && userTipo !== 'SUPERADMIN') {
        return (
          <div className="w-full max-w-7xl mx-auto px-4 py-8">
             <LockoutScreen />
          </div>
        );
    }
  }

  return (
    <div className="w-full max-w-7xl mx-auto px-4 py-8">
      {/* Cabeçalho Principal do Admin */}
      <div className="mb-6 border-b border-white/10 pb-4 flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-gold-light via-gold to-gold-dark bg-clip-text text-transparent">
            Painel de Gestão
          </h1>
          <p className="text-text-muted text-sm mt-1">Controle completo do seu negócio.</p>
        </div>
        
        {userEmpresa && userEmpresa.slug && (
          <div className="bg-background-darker border border-white/10 p-3 rounded-lg text-left sm:text-right w-full sm:w-auto">
            <p className="text-xs text-text-secondary mb-1">Seu Link de Agendamento:</p>
            <a 
              href={`/agendar/${userEmpresa.slug}`} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-gold font-bold hover:underline break-all text-sm sm:text-base"
            >
              {window.location.origin}/agendar/{userEmpresa.slug}
            </a>
          </div>
        )}
      </div>

      {/* Menu de Navegação (Tabs) */}
      <div className="flex gap-4 overflow-x-auto mb-8 pb-2">
        <button
          onClick={() => setActiveTab('agenda')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all whitespace-nowrap ${
            activeTab === 'agenda' 
            ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' 
            : 'bg-background-paper border border-white/5 text-text-secondary hover:text-white hover:border-white/20'
          }`}
        >
          📅 Agenda e Operação
        </button>

        {userTipo === 'ADMINISTRADOR' && (
          <>
            <button
              onClick={() => setActiveTab('servicos')}
              className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all whitespace-nowrap ${
                activeTab === 'servicos' 
                ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' 
                : 'bg-background-paper border border-white/5 text-text-secondary hover:text-white hover:border-white/20'
              }`}
            >
              ✂️ Serviços
            </button>
            <button
              onClick={() => setActiveTab('equipe')}
              className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all whitespace-nowrap ${
                activeTab === 'equipe' 
                ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' 
                : 'bg-background-paper border border-white/5 text-text-secondary hover:text-white hover:border-white/20'
              }`}
            >
              👥 Equipe (Barbeiros)
            </button>
            <button
              onClick={() => setActiveTab('financeiro')}
              className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all whitespace-nowrap ${
                activeTab === 'financeiro' 
                ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' 
                : 'bg-background-paper border border-white/5 text-text-secondary hover:text-white hover:border-white/20'
              }`}
            >
              💰 Financeiro
            </button>
          </>
        )}
      </div>

      {/* Conteúdo da Aba Ativa */}
      <div className="animate-in fade-in duration-300">
        
        {/* ABA: AGENDA */}
        {activeTab === 'agenda' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-text-primary">Visão Operacional</h2>
              <button 
                onClick={() => fetchAgendamentos(currentFilters)}
                className="btn-gold-outline text-xs px-4 py-2"
              >
                🔄 Atualizar Tabela
              </button>
            </div>

            <FilterBar onFilterChange={handleFilterChange} />

            {loadingAgenda ? (
              <div className="bg-background-paper border border-white/5 rounded-xl p-12 text-center">
                <div className="inline-block w-8 h-8 border-4 border-gold border-t-transparent rounded-full animate-spin mb-4"></div>
                <p className="text-text-secondary text-sm">Carregando agendamentos...</p>
              </div>
            ) : errorAgenda ? (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl p-6 text-center text-sm">
                ❌ {errorAgenda}
              </div>
            ) : (
              <AgendamentoTable agendamentos={agendamentos} />
            )}
          </div>
        )}

        {/* ABA: SERVIÇOS */}
        {activeTab === 'servicos' && <GestaoServicos />}

        {/* ABA: EQUIPE */}
        {activeTab === 'equipe' && <GestaoEquipe />}

        {/* ABA: FINANCEIRO */}
        {activeTab === 'financeiro' && <FinanceiroDashboard />}

      </div>
    </div>
  );
}
