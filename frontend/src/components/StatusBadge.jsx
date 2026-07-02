import React from 'react';

/**
 * Componente StatusBadge.
 * Exibe o status do agendamento formatado com cores específicas no tema dark.
 * 
 * @param {object} props
 * @param {string} props.status - O status ('PENDENTE', 'CONFIRMADO', 'CONCLUIDO', 'CANCELADO')
 */
export default function StatusBadge({ status }) {
  const normalizedStatus = (status || 'PENDENTE').toUpperCase();

  const config = {
    PENDENTE: {
      label: 'Pendente',
      classes: 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20',
    },
    CONFIRMADO: {
      label: 'Confirmado',
      classes: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
    },
    CONCLUIDO: {
      label: 'Concluído',
      classes: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
    },
    CANCELADO: {
      label: 'Cancelado',
      classes: 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
    },
  };

  const current = config[normalizedStatus] || config.PENDENTE;

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium tracking-wide ${current.classes}`}>
      {current.label}
    </span>
  );
}
