self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('event-cache-v1').then((cache) => {
      return cache.addAll([
        '/',
        '/index.html'
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
      }).catch(() => caches.match('/index.html')); // Fallback a caché si falla la red
    })
  );
});
