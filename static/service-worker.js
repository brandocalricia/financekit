// FinanceKit Service Worker v5.1 — offline caching + PWA support
const CACHE_NAME = 'financekit-v5.1';
const OFFLINE_URL = '/';

// Cache the app shell on install
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll([
        OFFLINE_URL,
        '/app/static/manifest.json',
        '/app/static/icons/icon-192.png',
        '/app/static/icons/icon-512.png',
      ]);
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
              '<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
              '<title>FinanceKit - Offline</title></head>' +
              '<body style="background:#0f1117;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;' +
              'display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center;">' +
              '<div><div style="font-size:3rem;margin-bottom:1rem;">📴</div>' +
              '<h1 style="font-size:1.5rem;margin:0 0 0.5rem;">You\'re Offline</h1>' +
              '<p style="color:#94a3b8;max-width:300px;">FinanceKit needs an internet connection to load. ' +
              'Please check your connection and try again.</p>' +
              '<button onclick="location.reload()" style="margin-top:1rem;padding:10px 24px;background:#6366f1;' +
              'color:white;border:none;border-radius:8px;font-size:1rem;cursor:pointer;">Retry</button>' +
              '</div></body></html>',
              { headers: { 'Content-Type': 'text/html' } }
            );
          }
        });
      })
  );
});
