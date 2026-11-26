// Service worker de ReportaYa (RNF-11): la aplicación abre sin señal (sótano, cuarto de bombas).
// - Navegación: red primero; sin red, la última versión guardada de index.html.
// - Archivos compilados (/assets/*, con hash en el nombre) e íconos: caché primero.
// - El API (/api/v1) NO pasa por aquí: lo maneja la app (cola de envíos y lectura sin conexión),
//   porque las respuestas dependen del usuario que inició sesión.
const VERSION = 'reportaya-v1'

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(['/', '/index.html', '/manifest.webmanifest', '/icono-192.png'])).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSION).map((k) => caches.delete(k)))).then(() => self.clients.claim()))
})

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url)
  if (e.request.method !== 'GET' || url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return
  if (e.request.mode === 'navigate') {
    e.respondWith(
      fetch(e.request)
        .then((r) => { const copia = r.clone(); caches.open(VERSION).then((c) => c.put('/index.html', copia)); return r })
        .catch(() => caches.match('/index.html')),
    )
    return
  }
  e.respondWith(
    caches.match(e.request).then((guardado) => guardado || fetch(e.request).then((r) => {
      if (r.ok) { const copia = r.clone(); caches.open(VERSION).then((c) => c.put(e.request, copia)) }
      return r
    })),
  )
})
