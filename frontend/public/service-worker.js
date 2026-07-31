const CACHE_NAME = 'salao-pro-v1';

self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
  // Apenas passa adiante todas as requisições para a rede
  // garantindo que não quebre chamadas de API ou WebSockets.
  event.respondWith(fetch(event.request));
});
