self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('event-cache-v1').then((cache) => {
      return cache.addAll([
        '/',
        '/index.html',
        'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js'
      ]);
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request).then((networkResponse) => {
        if (event.request.url.includes('/api/users')) {
          caches.open('event-cache-v1').then((cache) => {
            cache.put(event.request, networkResponse.clone());
          });
        }
        return networkResponse;
      });
    })
  );
});
