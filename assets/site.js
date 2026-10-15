/* MyTickets Tours: painel split-flap, parallax, vídeo guiado pelo scroll, cursor líquido e botões ímã. */
(function(){
"use strict";
const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;
const B = document.body.dataset;            // textos por idioma vindos do HTML
const VIDEO_SRC = B.video || "";            // opcional: MP4 vertical que passa a ser rolado no lugar da animação

/* ---------- Painel (split-flap) ---------- */
const CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
const active = new Set();
let ticker = null;
function setTile(t, ch){ t.textContent = ch === " " ? " " : ch; t.classList.toggle("blank", ch === " "); }
function build(el){
  const text = (el.dataset.flap || el.textContent).toUpperCase();
  const n = Math.max(+el.dataset.w || 0, text.length);
  el.dataset.flap = text;
  el.textContent = "";
  const target = text.padEnd(n, " ");
  for (let i = 0; i < n; i++){ const s = document.createElement("span"); s.className = "tile"; setTile(s, target[i]); el.appendChild(s); }
}
function flap(el){
  if (REDUCED) return;
  const target = el.dataset.flap.padEnd(el.children.length, " ");
  [...el.children].forEach((t, i) => {
    t._target = target[i]; t._left = 2 + Math.floor(Math.random() * 4) + Math.floor(i * .6); t._wait = Math.floor(i * .5);
    active.add(t);
  });
  if (!ticker) ticker = setInterval(tick, 55);
}
function tick(){
  active.forEach(t => {
    if (t._wait > 0){ t._wait--; return; }
    t.classList.remove("flip"); void t.offsetWidth; t.classList.add("flip");
    if (t._left-- > 0) setTile(t, CHARS[Math.floor(Math.random() * CHARS.length)]);
    else { setTile(t, t._target); active.delete(t); }
  });
  if (!active.size){ clearInterval(ticker); ticker = null; }
}
function scramble(el){
  if (REDUCED) return;
  const text = el.dataset.text || (el.dataset.text = el.textContent);
  let f = 0; const total = 18;
  const run = () => {
    const done = Math.floor(text.length * f / total);
    el.textContent = text.split("").map((c, i) => i < done || c === " " ? c : CHARS[Math.floor(Math.random() * CHARS.length)]).join("");
    if (++f <= total) setTimeout(run, 40); else el.textContent = text;
  };
  run();
}
const flaps = [...document.querySelectorAll("[data-flap]")];
flaps.forEach(build);
const board = document.getElementById("board");
if ("IntersectionObserver" in window){
  const seen = new WeakSet();
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting || seen.has(e.target)) return;
    seen.add(e.target);
    if (e.target === board) board.querySelectorAll("[data-flap]").forEach(flap);
    else if (e.target.dataset.flap) flap(e.target);
    else scramble(e.target);
  }), { threshold: .3 });
  if (board) io.observe(board);
  flaps.filter(el => !board || !board.contains(el)).forEach(el => io.observe(el));
  document.querySelectorAll("[data-scramble]").forEach(el => io.observe(el));
}

/* Relógio do painel */
const clockEl = document.getElementById("clock");
if (clockEl){
  const clock = () => { const d = new Date(); clockEl.textContent = String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0"); };
  clock(); setInterval(clock, 15000);
}

/* ---------- Notícias do robô (dados.json): um bloco por país, na ordem do ranking ---------- */
const news = document.getElementById("news");
if (news){
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const lang = news.dataset.lang || "pt", hot = news.dataset.hot || "";
  fetch((news.dataset.src || "dados.json") + "?t=" + Date.now()).then(r => r.ok ? r.json() : null).then(j => {
    if (!j || !Array.isArray(j.paises) || !j.paises.length) return;
    news.innerHTML = j.paises.map(p => `<article class="country"><h3><span class="cc">${esc(p.pais)}</span> ${esc((p.nome && p.nome[lang]) || p.pais)}</h3><ul>${
      p.noticias.map(n => `<li><a href="${esc(n.u)}" target="_blank" rel="noopener">${esc(n.t)}<small>${esc(n.f)}${n.alta ? " · " + esc(hot) : ""}</small></a></li>`).join("")}</ul></article>`).join("");
  }).catch(() => {});
}

/* ---------- Medição (dataLayer → GTM ou GA4; só envia algo ao Google se o visitante aceitar cookies) ---------- */
window.dataLayer = window.dataLayer || [];
function track(o){ try { window.dataLayer.push(o); } catch (e) {} }
function gtagSafe(){ if (typeof window.gtag === "function") window.gtag.apply(null, arguments); }

/* Tipo do link do parceiro a partir do caminho: /event/123, /dock/competition/x, /dock/team/x ...
   Links protegidos do próprio site (/ir/123/) contam como link de evento. */
function partnerLink(a){
  let u; try { u = new URL(a.href); } catch (e) { return null; }
  const ir = u.host === location.host && u.pathname.match(/\/ir\/(\d+)\/?$/);
  if (ir) return { type: "event", id: ir[1], path: u.pathname, url: u, cloaked: true };
  if (!/sportsevents365\.com$/.test(u.hostname)) return null;
  const p = u.pathname, m = p.match(/^\/event\/(\d+)/);
  const type = m ? "event" : /\/dock\/competition\//.test(p) ? "competition" : /\/dock\/team\//.test(p) ? "team"
    : /\/dock\/cities\//.test(p) ? "city" : /\/dock\/music\//.test(p) ? "artist" : /\/concerts/.test(p) ? "sport" : "home";
  return { type, id: m ? m[1] : "", path: p, url: u, cloaked: false };
}
/* SubID do painel de afiliado: data1 = onde foi o clique, data2 = em qual página (aparecem no relatório de comissões). */
function subId(){
  const pg = location.pathname.replace(/^\/|\/$/g, "").replace(/\//g, "_") || "home";
  return pg.slice(0, 90);
}
document.addEventListener("click", ev => {
  const a = ev.target.closest && ev.target.closest("a[href]");
  if (!a) return;
  const l = partnerLink(a);
  if (!l) return;
  const where = a.closest("#partidas") ? "board" : a.closest(".ev-hero .ev-cta") ? "event_cta_top" : a.closest(".ev-cta") ? "event_cta"
    : a.closest(".ev-hero") ? "event_facts" : a.closest("#explorar") ? "explore" : a.closest(".top") ? "header" : a.closest(".foot") ? "footer"
    : a.closest("#banner3d") ? "banner" : a.closest(".hero") ? "hero" : a.closest(".tips") ? "event_also" : "content";
  // Escreve o SubID no próprio link antes de o navegador seguir (o evento roda na fase de captura).
  const u = l.url;
  if (l.cloaked){ u.searchParams.set("d1", where); u.searchParams.set("d2", subId()); }
  else { u.searchParams.set("data1", where); u.searchParams.set("data2", subId()); }
  a.href = u.toString();
  // Conversão principal do site afiliado: marque "affiliate_click" como evento-chave no GA4 e importe no Google Ads.
  track({ event: "affiliate_click", link_type: l.type, link_url: a.href, partner_event_id: l.id, click_location: where });
  if (l.type === "event"){
    const it = (window.MT_ITEM && window.MT_ITEM.item_id === l.id) ? window.MT_ITEM
      : { item_id: l.id, item_name: (a.getAttribute("aria-label") || a.textContent || "").replace(/^[^:]*:\s*/, "").trim(), item_brand: "SportsEvents365" };
    track({ ecommerce: null });
    track({ event: "begin_checkout", click_location: where, ecommerce: { items: [it] } });
  }
}, true);

/* Banner de cookies (Consent Mode v2). Só existe quando o GTM ou o GA4 está configurado no gerador. */
const bar = document.getElementById("cookie-bar");
if (bar){
  let saved = null;
  try { saved = localStorage.getItem("mt_consent"); } catch (e) {}
  if (!saved) bar.hidden = false;
  bar.addEventListener("click", ev => {
    const b = ev.target.closest("[data-consent]");
    if (!b) return;
    const v = b.dataset.consent === "granted" ? "granted" : "denied";
    try { localStorage.setItem("mt_consent", v); } catch (e) {}
    gtagSafe("consent", "update", { ad_storage: v, ad_user_data: v, ad_personalization: v, analytics_storage: v });
    track({ event: "consent_" + v });
    bar.hidden = true;
  });
}

/* Botão "Voltar": volta à página anterior quando ela é deste site; se o visitante chegou de fora
   (Google, rede social, link direto), o link leva à página inicial, que é o href do botão. */
document.querySelectorAll("[data-back]").forEach(a => {
  let interno = false;
  try { interno = !!document.referrer && new URL(document.referrer).host === location.host; } catch (e) {}
  if (!interno) return;
  a.addEventListener("click", ev => { ev.preventDefault(); history.back(); });
});

/* ---------- Formulário de alertas (FormSubmit → caixa de e-mail do Titan) ---------- */
const form = document.getElementById("alert-form");
if (form){
  form.addEventListener("submit", e => {
    e.preventDefault();
    const m = document.getElementById("form-msg"), em = document.getElementById("a-email").value.trim(), ok = document.getElementById("a-consent").checked;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em) || !ok){ m.className = "form-msg err"; m.textContent = form.dataset.err; return; }
    const url = form.dataset.endpoint;
    if (!url){ m.className = "form-msg"; m.textContent = form.dataset.soon; return; }
    if (document.getElementById("a-honey").value) return;
    const sel = document.getElementById("a-event"), btn = form.querySelector("button[type=submit]");
    btn.disabled = true; m.className = "form-msg"; m.textContent = form.dataset.sending;
    fetch(url, { method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, body: JSON.stringify({
      email: em, evento: sel.options[sel.selectedIndex].text, evento_slug: sel.value,
      idioma_alertas: document.getElementById("a-lang").value, pagina: location.href, consentimento: "sim",
      _subject: "Alerta de venda: " + sel.options[sel.selectedIndex].text, _template: "table", _captcha: "false"
    }) }).then(r => r.ok ? r.json() : Promise.reject()).then(j => {
      if (j && (j.success === true || j.success === "true")){
        m.className = "form-msg ok"; m.textContent = form.dataset.done;
        track({ event: "generate_lead", lead_type: "sale_alert", event_slug: sel.value, alert_language: document.getElementById("a-lang").value });
        form.reset();
      }
      else return Promise.reject();
    }).catch(() => { m.className = "form-msg err"; m.textContent = form.dataset.fail; }).finally(() => { btn.disabled = false; });
  });
}

/* ---------- Parallax (scroll + mouse) ---------- */
const hero = document.querySelector("[data-parallax]");
const layers = hero ? [...hero.querySelectorAll("[data-depth]")] : [];
let mx = 0, my = 0, tmx = 0, tmy = 0, heroVisible = !!hero;
layers.forEach(l => { const r = l.dataset.rot; if (r) l.style.transform = `rotate(${r}deg)`; });
if (hero){
  if ("IntersectionObserver" in window) new IntersectionObserver(es => { heroVisible = es[0].isIntersecting; }).observe(hero);
  hero.addEventListener("pointermove", e => { const r = hero.getBoundingClientRect(); tmx = (e.clientX - r.left) / r.width - .5; tmy = (e.clientY - r.top) / r.height - .5; });
  hero.addEventListener("pointerleave", () => { tmx = 0; tmy = 0; });
}
function parallax(){
  if (!heroVisible || REDUCED) return;
  mx += (tmx - mx) * .08; my += (tmy - my) * .08;
  const sy = Math.min(window.scrollY, hero.offsetHeight);
  layers.forEach(l => {
    const d = parseFloat(l.dataset.depth), rot = l.dataset.rot || 0;
    l.style.transform = `translate3d(${(-mx * 30 * d).toFixed(1)}px,${(sy * d * .35 - my * 24 * d).toFixed(1)}px,0) rotate(${rot}deg)`;
  });
}

/* ---------- Vídeo guiado pelo scroll ---------- */
const sv = document.getElementById("video");
let draw = () => {}, updateVideo = () => {};
if (sv){
  const cv = document.getElementById("sv-canvas"), cx = cv.getContext("2d"), prog = document.getElementById("reel-prog");
  const steps = [...sv.querySelectorAll(".step")];
  let W = 0, H = 0, P = -1, scene = null, videoEl = null;
  const rng = seed => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const smooth = (a, b, v) => { const t = clamp((v - a) / (b - a)); return t * t * (3 - 2 * t); };
  const size = () => {
    const r = cv.getBoundingClientRect(), d = Math.min(window.devicePixelRatio || 1, 2);
    W = r.width; H = r.height; if (!W || !H) return;
    cv.width = Math.round(W * d); cv.height = Math.round(H * d); cx.setTransform(d, 0, 0, d, 0, 0);
    const R = rng(7), b = []; let x = -.25;
    while (x < 1.25){
      const w = .03 + R() * .05, center = Math.abs(x + w / 2 - .5) < .2, h = center ? .02 + R() * .04 : .06 + R() * .2;
      const win = []; for (let i = 0; i < 14; i++) win.push([R(), R(), R() < .45]);
      b.push({ x, w, h, win }); x += w + .004;
    }
    const stars = []; for (let i = 0; i < 90; i++) stars.push([R(), R() * .55, R() * 1.2 + .3]);
    const crowd = []; for (let i = 0; i < 520; i++) crowd.push([R(), R(), ["#E8ECF2", "#2B59C3", "#A50044", "#FFC400", "#E8ECF2"][Math.floor(R() * 5)]]);
    scene = { b, stars, crowd };
    draw(Math.max(P, 0));
  };
  const drawCity = p => {
    const hz = H * .66, scx = W * .5, scy = hz - H * .01, z = 1 + smooth(.16, .7, p) * 4.6, lights = smooth(.4, .5, p);
    const g = cx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, "#03070E"); g.addColorStop(.62, "#13264A"); g.addColorStop(1, "#1D3557");
    cx.fillStyle = g; cx.fillRect(0, 0, W, H);
    cx.fillStyle = "#fff";
    scene.stars.forEach(([x, y, s]) => { cx.globalAlpha = (1 - smooth(.1, .4, p)) * .8; cx.fillRect(x * W, y * H, s, s); }); cx.globalAlpha = 1;
    if (lights > 0){ const rg = cx.createRadialGradient(scx, scy, 0, scx, scy, W * .9); rg.addColorStop(0, `rgba(255,214,120,${.45 * lights})`); rg.addColorStop(1, "rgba(255,214,120,0)"); cx.fillStyle = rg; cx.fillRect(0, 0, W, H); }
    if (p < .42){
      const t = p / .42, px = -.1 * W + t * 1.2 * W, py = H * .2 - t * H * .06;
      cx.strokeStyle = "rgba(255,255,255,.25)"; cx.lineWidth = 1; cx.beginPath(); cx.moveTo(px - W * .25, py + H * .012); cx.lineTo(px, py); cx.stroke();
      cx.fillStyle = Math.floor(p * 90) % 2 ? "#FF4D4D" : "#fff"; cx.beginPath(); cx.arc(px, py, 2.2, 0, 7); cx.fill();
    }
    cx.save(); cx.translate(scx, scy); cx.scale(z, z); cx.translate(-scx, -scy);
    cx.fillStyle = "#08101D"; cx.fillRect(-W, hz, W * 3, H * 2);
    scene.b.forEach(o => {
      const x = o.x * W, w = o.w * W, h = o.h * H; cx.fillStyle = "#0C1729"; cx.fillRect(x, hz - h, w, h);
      o.win.forEach(([a, b, on]) => { if (on){ cx.fillStyle = "rgba(255,214,140,.7)"; cx.fillRect(x + a * (w - 3), hz - h + b * (h - 4) + 2, 1.6, 1.6); } });
    });
    const bw = W * .17, bh = H * .03;
    cx.fillStyle = "#17263C"; cx.fillRect(scx - bw, scy, bw * 2, H * .035);
    cx.beginPath(); cx.ellipse(scx, scy, bw, bh, 0, 0, 7); cx.fillStyle = "#1C2E48"; cx.fill();
    cx.beginPath(); cx.ellipse(scx, scy, bw * .62, bh * .55, 0, 0, 7); cx.fillStyle = `rgba(34,120,64,${.25 + lights * .75})`; cx.fill();
    cx.strokeStyle = `rgba(255,196,0,${.2 + lights * .6})`; cx.lineWidth = 1.2 / z; cx.beginPath(); cx.ellipse(scx, scy, bw, bh, 0, 0, 7); cx.stroke();
    [-1.05, -.72, .72, 1.05].forEach(k => {
      const tx = scx + k * bw, top = scy - H * .11;
      cx.strokeStyle = "#2A3B55"; cx.lineWidth = 2 / z; cx.beginPath(); cx.moveTo(tx, scy + H * .03); cx.lineTo(tx, top); cx.stroke();
      cx.fillStyle = lights > 0 ? `rgba(255,248,220,${.35 + lights * .65})` : "#2A3B55"; cx.fillRect(tx - W * .012, top - H * .008, W * .024, H * .01);
      if (lights > 0){
        cx.save(); cx.globalCompositeOperation = "lighter";
        const bg = cx.createLinearGradient(tx, top, scx, scy); bg.addColorStop(0, `rgba(255,240,200,${.28 * lights})`); bg.addColorStop(1, "rgba(255,240,200,0)");
        cx.fillStyle = bg; cx.beginPath(); cx.moveTo(tx - W * .01, top); cx.lineTo(tx + W * .01, top); cx.lineTo(scx + bw * .4, scy); cx.lineTo(scx - bw * .4, scy); cx.closePath(); cx.fill(); cx.restore();
      }
    });
    cx.restore();
  };
  const drawInside = p => {
    cx.fillStyle = "#07101C"; cx.fillRect(0, 0, W, H);
    const flashSeed = Math.floor(p * 400);
    scene.crowd.forEach(([x, row, c], i) => {
      const y = H * (.1 + row * .32), spread = 1 - row * .25, xx = W * (.5 + (x - .5) * (1.05 + spread * .2));
      const flash = ((i * 7919 + flashSeed) % 113) === 0;
      cx.fillStyle = flash ? "#FFFFFF" : c; cx.globalAlpha = flash ? 1 : .55 + row * .3; cx.fillRect(xx, y, 2.2, 2.2);
    }); cx.globalAlpha = 1;
    const top = H * .46, bot = H * 1.02, tl = W * .24, tr = W * .76;
    for (let i = 0; i < 8; i++){
      const a = i / 8, b = (i + 1) / 8, y1 = top + (bot - top) * a, y2 = top + (bot - top) * b;
      const l1 = tl + (-W * .1 - tl) * a, r1 = tr + (W * 1.1 - tr) * a, l2 = tl + (-W * .1 - tl) * b, r2 = tr + (W * 1.1 - tr) * b;
      cx.fillStyle = i % 2 ? "#1F7440" : "#23823F"; cx.beginPath(); cx.moveTo(l1, y1); cx.lineTo(r1, y1); cx.lineTo(r2, y2); cx.lineTo(l2, y2); cx.closePath(); cx.fill();
    }
    cx.strokeStyle = "rgba(255,255,255,.75)"; cx.lineWidth = 1.5; cx.beginPath(); cx.moveTo(tl, top); cx.lineTo(tr, top); cx.stroke();
    const my2 = top + (bot - top) * .42, ml = tl + (-W * .1 - tl) * .42, mr = tr + (W * 1.1 - tr) * .42;
    cx.beginPath(); cx.moveTo(ml, my2); cx.lineTo(mr, my2); cx.stroke(); cx.beginPath(); cx.ellipse(W * .5, my2, W * .16, H * .035, 0, 0, 7); cx.stroke();
    [[0, 0], [W, 0]].forEach(([x, y]) => { const rg = cx.createRadialGradient(x, y, 0, x, y, W * .7); rg.addColorStop(0, "rgba(255,244,210,.55)"); rg.addColorStop(1, "rgba(255,244,210,0)"); cx.fillStyle = rg; cx.fillRect(0, 0, W, H); });
    const sw = W * .72, sh = H * .065, sx = (W - sw) / 2, syy = H * .045;
    cx.fillStyle = "#04070B"; cx.fillRect(sx, syy, sw, sh); cx.strokeStyle = "rgba(255,196,0,.5)"; cx.lineWidth = 1; cx.strokeRect(sx + .5, syy + .5, sw - 1, sh - 1);
    cx.fillStyle = "#FFC400"; cx.font = `700 ${Math.round(sh * .42)}px "JetBrains Mono", monospace`; cx.textAlign = "center"; cx.textBaseline = "middle";
    cx.fillText(`MYTICKETS · ${B.gate || "GATE"} 7`, W / 2, syy + sh / 2);
  };
  const drawTicket = k => {
    const w = W * .8, h = H * .27, x = (W - w) / 2, y = H - k * (H * .64);
    cx.save(); cx.shadowColor = "rgba(0,0,0,.5)"; cx.shadowBlur = 24; cx.fillStyle = "#FFFFFF";
    cx.beginPath(); if (cx.roundRect) cx.roundRect(x, y, w, h, 12); else cx.rect(x, y, w, h); cx.fill(); cx.restore();
    cx.fillStyle = "#FFC400"; cx.fillRect(x, y, w, h * .24);
    cx.fillStyle = "#1B1500"; cx.font = `700 ${Math.round(h * .1)}px "JetBrains Mono", monospace`; cx.textAlign = "left"; cx.textBaseline = "middle"; cx.fillText(B.admit || "ADMIT · 1", x + w * .06, y + h * .12);
    cx.fillStyle = "#0F2236"; cx.font = `800 ${Math.round(h * .16)}px "Big Shoulders Display", sans-serif`; cx.fillText(B.ticket || "", x + w * .06, y + h * .42);
    cx.fillStyle = "#52637A"; cx.font = `600 ${Math.round(h * .09)}px Barlow, sans-serif`; cx.fillText(B.venue || "", x + w * .06, y + h * .6);
    for (let i = 0; i < 34; i++){ if (i % 3 === 1) continue; cx.fillStyle = "#0F2236"; cx.fillRect(x + w * .06 + i * (w * .022), y + h * .72, i % 4 ? w * .008 : w * .014, h * .18); }
    cx.fillStyle = "#04080F"; [x, x + w].forEach(c => { cx.beginPath(); cx.arc(c, y + h * .24, h * .07, 0, 7); cx.fill(); });
  };
  draw = p => {
    if (!scene || !W) return;
    cx.clearRect(0, 0, W, H);
    const inside = smooth(.64, .78, p);
    if (inside < 1) drawCity(p);
    if (inside > 0){ cx.globalAlpha = inside; drawInside(p); cx.globalAlpha = 1; }
    const tk = smooth(.84, .97, p); if (tk > 0) drawTicket(tk);
    const vg = cx.createRadialGradient(W / 2, H / 2, H * .3, W / 2, H / 2, H * .75); vg.addColorStop(0, "rgba(0,0,0,0)"); vg.addColorStop(1, "rgba(0,0,0,.45)"); cx.fillStyle = vg; cx.fillRect(0, 0, W, H);
  };
  const progress = () => { const r = sv.getBoundingClientRect(), total = r.height - innerHeight; return clamp(-r.top / (total || 1)); };
  updateVideo = () => {
    const p = progress(); if (Math.abs(p - P) < .0005) return; P = p;
    prog.style.width = (p * 100).toFixed(1) + "%";
    const s = p < .36 ? 0 : p < .72 ? 1 : 2; steps.forEach((el, i) => el.classList.toggle("on", i === s));
    if (videoEl && videoEl.duration) videoEl.currentTime = p * videoEl.duration; else draw(p);
  };
  if (VIDEO_SRC){
    videoEl = document.createElement("video"); videoEl.src = VIDEO_SRC; videoEl.muted = true; videoEl.playsInline = true; videoEl.preload = "auto";
    videoEl.addEventListener("loadedmetadata", () => { cv.hidden = true; P = -1; updateVideo(); });
    document.getElementById("screen").prepend(videoEl);
  }
  window.addEventListener("resize", () => { size(); P = -1; updateVideo(); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => draw(Math.max(P, 0)));
  size();
}

/* ---------- Cursor líquido + botões ímã ---------- */
const fine = matchMedia("(pointer: fine)").matches && !REDUCED;
const blob = document.getElementById("cur-blob"), dot = document.getElementById("cur-dot");
let cxp = -100, cyp = -100, bx = -100, by = -100, vx = 0, vy = 0;
if (fine && blob){
  document.documentElement.classList.add("has-cursor");
  window.addEventListener("pointermove", e => {
    cxp = e.clientX; cyp = e.clientY;
    const t = e.target, native = t.closest && t.closest("input,select,#banner3d");
    blob.classList.toggle("off", !!native); dot.classList.toggle("off", !!native);
  });
  document.addEventListener("pointerleave", () => { blob.classList.add("off"); dot.classList.add("off"); });
  document.querySelectorAll("[data-magnetic]").forEach(el => {
    const inner = el.querySelector(".mag-inner");
    el.addEventListener("pointerenter", () => blob.classList.add("big"));
    el.addEventListener("pointermove", e => {
      const r = el.getBoundingClientRect(), dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
      el.style.transform = `translate(${(dx * .3).toFixed(1)}px,${(dy * .4).toFixed(1)}px)`;
      if (inner) inner.style.transform = `translate(${(dx * .14).toFixed(1)}px,${(dy * .18).toFixed(1)}px)`;
    });
    el.addEventListener("pointerleave", () => { el.style.transform = ""; if (inner) inner.style.transform = ""; blob.classList.remove("big"); });
  });
}
function cursorLoop(){
  if (!fine || !blob) return;
  const ax = (cxp - bx) * .16, ay = (cyp - by) * .16; vx = vx * .55 + ax; vy = vy * .55 + ay; bx += vx; by += vy;
  const sp = Math.min(Math.hypot(vx, vy) / 26, .55), ang = Math.atan2(vy, vx) * 180 / Math.PI;
  blob.style.transform = `translate3d(${bx.toFixed(1)}px,${by.toFixed(1)}px,0) rotate(${ang.toFixed(1)}deg) scale(${(1 + sp).toFixed(3)},${(1 - sp * .45).toFixed(3)})`;
  dot.style.transform = `translate3d(${cxp}px,${cyp}px,0)`;
}

/* ---------- Laço único de animação ---------- */
function loop(){ parallax(); updateVideo(); cursorLoop(); requestAnimationFrame(loop); }
document.querySelectorAll(".hero [data-flap]").forEach(flap);
requestAnimationFrame(loop);
})();
