import React, { useState, useEffect } from 'react';
import api from '../services/api';
import ClientAgendaCard from '../components/ClientAgendaCard';
import useAgendamentoStore from '../store/useAgendamentoStore';
import CartaoFidelidadeCard from '../components/CartaoFidelidadeCard';

export default function PainelCliente() {
  const { userEmpresa } = useAgendamentoStore();
  const [agendamentos, setAgendamentos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Estados para o modal de Perfil
  const [perfilModalOpen, setPerfilModalOpen] = useState(false);
  const [perfilData, setPerfilData] = useState({ first_name: '', last_name: '', email: '', telefone: '' });
  const [salvandoPerfil, setSalvandoPerfil] = useState(false);
  const [perfilSuccess, setPerfilSuccess] = useState('');
  const [perfilError, setPerfilError] = useState('');

  // Estados para o modal customizado de cancelamento
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [selectedAgendamentoId, setSelectedAgendamentoId] = useState(null);
  const [canceling, setCanceling] = useState(false);

  const fetchAgendamentos = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/api/agendamentos/');
      // O backend já garante que só vêm os agendamentos do cliente logado
      setAgendamentos(response.data.results || response.data);
    } catch (err) {
      console.error('Erro ao buscar histórico do cliente:', err);
      setError('Não foi possível carregar seus agendamentos.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgendamentos();
  }, []);

  const handleOpenPerfilModal = async () => {
    setPerfilModalOpen(true);
    setPerfilSuccess('');
    setPerfilError('');
    try {
      const response = await api.get('/api/usuarios/me/');
      setPerfilData({
        first_name: response.data.first_name || '',
        last_name: response.data.last_name || '',
        email: response.data.email || '',
        telefone: response.data.telefone || ''
      });
    } catch (err) {
      setPerfilError('Não foi possível carregar os dados do perfil.');
    }
  };

  const handleSavePerfil = async (e) => {
    e.preventDefault();
    setSalvandoPerfil(true);
    setPerfilSuccess('');
    setPerfilError('');
    try {
      await api.patch('/api/usuarios/me/', {
        first_name: perfilData.first_name,
        last_name: perfilData.last_name,
        telefone: perfilData.telefone
      });
      setPerfilSuccess('Perfil atualizado com sucesso!');
      setTimeout(() => setPerfilModalOpen(false), 2000);
    } catch (err) {
      setPerfilError('Erro ao atualizar o perfil. Tente novamente.');
    } finally {
      setSalvandoPerfil(false);
    }
  };

  const handleOpenCancelModal = (id) => {
    setSelectedAgendamentoId(id);
    setCancelModalOpen(true);
  };

  const handleConfirmarCancelamento = async () => {
    if (!selectedAgendamentoId) return;
    setCanceling(true);
    try {
      await api.patch(`/api/agendamentos/${selectedAgendamentoId}/cancelar/`);
      setCancelModalOpen(false);
      setSelectedAgendamentoId(null);
      fetchAgendamentos();
    } catch (err) {
      console.error('Erro ao cancelar agendamento:', err);
      setError('Falha ao cancelar o agendamento. Tente novamente mais tarde.');
    } finally {
      setCanceling(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-text-muted">Carregando sua agenda...</div>;
  }

  if (error) {
    return <div className="p-8 text-center text-rose-400 bg-rose-500/10 rounded-xl m-4">{error}</div>;
  }

  const agora = new Date();

  // Separa os agendamentos
  const futuros = agendamentos.filter((a) => {
    const dataAgendamento = new Date(a.data_hora_inicio);
    return dataAgendamento >= agora && a.status !== 'CANCELADO';
  });

  const passados = agendamentos.filter((a) => {
    const dataAgendamento = new Date(a.data_hora_inicio);
    return dataAgendamento < agora || a.status === 'CANCELADO';
  });



  return (
    <div className="w-full max-w-4xl mx-auto py-8 px-4 space-y-10">
      <CartaoFidelidadeCard />
      
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-2">
        <div>
          <h2 className="text-2xl font-bold text-text-primary mb-2">Próximos Agendamentos</h2>
          <p className="text-text-muted text-sm">Confira seus horários marcados ou efetue o cancelamento se necessário.</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleOpenPerfilModal}
            className="px-4 py-2.5 text-sm font-semibold rounded-lg bg-background-darker border border-white/10 text-text-primary hover:border-gold/50 transition-colors"
          >
            Meus Dados
          </button>
          {userEmpresa && userEmpresa.slug && (
            <button
              onClick={() => window.open(`/agendar/${userEmpresa.slug}`, '_blank')}
              className="btn-gold px-6 py-2.5 text-sm"
            >
              + Novo Agendamento
            </button>
          )}
        </div>
      </div>

      <div>
        {futuros.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {futuros.map(a => <ClientAgendaCard key={a.id} agendamento={a} isFuturo={true} onCancel={handleOpenCancelModal} />)}
          </div>
        ) : (
          <div className="p-8 text-center text-text-muted bg-background-darker rounded-xl border border-white/5">
            Você não possui nenhum agendamento futuro no momento.
          </div>
        )}
      </div>

      <div>
        <h2 className="text-xl font-bold text-text-primary mb-2">Histórico</h2>
        <p className="text-text-muted text-sm mb-6">Seus agendamentos anteriores e horários cancelados.</p>
        
        {passados.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {passados.map(a => <ClientAgendaCard key={a.id} agendamento={a} isFuturo={false} onCancel={handleOpenCancelModal} />)}
          </div>
        ) : (
          <div className="p-8 text-center text-text-muted bg-background-darker rounded-xl border border-white/5">
            Seu histórico de agendamentos está vazio.
          </div>
        )}
      </div>

      {/* Modal Customizado de Confirmação de Cancelamento */}
      {cancelModalOpen && (
        <div className="fixed inset-0 bg-background-darker/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-background-paper border border-white/5 rounded-2xl w-full max-w-sm overflow-hidden relative shadow-2xl shadow-rose-500/5 p-6 space-y-5 animate-in fade-in zoom-in-95 duration-200">
            
            {/* Ícone de Alerta */}
            <div className="w-12 h-12 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-full flex items-center justify-center text-xl mx-auto">
              ⚠️
            </div>

            <div className="text-center space-y-2">
              <h3 className="text-base font-bold text-text-primary">Confirmar Cancelamento</h3>
              <p className="text-text-muted text-xs leading-relaxed">
                Tem certeza que deseja cancelar este agendamento? Esta ação liberará a vaga na agenda e não poderá ser desfeita.
              </p>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => {
                  setCancelModalOpen(false);
                  setSelectedAgendamentoId(null);
                }}
                className="flex-1 py-2.5 text-xs font-semibold rounded-lg bg-background-darker border border-white/10 text-text-primary hover:border-white/20 transition-colors"
                disabled={canceling}
              >
                Voltar
              </button>
              <button
                type="button"
                onClick={handleConfirmarCancelamento}
                className="flex-1 py-2.5 text-xs font-semibold rounded-lg bg-rose-600 text-white hover:bg-rose-700 transition-colors shadow-md shadow-rose-600/15 flex items-center justify-center gap-2"
                disabled={canceling}
              >
                {canceling ? (
                  <>
                    <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    Processando...
                  </>
                ) : (
                  'Sim, Cancelar'
                )}
              </button>
            </div>

          </div>
        </div>
      )}
      {/* Modal de Perfil */}
      {perfilModalOpen && (
        <div className="fixed inset-0 bg-background-darker/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-background-paper border border-white/5 rounded-2xl w-full max-w-md overflow-hidden relative shadow-2xl p-6 space-y-5 animate-in fade-in zoom-in-95 duration-200">
            
            <div className="flex justify-between items-center border-b border-white/10 pb-3">
              <h3 className="text-lg font-bold text-text-primary">Meus Dados</h3>
              <button onClick={() => setPerfilModalOpen(false)} className="text-text-muted hover:text-white transition-colors">
                ✕
              </button>
            </div>

            {perfilSuccess && (
              <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400 text-sm text-center">
                {perfilSuccess}
              </div>
            )}
            
            {perfilError && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-sm text-center">
                {perfilError}
              </div>
            )}

            <form onSubmit={handleSavePerfil} className="space-y-4 text-left">
              <div>
                <label className="block text-xs font-semibold text-text-muted mb-1">Nome</label>
                <input
                  type="text"
                  required
                  className="w-full px-3 py-2 bg-background-darker border border-white/10 rounded-lg text-sm text-text-primary focus:outline-none focus:border-gold/50"
                  value={perfilData.first_name}
                  onChange={(e) => setPerfilData({...perfilData, first_name: e.target.value})}
                />
              </div>
              
              <div>
                <label className="block text-xs font-semibold text-text-muted mb-1">Sobrenome</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 bg-background-darker border border-white/10 rounded-lg text-sm text-text-primary focus:outline-none focus:border-gold/50"
                  value={perfilData.last_name}
                  onChange={(e) => setPerfilData({...perfilData, last_name: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-muted mb-1">Telefone (WhatsApp)</label>
                <input
                  type="text"
                  required
                  className="w-full px-3 py-2 bg-background-darker border border-white/10 rounded-lg text-sm text-text-primary focus:outline-none focus:border-gold/50"
                  value={perfilData.telefone}
                  onChange={(e) => setPerfilData({...perfilData, telefone: e.target.value})}
                  placeholder="Ex: 11999999999"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-muted mb-1">E-mail</label>
                <input
                  type="email"
                  disabled
                  className="w-full px-3 py-2 bg-background-darker/50 border border-white/5 rounded-lg text-sm text-text-muted cursor-not-allowed"
                  value={perfilData.email}
                />
                <p className="text-[10px] text-text-muted mt-1">O e-mail de login não pode ser alterado.</p>
              </div>

              <div className="pt-4 flex gap-3">
                <button
                  type="button"
                  onClick={() => setPerfilModalOpen(false)}
                  className="flex-1 py-2.5 text-xs font-semibold rounded-lg bg-background-darker border border-white/10 text-text-primary hover:border-white/20 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={salvandoPerfil}
                  className="flex-1 py-2.5 text-xs font-semibold rounded-lg bg-gold text-background-darker hover:bg-gold-light transition-colors shadow-md shadow-gold/20 flex items-center justify-center gap-2"
                >
                  {salvandoPerfil ? 'Salvando...' : 'Salvar Alterações'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
