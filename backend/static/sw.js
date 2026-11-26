/* Linda service worker — caches the app shell so the UI loads instantly
   and the app can be installed on the Android home screen.
   API calls (/health, /chat, /tasks, ...) are never cached: they always
   go to the network, because they are live agent work. */
var CACHE_NAME = "linda-shell-v21";
var SHELL_FILES = [
  "/",
  "/index.html",
  "/style.css",
  "/app.js",
  "/manifest.json",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "/icons/icon-180.png"
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(SHELL_FILES);
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (k) { return k !== CACHE_NAME; })
          .map(function (k) { return caches.delete(k); })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", function (event) {
  var url = new URL(event.request.url);

  // API calls: network only, never cached.
  if (url.pathname === "/chat" || url.pathname === "/health" ||
      url.pathname === "/health/detailed" || url.pathname === "/settings" ||
      url.pathname === "/config" || url.pathname === "/memory" ||
      url.pathname.indexOf("/tasks") === 0) {
    event.respondWith(fetch(event.request));
    return;
  }

  // App shell: cache first, fall back to network.
  event.respondWith(
    caches.match(event.request).then(function (cached) {
      if (cached) return cached;
      return fetch(event.request).then(function (response) {
        if (response.ok && event.request.method === "GET") {
          var copy = response.clone();
          caches.open(CACHE_NAME).then(function (cache) {
            cache.put(event.request, copy);
          });
        }
        return response;
      });
    })
  );
});
