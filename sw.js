/* SonoPlay — cache offline */
const CACHE = "sonoplay-v7";
const V = "?v=7";

const ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icon.svg",
  "./icon-192.png",
  "./icon-512.png",
  "./audio/01-tempestade.mp3" + V,
  "./audio/02-batidas.mp3" + V,
  "./audio/03-suspense.mp3" + V,
  "./audio/04-quebra.mp3" + V,
  "./audio/05-janela.mp3" + V,
  "./audio/06-passos.mp3" + V,
  "./audio/07-porta.mp3" + V,
  "./audio/08-melancolico.mp3" + V
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => Promise.allSettled(
        // no-cache: nunca copia uma cópia velha vinda do cache HTTP do navegador
        ASSETS.map((a) => fetch(a, { cache: "no-cache" }).then((r) => c.put(a, r)))
      ))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const isAudio = new URL(e.request.url).pathname.endsWith(".mp3");

  if (isAudio){
    // áudio: rede primeiro (sempre a versão atual), cache só como plano offline
    e.respondWith(
      fetch(e.request, { cache: "no-cache" })
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then((hit) =>
      hit ||
      fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        return res;
      }).catch(() => caches.match("./index.html"))
    )
  );
});
