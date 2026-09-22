import { create } from 'zustand';

/**
 * Zustand Store para gerenciar o estado do fluxo de agendamento do cliente (Wizard).
 */
const getInitialEmpresa = () => {
  try {
    const item = localStorage.getItem('user_empresa');
    return item && item !== 'undefined' ? JSON.parse(item) : null;
  } catch {
    return null;
  }
};

const useAgendamentoStore = create((set) => ({
  // Estados iniciais de Agendamento
  empresaId: null,
  barbeiroId: null,
  servicosIds: [],
  dataHora: null,
  metodoPagamento: null,

  // Estados de Autenticação do Cliente
  userToken: localStorage.getItem('access_token') || null,
  userId: localStorage.getItem('user_id') || null,
  userNome: localStorage.getItem('user_nome') || null,
  userTipo: localStorage.getItem('user_tipo') || null,
  userEmpresa: getInitialEmpresa(),
  authModalOpen: false,

  // Ações de alteração de estado do Agendamento
  setEmpresaId: (id) => set({ empresaId: id, barbeiroId: null, servicosIds: [], dataHora: null, metodoPagamento: null }),
  
  setBarbeiroId: (id) => set({ barbeiroId: id, dataHora: null }),
  
  setServicosIds: (ids) => set({ servicosIds: ids, dataHora: null }),
  
  toggleServicoId: (id, empresaId) => set((state) => {
    if (empresaId != null && state.empresaId !== empresaId) {
      return { empresaId, servicosIds: [id], barbeiroId: null, dataHora: null, metodoPagamento: null };
    }
    const isSelected = state.servicosIds.includes(id);
    const newServicosIds = isSelected
      ? state.servicosIds.filter((servicoId) => servicoId !== id)
      : [...state.servicosIds, id];
    return { servicosIds: newServicosIds, dataHora: null };
  }),

  setDataHora: (data) => set({ dataHora: data }),

  setMetodoPagamento: (metodo) => set({ metodoPagamento: metodo }),

  // Ações de Autenticação
  login: (token, id, nome, tipo, empresa = null) => {
    localStorage.setItem('access_token', token);
    localStorage.setItem('user_id', id);
    localStorage.setItem('user_nome', nome);
    localStorage.setItem('user_tipo', tipo);
    if (empresa) {
        localStorage.setItem('user_empresa', JSON.stringify(empresa));
    } else {
        localStorage.removeItem('user_empresa');
    }
    set({ userToken: token, userId: id, userNome: nome, userTipo: tipo, userEmpresa: empresa, authModalOpen: false });
  },

  logout: () => {
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    if (accessToken && refreshToken) {
      const apiBase = (import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '')).replace(/\/+$/, '');
      fetch(`${apiBase}/api/logout/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
        keepalive: true,
      }).catch(() => {});
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_nome');
    localStorage.removeItem('user_tipo');
    localStorage.removeItem('user_empresa');
    set({ userToken: null, userId: null, userNome: null, userTipo: null, userEmpresa: null, empresaId: null, barbeiroId: null, servicosIds: [], dataHora: null, metodoPagamento: null });
  },

  setAuthModalOpen: (isOpen) => set({ authModalOpen: isOpen }),

  // Reseta o fluxo de agendamento mantendo a autenticação
  resetStore: () => set({
    empresaId: null,
    barbeiroId: null,
    servicosIds: [],
    dataHora: null,
    metodoPagamento: null,
  }),
}));

export default useAgendamentoStore;
