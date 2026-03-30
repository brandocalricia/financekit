// FinanceKit Service Worker — basic caching for faster load
const CACHE_NAME = 'financekit-v4.0';
const OFFLINE_URL = '/';

// Cache the app shell on install
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll([OFFLINE_URL]);
    })
  );
  self.skipWaiting();
});

// Clean up old caches on activate
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Network-first strategy — fall back to cache if offline
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Cache successful responses
        if (response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Offline — try cache
        return caches.match(event.request).then((response) => {
          if (response) return response;
          // Show offline message for navigation requests
          if (event.request.mode === 'navigate') {
            return new Response(
              '<html><body style="background:#0f1117;color:#e2e8f0;font-family:sans-serif;' +
              'display:flex;align-items:center;justify-content:center;height:100vh;text-align:center;">' +
              '<div><h1>You\'re Offline</h1><p>FinanceKit needs an internet connection to load.</p>' +
              '<p>Please check your connection and try again.</p></div></body></html>',
              { headers: { 'Content-Type': 'text/html' } }
            );
          }
        });
      })
  );
});
