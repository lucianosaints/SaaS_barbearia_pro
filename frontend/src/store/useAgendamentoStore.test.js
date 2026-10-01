import { beforeEach, afterEach, it, expect, vi } from 'vitest';

let store;
beforeEach(async () => {
  vi.resetModules();
  vi.stubGlobal('localStorage', { getItem: () => null, setItem: vi.fn(), removeItem: vi.fn() });
  store = (await import('./useAgendamentoStore')).default;
});
afterEach(() => vi.unstubAllGlobals());

it('trocar serviço ou profissional invalida o horário selecionado', () => {
  store.getState().toggleServicoId(1, 10);
  store.getState().setBarbeiroId(5);
  store.getState().setDataHora('2030-01-01T10:00:00-03:00');
  store.getState().setBarbeiroId(6);
  expect(store.getState().dataHora).toBeNull();
  store.getState().setDataHora('2030-01-01T10:00:00-03:00');
  store.getState().toggleServicoId(2, 10);
  expect(store.getState().dataHora).toBeNull();
  expect(store.getState().servicosIds).toEqual([1, 2]);
});

it('não mistura serviços de barbearias distintas', () => {
  store.getState().toggleServicoId(1, 10);
  store.getState().setBarbeiroId(5);
  store.getState().toggleServicoId(2, 20);
  expect(store.getState().servicosIds).toEqual([2]);
  expect(store.getState().empresaId).toBe(20);
  expect(store.getState().barbeiroId).toBeNull();
});

it('notifica o backend no logout antes de remover os tokens locais', () => {
  const values = new Map([
    ['access_token', 'access-test'],
    ['refresh_token', 'refresh-test'],
  ]);
  const removeItem = vi.fn((key) => values.delete(key));
  vi.stubGlobal('localStorage', {
    getItem: (key) => values.get(key) || null,
    setItem: (key, value) => values.set(key, value),
    removeItem,
  });
  const fetchMock = vi.fn(() => Promise.resolve({ ok: true }));
  vi.stubGlobal('fetch', fetchMock);

  store.getState().logout();

  expect(fetchMock).toHaveBeenCalledWith(
    expect.stringContaining('/api/logout/'),
    expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({ Authorization: 'Bearer access-test' }),
      body: JSON.stringify({ refresh_token: 'refresh-test' }),
      keepalive: true,
    }),
  );
  expect(removeItem).toHaveBeenCalledWith('access_token');
  expect(removeItem).toHaveBeenCalledWith('refresh_token');
});
