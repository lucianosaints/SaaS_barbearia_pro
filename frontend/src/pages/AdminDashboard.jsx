import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { FiMenu, FiX } from 'react-icons/fi';
import FilterBar from '../components/FilterBar';
import AgendaTable from '../components/AgendaTable';
import GestaoServicos from './GestaoServicos';
import GestaoEquipe from './GestaoEquipe';
import GestaoClientes from './GestaoClientes';
import FinanceiroDashboard from './FinanceiroDashboard';
import GestaoConfiguracoes from './GestaoConfiguracoes';
import BloqueioHorarioModal from '../components/BloqueioHorarioModal';
import ConfirmModal from '../components/ConfirmModal';
import LockoutScreen from '../components/LockoutScreen';
import useAgendamentoStore from '../store/useAgendamentoStore';
import PlacaQRCode from '../components/PlacaQRCode';

/**
 * Página AdminDashboard.
 * Funciona como um container de abas para a gestão completa da barbearia.
 */
export default function AdminDashboard() {
  const { userEmpresa, userTipo } = useAgendamentoStore();
  const [activeTab, setActiveTab] = useState('agenda'); // 'agenda', 'servicos', 'equipe', 'financeiro', 'configuracoes'
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [bloqueioModalOpen, setBloqueioModalOpen] = useState(false);
  const [cancelamentoModal, setCancelamentoModal] = useState({ isOpen: false, agendamento: null });
  
  // ==========================================
  // ESTADOS E FUNÇÕES DA ABA AGENDA (Padrão)
  // ==========================================
  const placaRef = useRef(null);
  const [gerandoPDF, setGerandoPDF] = useState(false);

  const gerarPDF = async () => {
    if (!placaRef.current || !userEmpresa) return;
    try {
      setGerandoPDF(true);
      const element = placaRef.current;
      const canvas = await html2canvas(element, { scale: 2 });
      const imgData = canvas.toDataURL('image/png');
      
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      pdf.save(`Placa-${userEmpresa.slug}.pdf`);
    } catch (error) {
      console.error('Erro ao gerar PDF:', error);
      alert('Não foi possível gerar o PDF. Tente novamente.');
    } finally {
      setGerandoPDF(false);
    }
  };

  const [agendamentos, setAgendamentos] = useState([]);
  const [loadingAgenda, setLoadingAgenda] = useState(true);
  const [errorAgenda, setErrorAgenda] = useState(null);
  const [currentFilters, setCurrentFilters] = useState({
    data: '',
    barbeiro: '',
    status: '',
  });
  const [editingAgendamento, setEditingAgendamento] = useState(null);
  const [savingStatus, setSavingStatus] = useState(false);

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

  const handleEditClick = (agendamento) => {
    setEditingAgendamento(agendamento);
  };

  const handleSaveStatus = async (e) => {
    e.preventDefault();
    setSavingStatus(true);
    try {
      await api.patch(`/api/agendamentos/${editingAgendamento.id}/`, {
        status: editingAgendamento.status,
        status_pagamento: editingAgendamento.status_pagamento
      });
      setEditingAgendamento(null);
      fetchAgendamentos(currentFilters);
    } catch (err) {
      console.error(err);
      alert("Erro ao salvar o status do agendamento.");
    } finally {
      setSavingStatus(false);
    }
  };

  const handleCancelAgendamento = (agendamento) => {
    setCancelamentoModal({ isOpen: true, agendamento });
  };

  const confirmCancelamento = async () => {
    const agendamento = cancelamentoModal.agendamento;
    if (!agendamento) return;
    
    try {
      await api.patch(`/api/agendamentos/${agendamento.id}/cancelar/`);
      setCancelamentoModal({ isOpen: false, agendamento: null });
      fetchAgendamentos(currentFilters);
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.error || "Erro ao cancelar o agendamento.");
    }
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
    <div className="flex flex-col sm:flex-row w-full flex-1 min-h-[calc(100vh-80px)]">
      
      {/* SIDEBAR DESKTOP */}
      <aside className={`hidden sm:flex flex-col bg-background-paper border-r border-white/5 transition-all duration-300 ease-in-out shrink-0 ${isSidebarCollapsed ? 'w-20' : 'w-64'}`}>
        <div className={`flex items-center p-4 border-b border-white/5 ${isSidebarCollapsed ? 'justify-center' : 'justify-between'}`}>
          {!isSidebarCollapsed && <span className="font-bold text-gold text-lg tracking-wide truncate">Menu Gestão</span>}
          <button 
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)} 
            className="text-text-secondary hover:text-gold transition-colors p-2 rounded-lg hover:bg-white/5"
            title="Recolher/Expandir Menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
          </button>
        </div>
        
        <nav className="flex-1 flex flex-col gap-2 p-3 mt-2 overflow-y-auto overflow-x-hidden">
          <button
            onClick={() => setActiveTab('agenda')}
            className={`flex items-center gap-3 px-3 py-3 text-sm font-semibold rounded-lg transition-all ${
              activeTab === 'agenda' 
              ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' 
              : 'text-text-secondary hover:text-white hover:bg-white/5'
            } ${isSidebarCollapsed ? 'justify-center' : 'justify-start'}`}
            title="Agenda e Operação"
          >
            <span className="text-xl">📅</span>
            {!isSidebarCollapsed && <span>Agenda e Operação</span>}
          </button>

          {userTipo === 'ADMINISTRADOR' && (
            <>
              <button
                onClick={() => setActiveTab('servicos')}
                className={`flex items-center gap-3 px-3 py-3 text-sm font-semibold rounded-lg transition-all ${
                  activeTab === 'servicos' 
                  ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' 
                  : 'text-text-secondary hover:text-white hover:bg-white/5'
                } ${isSidebarCollapsed ? 'justify-center' : 'justify-start'}`}
                title="Serviços"
              >
                <span className="text-xl">✂️</span>
                {!isSidebarCollapsed && <span>Serviços</span>}
              </button>
              
              <button
                onClick={() => setActiveTab('equipe')}
                className={`flex items-center gap-3 px-3 py-3 text-sm font-semibold rounded-lg transition-all ${
                  activeTab === 'equipe' 
                  ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' 
                  : 'text-text-secondary hover:text-white hover:bg-white/5'
                } ${isSidebarCollapsed ? 'justify-center' : 'justify-start'}`}
                title="Cadastro de Equipe"
              >
                <span className="text-xl">👥</span>
                {!isSidebarCollapsed && <span>Equipe</span>}
              </button>
              
              <button
                onClick={() => setActiveTab('clientes')}
                className={`flex items-center gap-3 px-3 py-3 text-sm font-semibold rounded-lg transition-all ${
                  activeTab === 'clientes' 
                  ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' 
                  : 'text-text-secondary hover:text-white hover:bg-white/5'
                } ${isSidebarCollapsed ? 'justify-center' : 'justify-start'}`}
                title="Gestão de Clientes"
              >
                <span className="text-xl">🤝</span>
                {!isSidebarCollapsed && <span>Clientes</span>}
              </button>
              
              <button
                onClick={() => setActiveTab('financeiro')}
                className={`flex items-center gap-3 px-3 py-3 text-sm font-semibold rounded-lg transition-all ${
                  activeTab === 'financeiro' 
                  ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' 
                  : 'text-text-secondary hover:text-white hover:bg-white/5'
                } ${isSidebarCollapsed ? 'justify-center' : 'justify-start'}`}
                title="Financeiro"
              >
                <span className="text-xl">💰</span>
                {!isSidebarCollapsed && <span>Financeiro</span>}
              </button>
              
              <button
                onClick={() => setActiveTab('configuracoes')}
                className={`flex items-center gap-3 px-3 py-3 text-sm font-semibold rounded-lg transition-all ${
                  activeTab === 'configuracoes' 
                  ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' 
                  : 'text-text-secondary hover:text-white hover:bg-white/5'
                } ${isSidebarCollapsed ? 'justify-center' : 'justify-start'}`}
                title="Configurações"
              >
                <span className="text-xl">⚙️</span>
                {!isSidebarCollapsed && <span>Configurações</span>}
              </button>
            </>
          )}
        </nav>
      </aside>

      {/* ÁREA DE CONTEÚDO PRINCIPAL */}
      <div className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 overflow-y-auto">
        {/* Cabeçalho Principal do Admin */}
        <div className="mb-6 border-b border-white/10 pb-4 flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 relative">
          <div className="flex items-center gap-3">
            <button onClick={() => setIsMobileMenuOpen(true)} className="sm:hidden text-gold hover:text-gold-light transition-colors" title="Abrir Menu">
              <FiMenu size={28} />
            </button>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-gold-light via-gold to-gold-dark bg-clip-text text-transparent">
                Painel de Gestão
              </h1>
              <p className="text-text-muted text-sm mt-1">Controle completo do seu negócio.</p>
            </div>
          </div>
          
          {userEmpresa && userEmpresa.slug && (
            <div className="bg-background-darker border border-gold/20 p-3 sm:p-4 rounded-xl text-center sm:text-right w-full sm:w-auto flex flex-col items-center sm:items-end">
              <div className="flex flex-col sm:flex-row items-center gap-1 sm:gap-2">
                <p className="text-xs text-text-secondary">Link de Agendamento:</p>
                <a 
                  href={`/agendar/${userEmpresa.slug}`} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-gold font-bold hover:underline truncate max-w-[280px] sm:max-w-none text-sm"
                >
                  {window.location.origin}/agendar/{userEmpresa.slug}
                </a>
              </div>
              
              <button 
                onClick={gerarPDF} 
                disabled={gerandoPDF}
                className="mt-3 w-full sm:w-auto bg-gold/10 text-gold border border-gold/30 hover:bg-gold/20 px-4 py-2 rounded-lg font-bold text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
              >
                🖨️ {gerandoPDF ? 'Gerando...' : 'Baixar Placa QR Code'}
              </button>
            </div>
          )}
        </div>

      {/* DRAWER MOBILE */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-[100] flex sm:hidden">
          {/* Overlay escuro */}
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm transition-opacity" onClick={() => setIsMobileMenuOpen(false)}></div>
          
          {/* Menu Lateral */}
          <div className="relative flex flex-col w-72 max-w-[80vw] h-full bg-background-paper border-r border-gold/20 shadow-2xl animate-in slide-in-from-left duration-300">
            <div className="flex items-center justify-between p-5 border-b border-white/10">
              <span className="font-bold text-gold text-xl tracking-wide">Menu Gestão</span>
              <button onClick={() => setIsMobileMenuOpen(false)} className="text-text-secondary hover:text-white p-2 rounded-lg hover:bg-white/5 transition-colors">
                <FiX size={24} />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto py-4 px-3 space-y-2">
              <button
                onClick={() => { setActiveTab('agenda'); setIsMobileMenuOpen(false); }}
                className={`w-full flex items-center gap-3 px-4 py-3.5 text-sm font-semibold rounded-lg transition-all ${
                  activeTab === 'agenda' ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' : 'text-text-secondary hover:text-white hover:bg-white/5'
                }`}
              >
                <span className="text-xl">📅</span> Agenda e Operação
              </button>
              
              {userTipo === 'ADMINISTRADOR' && (
                <>
                  <button
                    onClick={() => { setActiveTab('servicos'); setIsMobileMenuOpen(false); }}
                    className={`w-full flex items-center gap-3 px-4 py-3.5 text-sm font-semibold rounded-lg transition-all ${
                      activeTab === 'servicos' ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' : 'text-text-secondary hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <span className="text-xl">✂️</span> Serviços
                  </button>
                  <button
                    onClick={() => { setActiveTab('equipe'); setIsMobileMenuOpen(false); }}
                    className={`w-full flex items-center gap-3 px-4 py-3.5 text-sm font-semibold rounded-lg transition-all ${
                      activeTab === 'equipe' ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' : 'text-text-secondary hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <span className="text-xl">👥</span> Cadastro de Equipe
                  </button>
                  <button
                    onClick={() => { setActiveTab('clientes'); setIsMobileMenuOpen(false); }}
                    className={`w-full flex items-center gap-3 px-4 py-3.5 text-sm font-semibold rounded-lg transition-all ${
                      activeTab === 'clientes' ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' : 'text-text-secondary hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <span className="text-xl">🤝</span> Gestão de Clientes
                  </button>
                  <button
                    onClick={() => { setActiveTab('financeiro'); setIsMobileMenuOpen(false); }}
                    className={`w-full flex items-center gap-3 px-4 py-3.5 text-sm font-semibold rounded-lg transition-all ${
                      activeTab === 'financeiro' ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' : 'text-text-secondary hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <span className="text-xl">💰</span> Financeiro
                  </button>
                  <button
                    onClick={() => { setActiveTab('configuracoes'); setIsMobileMenuOpen(false); }}
                    className={`w-full flex items-center gap-3 px-4 py-3.5 text-sm font-semibold rounded-lg transition-all ${
                      activeTab === 'configuracoes' ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' : 'text-text-secondary hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <span className="text-xl">⚙️</span> Configurações
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Conteúdo da Aba Ativa */}
      <div className="animate-in fade-in duration-300">
        
        {/* ABA: AGENDA */}
        {activeTab === 'agenda' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center flex-wrap gap-4">
              <h2 className="text-xl font-bold text-text-primary">Visão Operacional</h2>
              <div className="flex gap-2">
                <button 
                  onClick={() => setBloqueioModalOpen(true)}
                  className="bg-red-500/20 text-red-500 border border-red-500/50 hover:bg-red-500/30 font-semibold text-xs px-4 py-2 rounded-lg transition-colors"
                >
                  🚫 Bloquear Horário
                </button>
                <button 
                  onClick={() => fetchAgendamentos(currentFilters)}
                  className="btn-gold-outline text-xs px-4 py-2"
                >
                  🔄 Atualizar Tabela
                </button>
              </div>
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
              <>
                <AgendaTable agendamentos={agendamentos} onEdit={handleEditClick} onCancel={handleCancelAgendamento} />

            {/* Modal de Edição Rápida */}
            {editingAgendamento && (
              <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                <div className="bg-[#1a1a1a] border border-gold/20 rounded-2xl w-full max-w-sm p-6 shadow-2xl animate-in zoom-in-95 duration-200">
                  <h3 className="text-xl font-bold text-gold mb-4">Atualizar Status</h3>
                  <form onSubmit={handleSaveStatus} className="space-y-4">
                    <div>
                      <label className="block text-xs font-semibold text-gray-400 mb-1">Situação do Serviço</label>
                      <select 
                        value={editingAgendamento.status}
                        onChange={(e) => setEditingAgendamento({...editingAgendamento, status: e.target.value})}
                        className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-gold outline-none"
                      >
                        <option value="PENDENTE">Pendente</option>
                        <option value="CONFIRMADO">Confirmado</option>
                        <option value="CONCLUIDO">Concluído</option>
                        <option value="CANCELADO">Cancelado</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-400 mb-1">Situação do Pagamento</label>
                      <select 
                        value={editingAgendamento.status_pagamento || 'PENDENTE'}
                        onChange={(e) => setEditingAgendamento({...editingAgendamento, status_pagamento: e.target.value})}
                        className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-gold outline-none"
                      >
                        <option value="PENDENTE">Pendente</option>
                        <option value="PAGO">Pago</option>
                      </select>
                    </div>
                    <div className="flex gap-3 pt-4">
                      <button 
                        type="button" 
                        onClick={() => setEditingAgendamento(null)}
                        className="flex-1 py-2.5 rounded-lg bg-transparent border border-white/20 text-gray-300 font-semibold text-sm hover:bg-white/5 transition-colors"
                      >
                        Cancelar
                      </button>
                      <button 
                        type="submit" 
                        disabled={savingStatus}
                        className="flex-1 py-2.5 rounded-lg bg-gold text-black font-bold text-sm hover:bg-yellow-500 disabled:opacity-50 transition-colors"
                      >
                        {savingStatus ? 'Salvando...' : 'Salvar Alterações'}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
              )}
              </>
            )}
          </div>
        )}

        {/* ABA: SERVIÇOS */}
        {activeTab === 'servicos' && <GestaoServicos />}

        {/* ABA: EQUIPE */}
        {activeTab === 'equipe' && <GestaoEquipe />}

        {/* ABA: FINANCEIRO */}
        {activeTab === 'financeiro' && <FinanceiroDashboard />}

        {/* ABA: CONFIGURACOES */}
        {activeTab === 'configuracoes' && userTipo === 'ADMINISTRADOR' && (
          <GestaoConfiguracoes />
        )}
        
        {/* ABA: CLIENTES */}
        {activeTab === 'clientes' && userTipo === 'ADMINISTRADOR' && (
          <GestaoClientes />
        )}
      </div>

      {/* MODAL DE BLOQUEIO */}
      <BloqueioHorarioModal 
        isOpen={bloqueioModalOpen} 
        onClose={() => setBloqueioModalOpen(false)} 
        onSave={() => {
          setBloqueioModalOpen(false);
          if (activeTab === 'agenda') fetchAgendamentos(currentFilters);
        }}
      />

      {/* MODAL DE CONFIRMACAO DE CANCELAMENTO */}
      <ConfirmModal 
        isOpen={cancelamentoModal.isOpen}
        title="Cancelar Agendamento"
        message={cancelamentoModal.agendamento ? `Tem certeza que deseja cancelar o agendamento de ${cancelamentoModal.agendamento.cliente_nome}? O horário será liberado imediatamente.` : ''}
        confirmText="Sim, Cancelar"
        cancelText="Voltar"
        isDestructive={true}
        onConfirm={confirmCancelamento}
        onCancel={() => setCancelamentoModal({ isOpen: false, agendamento: null })}
      />

      {/* PLACA QR CODE INVISÍVEL PARA GERAÇÃO DO PDF */}
      {userEmpresa && (
        <PlacaQRCode 
          ref={placaRef} 
          nomeBarbearia={userEmpresa.nome || userEmpresa.slug || 'SUA BARBEARIA'} 
          linkAgendamento={`${window.location.origin}/agendar/${userEmpresa.slug}`} 
        />
      )}
      </div>
    </div>
  );
}
