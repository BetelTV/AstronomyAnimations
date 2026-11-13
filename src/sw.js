// sw.js — service worker: guarda o site no aparelho para o app funcionar sem internet.
// Estratégia: responde com a cópia guardada (rápido e offline) e, em paralelo, busca a versão nova na rede
// e atualiza a cópia. Assim, depois de publicar mudanças, o app se atualiza sozinho na abertura seguinte.
// Ao acrescentar um arquivo novo ao site, inclua-o em ARQUIVOS e mude a VERSAO.
const VERSAO = "sol-terra-lua-v1";
const ARQUIVOS = [
  "./", "index.html", "modelo1.html", "modelo2.html", "astro.js", "estilo.css", "app.js", "manifest.webmanifest",
  "vendor/three.module.min.js", "vendor/addons/controls/OrbitControls.js", "vendor/addons/renderers/CSS2DRenderer.js",
  "vendor/mundo.json",
  "icones/icone-192.png", "icones/icone-512.png", "icones/icone-maskable-512.png", "icones/apple-touch-icon.png", "icones/favicon-32.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSAO).then((c) => c.addAll(ARQUIVOS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((nomes) => Promise.all(nomes.filter((n) => n !== VERSAO).map((n) => caches.delete(n))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  e.respondWith(caches.open(VERSAO).then(async (cache) => {
    const guardado = await cache.match(req, { ignoreSearch: true });
    const daRede = fetch(req).then((resp) => {
      if (resp.ok) cache.put(req, resp.clone());
      return resp;
    }).catch(() => null);
    if (guardado) { e.waitUntil(daRede); return guardado; }
    const resp = await daRede;
    if (resp) return resp;
    if (req.mode === "navigate") return (await cache.match("index.html")) || Response.error();
    return Response.error();
  }));
});
