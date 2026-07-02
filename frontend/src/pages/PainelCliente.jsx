import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function PainelCliente() {
  const [agendamentos, setAgendamentos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  const handleCancelar = async (id) => {
    if (!window.confirm('Tem certeza que deseja cancelar este agendamento? Esta ação não pode ser desfeita.')) {
      return;
    }

    try {
      await api.patch(`/api/agendamentos/${id}/cancelar/`);
      // Atualiza a lista localmente para refletir o cancelamento
      fetchAgendamentos();
    } catch (err) {
      console.error('Erro ao cancelar agendamento:', err);
      alert('Falha ao cancelar o agendamento. Tente novamente mais tarde.');
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

  const AgendamentoCard = ({ agendamento, isFuturo }) => {
    const data = new Date(agendamento.data_hora_inicio);
    const dataFormatada = data.toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' });
    const horaFormatada = data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    
    // Calcula serviços e valor total
    const detalhes = agendamento.servicos_detalhes || [];
    const nomesServicos = detalhes.map(s => s.nome).join(', ') || 'Serviços não listados';
    const valorTotal = detalhes.reduce((acc, curr) => acc + parseFloat(curr.preco), 0);

    return (
      <div className={`p-4 rounded-xl border flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 transition-all ${
        agendamento.status === 'CANCELADO' ? 'bg-background-darker border-white/5 opacity-60' : 'bg-background-paper border-white/10 shadow-lg shadow-black/20'
      }`}>
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="text-gold-light font-bold text-lg">{dataFormatada}</span>
            <span className="text-text-secondary text-sm border-l border-white/20 pl-2">{horaFormatada}</span>
            {agendamento.status === 'CANCELADO' && (
              <span className="ml-2 px-2 py-0.5 text-[10px] uppercase font-bold bg-rose-500/20 text-rose-400 rounded border border-rose-500/30">
                Cancelado
              </span>
            )}
          </div>
          <div className="text-text-primary text-sm font-medium">{nomesServicos}</div>
          <div className="text-text-muted text-xs flex items-center gap-3">
            <span>💈 Profissional ID: {agendamento.profissional}</span>
            <span>💰 R$ {valorTotal.toFixed(2).replace('.', ',')}</span>
          </div>
        </div>
        
        {isFuturo && agendamento.status !== 'CANCELADO' && (
          <button
            onClick={() => handleCancelar(agendamento.id)}
            className="w-full sm:w-auto px-4 py-2 rounded-lg text-sm font-semibold transition-all text-rose-400 border border-rose-500/30 hover:bg-rose-500/10 hover:border-rose-500/50"
          >
            Cancelar Agendamento
          </button>
        )}
      </div>
    );
  };

  return (
    <div className="w-full max-w-4xl mx-auto py-8 px-4 space-y-10">
      <div>
        <h2 className="text-2xl font-bold text-text-primary mb-2">Próximos Agendamentos</h2>
        <p className="text-text-muted text-sm mb-6">Confira seus horários marcados ou efetue o cancelamento se necessário.</p>
        
        {futuros.length > 0 ? (
          <div className="space-y-4">
            {futuros.map(a => <AgendamentoCard key={a.id} agendamento={a} isFuturo={true} />)}
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
          <div className="space-y-4">
            {passados.map(a => <AgendamentoCard key={a.id} agendamento={a} isFuturo={false} />)}
          </div>
        ) : (
          <div className="p-8 text-center text-text-muted bg-background-darker rounded-xl border border-white/5">
            Seu histórico de agendamentos está vazio.
          </div>
        )}
      </div>
    </div>
  );
}
