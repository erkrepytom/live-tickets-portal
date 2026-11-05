/* MyTickets Tours: service worker.
   Páginas: rede primeiro (conteúdo sempre atual); sem internet, a última cópia vista ou /offline.html.
   /assets/: cache primeiro (as URLs já levam ?v=<hash>, então arquivo novo tem URL nova).
   Nada de outros domínios é interceptado (Analytics, YouTube, Open-Meteo passam direto). */
const VERSAO = "mt-v1";
const PAGINAS = VERSAO + "-paginas";
const ARQUIVOS = VERSAO + "-arquivos";
const OFFLINE = new URL("offline.html", self.registration.scope).href;

self.addEventListener("install", ev => {
  ev.waitUntil(caches.open(PAGINAS).then(c => c.add(OFFLINE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", ev => {
  ev.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => !k.startsWith(VERSAO)).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
async function limitar(nome, max){
  const c = await caches.open(nome);
  const ks = await c.keys();
  for (let i = 0; i < ks.length - max; i++) await c.delete(ks[i]);
}
self.addEventListener("fetch", ev => {
  const req = ev.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (/\/(go|ir)\//.test(url.pathname) || url.pathname.endsWith(".ics")) return;
  if (req.mode === "navigate"){
    ev.respondWith(fetch(req).then(r => {
      if (r.ok && r.type === "basic"){
        const copia = r.clone();
        caches.open(PAGINAS).then(c => c.put(req, copia)).then(() => limitar(PAGINAS, 40));
      }
      return r;
    }).catch(() => caches.match(req).then(r => r || caches.match(OFFLINE))));
    return;
  }
  if (url.pathname.includes("/assets/") && !/\.(mp4|webm|mp3|m4a)$/.test(url.pathname)){
    ev.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => {
      if (r.ok && r.type === "basic"){
        const copia = r.clone();
        caches.open(ARQUIVOS).then(c => c.put(req, copia)).then(() => limitar(ARQUIVOS, 120));
      }
      return r;
    })));
  }
});
