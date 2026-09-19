const CACHE_NAME = "montour-cache-v2";
const CORE_ASSETS = [
    "/",
    "/manifest.json",
    "/static/icons/icon-192.png",
    "/static/icons/icon-512.png",
];

// Installation : met en cache les fichiers essentiels de l'application
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS))
    );
    self.skipWaiting();
});

// Activation : nettoie les anciens caches
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys
                    .filter((key) => key !== CACHE_NAME)
                    .map((key) => caches.delete(key))
            )
        )
    );
    self.clients.claim();
});

// Stratégie : réseau d'abord, repli sur le cache (fonctionne aussi hors-ligne)
self.addEventListener("fetch", (event) => {
    if (event.request.method !== "GET") return;

    const url = new URL(event.request.url);
    // Jamais de cache pour l'API : ses réponses sont privées (profil, tickets…) et
    // seraient resservies à un autre compte sur le même appareil, ou périmées.
    if (url.origin !== self.location.origin || url.pathname.startsWith("/api/")) return;

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // On ne met en cache que les réponses réussies (pas d'erreurs 4xx/5xx)
                if (response.ok) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                }
                return response;
            })
            .catch(() =>
                caches.match(event.request).then((cached) => cached || caches.match("/"))
            )
    );
});