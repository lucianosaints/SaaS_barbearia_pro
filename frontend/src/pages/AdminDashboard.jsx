import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import FilterBar from '../components/FilterBar';
import AgendaTable from '../components/AgendaTable';
import GestaoServicos from './GestaoServicos';
import GestaoEquipe from './GestaoEquipe';
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
            
            <button 
              onClick={gerarPDF} 
              disabled={gerandoPDF}
              className="mt-4 w-full sm:w-auto bg-white text-black hover:bg-gray-200 px-4 py-2 rounded-md font-bold text-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
            >
              🖨️ {gerandoPDF ? 'Gerando PDF...' : 'Baixar Placa QR Code (PDF)'}
            </button>
          </div>
        )}
      </div>

      {/* Menu de Navegação (Tabs) */}
      <div className="flex flex-wrap gap-2 sm:gap-4 mb-8 pb-2">
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
            <button
              onClick={() => setActiveTab('configuracoes')}
              className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all whitespace-nowrap ${
                activeTab === 'configuracoes' 
                ? 'bg-gold text-background-darker shadow-lg shadow-gold/20' 
                : 'bg-background-paper border border-white/5 text-text-secondary hover:text-white hover:border-white/20'
              }`}
            >
              ⚙️ Configurações
            </button>
          </>
        )}
      </div>

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
        {activeTab === 'configuracoes' && <GestaoConfiguracoes />}

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
  );
}
