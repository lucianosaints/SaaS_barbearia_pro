import { create } from 'zustand';

/**
 * Zustand Store para gerenciar o estado do fluxo de agendamento do cliente (Wizard).
 */
const useAgendamentoStore = create((set) => ({
  // Estados iniciais de Agendamento
  barbeiroId: null,
  servicosIds: [],
  dataHora: null,

  // Estados de Autenticação do Cliente
  userToken: localStorage.getItem('access_token') || null,
  userId: localStorage.getItem('user_id') || null,
  userNome: localStorage.getItem('user_nome') || null,
  userTipo: localStorage.getItem('user_tipo') || null,
  authModalOpen: false,

  // Ações de alteração de estado do Agendamento
  setBarbeiroId: (id) => set({ barbeiroId: id }),
  
  setServicosIds: (ids) => set({ servicosIds: ids }),
  
  toggleServicoId: (id) => set((state) => {
    const isSelected = state.servicosIds.includes(id);
    const newServicosIds = isSelected
      ? state.servicosIds.filter((servicoId) => servicoId !== id)
      : [...state.servicosIds, id];
    return { servicosIds: newServicosIds };
  }),

  setDataHora: (data) => set({ dataHora: data }),

  // Ações de Autenticação
  login: (token, id, nome, tipo) => {
    localStorage.setItem('access_token', token);
    localStorage.setItem('user_id', id);
    localStorage.setItem('user_nome', nome);
    localStorage.setItem('user_tipo', tipo);
    set({ userToken: token, userId: id, userNome: nome, userTipo: tipo, authModalOpen: false });
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_nome');
    localStorage.removeItem('user_tipo');
    set({ userToken: null, userId: null, userNome: null, userTipo: null });
  },

  setAuthModalOpen: (isOpen) => set({ authModalOpen: isOpen }),

  // Reseta o fluxo de agendamento mantendo a autenticação
  resetStore: () => set({
    barbeiroId: null,
    servicosIds: [],
    dataHora: null,
  }),
}));

export default useAgendamentoStore;
