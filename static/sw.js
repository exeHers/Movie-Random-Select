const CACHE = "movie-night-v2";
const ASSETS = ["/", "/sync", "/static/manifest.webmanifest", "/static/icon.svg", "/static/app.css"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (
    url.pathname.startsWith("/movie/") ||
    url.pathname === "/" ||
    url.pathname === "/profiles" ||
    url.pathname === "/sync"
  ) {
    event.respondWith(
      fetch(req).catch(() => caches.match("/"))
    );
  }
});
