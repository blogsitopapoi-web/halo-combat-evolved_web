/*! coi-serviceworker v0.1.7 | MIT License | https://github.com */
if (typeof window === 'undefined') {
    self.addEventListener('install', () => self.skipWaiting());
    self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
    self.addEventListener('fetch', e => {
        if (e.request.cache === 'only-if-cached' && e.request.mode !== 'same-origin') return;
        e.respondWith(
            fetch(e.request).then(r => {
                if (r.status === 0) return r;
                const h = new Headers(r.headers);
                h.set('Cross-Origin-Opener-Policy', 'same-origin');
                h.set('Cross-Origin-Embedder-Policy', 'require-corp');
                return new Response(r.body, { status: r.status, statusText: r.statusText, headers: h });
            }).catch(err => console.error(err))
        );
    });
} else {
    const s = document.currentScript;
    if (s && s.hasAttribute('data-coi')) {
        navigator.serviceWorker.register(s.src).then(r => {
            r.addEventListener('updatefound', () => location.reload());
            if (r.active && !navigator.serviceWorker.controller) location.reload();
        });
    }
}
