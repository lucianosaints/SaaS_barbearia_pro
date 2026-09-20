import { beforeEach, afterEach, describe, it, expect, vi } from 'vitest';
import axios from 'axios';

let api;
const storage = new Map();

beforeEach(async () => {
  vi.resetModules();
  storage.clear();
  vi.stubGlobal('localStorage', {
    getItem: key => storage.get(key) ?? null,
    setItem: (key, value) => storage.set(key, String(value)),
    removeItem: key => storage.delete(key),
  });
  vi.stubGlobal('window', { dispatchEvent: vi.fn() });
  vi.stubEnv('VITE_API_URL', 'https://api.example.com/');
  api = (await import('./api')).default;
});

afterEach(() => { vi.restoreAllMocks(); vi.unstubAllEnvs(); vi.unstubAllGlobals(); });

function unauthorized(config) {
  const error = new Error('Unauthorized');
  error.config = config;
  error.response = { status: 401 };
  return Promise.reject(error);
}

describe('sessão da API', () => {
  it('renova no servidor configurado e persiste o refresh rotacionado', async () => {
    storage.set('access_token', 'old');
    storage.set('refresh_token', 'refresh-old');
    const refreshed = vi.spyOn(axios, 'post').mockResolvedValue({ data: { access: 'new', refresh: 'refresh-new' } });
    api.defaults.adapter = vi.fn(config => config.headers.Authorization === 'Bearer new'
      ? Promise.resolve({ data: 'ok', status: 200, config }) : unauthorized(config));
    const response = await api.get('/api/agendamentos/');
    expect(response.data).toBe('ok');
    expect(refreshed).toHaveBeenCalledWith('https://api.example.com/api/token/refresh/', { refresh: 'refresh-old' }, { timeout: 15000 });
    expect(storage.get('refresh_token')).toBe('refresh-new');
  });

  it('compartilha uma renovação entre requisições concorrentes', async () => {
    storage.set('access_token', 'old');
    storage.set('refresh_token', 'refresh-old');
    let finish;
    const refreshed = vi.spyOn(axios, 'post').mockImplementation(() => new Promise(resolve => { finish = resolve; }));
    api.defaults.adapter = vi.fn(config => config.headers.Authorization === 'Bearer new'
      ? Promise.resolve({ data: 'ok', status: 200, config }) : unauthorized(config));
    const requests = Promise.all([api.get('/one'), api.get('/two')]);
    await vi.waitFor(() => expect(refreshed).toHaveBeenCalledTimes(1));
    finish({ data: { access: 'new' } });
    expect((await requests).map(r => r.data)).toEqual(['ok', 'ok']);
    expect(refreshed).toHaveBeenCalledTimes(1);
  });

  it('remove tokens expirados e avisa a interface após falha no refresh', async () => {
    storage.set('access_token', 'old');
    storage.set('refresh_token', 'expired');
    vi.spyOn(axios, 'post').mockRejectedValue(new Error('Expired'));
    api.defaults.adapter = unauthorized;
    await expect(api.get('/api/agendamentos/')).rejects.toThrow('Expired');
    expect(storage.has('access_token')).toBe(false);
    expect(storage.has('refresh_token')).toBe(false);
    expect(window.dispatchEvent).toHaveBeenCalled();
  });

  it('não mantém Authorization após logout', async () => {
    api.defaults.adapter = vi.fn(config => Promise.resolve({ status: 200, config, data: config.headers.Authorization }));
    storage.set('access_token', 'old');
    expect((await api.get('/one')).data).toBe('Bearer old');
    storage.delete('access_token');
    expect((await api.get('/two')).data).toBeUndefined();
  });
});
