import { create } from 'zustand';

/**
 * Zustand Store para gerenciar o estado do fluxo de agendamento do cliente (Wizard).
 */
const useAgendamentoStore = create((set) => ({
  // Estados iniciais de Agendamento
  empresaId: null,
  barbeiroId: null,
  servicosIds: [],
  dataHora: null,

  // Estados de Autenticação do Cliente
  userToken: localStorage.getItem('access_token') || null,
  userId: localStorage.getItem('user_id') || null,
  userNome: localStorage.getItem('user_nome') || null,
  userTipo: localStorage.getItem('user_tipo') || null,
  userEmpresa: JSON.parse(localStorage.getItem('user_empresa')) || null,
  authModalOpen: false,

  // Ações de alteração de estado do Agendamento
  setEmpresaId: (id) => set({ empresaId: id, barbeiroId: null, servicosIds: [], dataHora: null }),
  
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
  login: (token, id, nome, tipo, empresa = null) => {
    localStorage.setItem('access_token', token);
    localStorage.setItem('user_id', id);
    localStorage.setItem('user_nome', nome);
    localStorage.setItem('user_tipo', tipo);
    if (empresa) {
        localStorage.setItem('user_empresa', JSON.stringify(empresa));
    }
    set({ userToken: token, userId: id, userNome: nome, userTipo: tipo, userEmpresa: empresa, authModalOpen: false });
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_nome');
    localStorage.removeItem('user_tipo');
    localStorage.removeItem('user_empresa');
    set({ userToken: null, userId: null, userNome: null, userTipo: null, userEmpresa: null });
  },

  setAuthModalOpen: (isOpen) => set({ authModalOpen: isOpen }),

  // Reseta o fluxo de agendamento mantendo a autenticação
  resetStore: () => set({
    empresaId: null,
    barbeiroId: null,
    servicosIds: [],
    dataHora: null,
  }),
}));

export default useAgendamentoStore;
