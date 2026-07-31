import axios from 'axios';

// Instância base do Axios apontando para o nosso backend Django
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '' : 'http://localhost:8000'),
  headers: {
    'Content-Type': 'application/json',
  },
});

// Flag e fila para evitar chamadas de refresh duplicadas e concorrentes
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Request Interceptor: Injeta o Access Token no Header de Autorização
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Trata a expiração do token (401) e renova silenciosamente
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Se o erro for 402 (Payment Required), redireciona para a tela de assinatura
    if (error.response?.status === 402) {
      window.location.href = '/admin/assinatura';
      return Promise.reject(error);
    }

    // Se o erro for 401 (Unauthorized) e não for uma tentativa repetida de obter token
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (originalRequest.url === '/api/token/' || originalRequest.url === '/api/token/refresh/') {
        // Se falhar na própria autenticação ou renovação, limpa os tokens e rejeita
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // Só redireciona se já não estivermos na página de login, para evitar loops
        if (window.location.pathname !== '/login') {
            window.location.href = '/login';
        }
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Enfileira as requisições concorrentes enquanto o refresh é processado
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        isRefreshing = false;
        // Sem refresh token, força deslogar
        localStorage.removeItem('access_token');
        if (window.location.pathname !== '/login') {
            window.location.href = '/login';
        }
        return Promise.reject(error);
      }

      try {
        // Usamos axios em vez de api.post para o refresh para não passar pelo interceptor
        // Mas como usamos api.post, a condição originalRequest.url === '/api/token/refresh/' acima já protege contra loops.
        const response = await api.post('/api/token/refresh/', {
          refresh: refreshToken,
        });

        const newAccessToken = response.data.access;
        localStorage.setItem('access_token', newAccessToken);

        // Se o endpoint de refresh também retornar um novo refresh_token (rotação ativa), salve-o
        if (response.data.refresh) {
          localStorage.setItem('refresh_token', response.data.refresh);
        }

        // Atualiza a autorização na requisição original e na fila
        api.defaults.headers.common.Authorization = `Bearer ${newAccessToken}`;
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

        processQueue(null, newAccessToken);
        isRefreshing = false;

        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;

        // Se falhar na renovação, limpa armazenamento e força redirecionamento (ex: deslogar)
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Dispara evento global ou redirecionamento de login se necessário
        window.dispatchEvent(new Event('auth_expired'));
        if (window.location.pathname !== '/login') {
            window.location.href = '/login';
        }
        
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
