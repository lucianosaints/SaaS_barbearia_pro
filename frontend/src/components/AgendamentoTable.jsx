import React from 'react';
import StatusBadge from './StatusBadge';
import useAgendamentoStore from '../store/useAgendamentoStore';

/**
 * Componente AgendamentoTable.
 * Renders a responsive table list of appointments.
 * 
 * @param {object} props
 * @param {Array} props.agendamentos - Lista de agendamentos
 */
export default function AgendamentoTable({ agendamentos, onStatusChange, updatingId }) {
  const { userId, userTipo } = useAgendamentoStore();
  // Auxiliar para formatar moeda brasileira
  const formatMoeda = (valor) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
  };

  // Auxiliar para formatar data e hora
  const formatDataHora = (dataStr) => {
    if (!dataStr) return '-';
    const data = new Date(dataStr);
    return data.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Calcula o valor total do agendamento somando seus serviços
  const calcularValorTotal = (servicos) => {
    if (!servicos || servicos.length === 0) return 0;
    return servicos.reduce((total, s) => total + parseFloat(s.preco), 0);
  };

  if (!agendamentos || agendamentos.length === 0) {
    return (
      <div className="bg-background-paper border border-white/5 rounded-xl p-8 text-center text-text-muted">
        Nenhum agendamento encontrado para os filtros selecionados.
      </div>
    );
  }

  return (
    <div className="bg-background-paper border border-white/5 rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-white/5 bg-background-darker/50 text-xs font-semibold text-text-secondary uppercase tracking-wider">
              <th className="px-6 py-4">Horário de Início</th>
              <th className="px-6 py-4">Horário de Fim</th>
              <th className="px-6 py-4">Cliente</th>
              <th className="px-6 py-4">Serviços</th>
              <th className="px-6 py-4">Profissional</th>
              <th className="px-6 py-4">Valor Total</th>
              <th className="px-6 py-4 text-center">Status</th>
              {onStatusChange && <th className="px-6 py-4">Ações</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-sm text-text-primary">
            {agendamentos.map((agendamento) => {
              // Detalhes extras vindos do get_representation do backend
              const servicos = agendamento.servicos_detalhes || [];
              const total = agendamento.valor_total !== null && agendamento.valor_total !== undefined
                ? Number(agendamento.valor_total) : calcularValorTotal(servicos);
              const canManage = userTipo === 'ADMINISTRADOR' || Number(userId) === agendamento.profissional;

              return (
                <tr key={agendamento.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-6 py-4 font-medium text-gold-light">
                    {formatDataHora(agendamento.data_hora_inicio)}
                  </td>
                  <td className="px-6 py-4 text-text-secondary">
                    {formatDataHora(agendamento.data_hora_fim)}
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-semibold">{agendamento.cliente_nome || `Usuário (ID: ${agendamento.cliente})`}</div>
                  </td>
                  <td className="px-6 py-4 max-w-[250px] truncate">
                    {servicos.length > 0 
                      ? servicos.map(s => s.nome).join(', ') 
                      : 'Sem serviços cadastrados'}
                  </td>
                  <td className="px-6 py-4 text-text-secondary">
                    {agendamento.profissional_nome || `Profissional (ID: ${agendamento.profissional})`}
                  </td>
                  <td className="px-6 py-4 font-bold text-accent-orange">
                    {formatMoeda(total)}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <StatusBadge status={agendamento.status} />
                  </td>
                  {onStatusChange && <td className="px-6 py-4">
                    {canManage && ['PENDENTE', 'CONFIRMADO'].includes(agendamento.status) && (
                      <div className="flex gap-2">
                        {agendamento.status === 'PENDENTE' && <button disabled={updatingId !== null} className="btn-gold-outline text-xs" onClick={() => onStatusChange(agendamento.id, 'CONFIRMADO')}>Confirmar</button>}
                        {agendamento.status === 'CONFIRMADO' && new Date(agendamento.data_hora_inicio) <= new Date() && <button disabled={updatingId !== null} className="btn-gold-outline text-xs" onClick={() => onStatusChange(agendamento.id, 'CONCLUIDO')}>Concluir</button>}
                        <button disabled={updatingId !== null} className="text-rose-400 text-xs" onClick={() => onStatusChange(agendamento.id, 'CANCELADO')}>Cancelar</button>
                      </div>
                    )}
                  </td>}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
