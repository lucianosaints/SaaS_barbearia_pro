const FIELD_LABELS = {
  cliente: 'Cliente',
  profissional: 'Profissional',
  servicos: 'Serviço',
  data_hora_inicio: 'Data e horário',
  metodo_pagamento: 'Forma de pagamento',
};

const firstMessage = (value) => {
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) {
    for (const item of value) {
      const message = firstMessage(item);
      if (message) return message;
    }
  }
  return null;
};

export function formatApiError(error) {
  if (error?.code === 'ECONNABORTED') {
    return 'A confirmação demorou mais que o esperado. Confira “Minha Agenda” antes de tentar novamente.';
  }

  const data = error?.response?.data;
  if (typeof data === 'string' && data.trim()) return data;
  if (!data || typeof data !== 'object') {
    return 'Ocorreu uma falha ao realizar o agendamento. Por favor, tente novamente.';
  }

  const preferred = firstMessage(data.non_field_errors) || firstMessage(data.detail);
  if (preferred) return preferred;

  for (const [field, value] of Object.entries(data)) {
    const message = firstMessage(value);
    if (message) return `${FIELD_LABELS[field] || field}: ${message}`;
  }

  return 'Ocorreu uma falha ao realizar o agendamento. Por favor, tente novamente.';
}
