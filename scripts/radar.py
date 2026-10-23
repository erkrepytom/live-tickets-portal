#!/usr/bin/env python3
"""Radar de menções: procura na internet quem está perguntando sobre os eventos do site e monta
uma fila de respostas para uma pessoa escrever à mão.

O que ele FAZ: lê posts públicos, pontua a intenção de compra, junta tudo em radar/fila.md com um
rascunho de resposta em cada caso, citando o nome do site (MyTickets Tours) e o WhatsApp.

O que ele NÃO FAZ, de propósito: publicar. Resposta automática em fórum é spam, derruba a conta e
mancha a marca justamente onde ela promete confiança. A fila existe para você responder quem de fato
perguntou, uma a uma, dizendo que o site é seu.

Fontes de agora: Reddit e Bluesky (públicas, sem chave). YouTube, Bright Data e fóruns entram depois.
Uso: python scripts/radar.py [--dias 30]
"""
import datetime
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Mozilla/5.0 (compatible; MyTicketsToursRadar/1.0; +https://mytickets.tours/)"
SITE = "MyTickets Tours"
WHATSAPP = os.environ.get("WHATSAPP_CONTATO", "").strip()
DIAS = 30
LIMITE_FILA = 40

# Palavras que separam "quem está comprando" de "quem está só comentando o jogo".
INTENCAO = {
    "pt": {"ingresso": 3, "ingressos": 3, "comprar": 3, "onde compro": 4, "revenda": 2, "cambista": 2,
           "golpe": 3, "confiável": 2, "confiavel": 2, "viajar": 1, "hospedagem": 1, "quanto custa": 3,
           "vale a pena": 1, "setor": 1, "como faço": 2},
    "en": {"ticket": 3, "tickets": 3, "buy": 3, "where to buy": 4, "resale": 2, "scam": 3, "legit": 2,
           "trip": 1, "hotel": 1, "how much": 3, "worth it": 1, "seats": 1, "away section": 2},
    "es": {"entrada": 3, "entradas": 3, "comprar": 3, "dónde compro": 4, "donde compro": 4, "reventa": 2,
           "estafa": 3, "fiable": 2, "viajar": 1, "cuánto cuesta": 3, "cuanto cuesta": 3, "vale la pena": 1},
}
RUIDO = ("free stream", "streaming grátis", "assistir de graça", "crackstream", "apostas", "bet365",
         "aposta", "odds", "palpite")


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", s)).strip()


def baixar(url, cabecalhos=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json", **(cabecalhos or {})})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def nomes_do_evento(ev):
    """Como as pessoas chamam o evento na internet: times, artista, competição e cidade."""
    nomes = []
    for tm in ev.get("times", []):
        n = tm["nome"] if isinstance(tm["nome"], str) else tm["nome"].get("en", "")
        if n:
            nomes.append(n)
    if ev.get("artista"):
        nomes.append(ev["artista"]["nome"])
    comp = ev.get("competicao", {}).get("nome")
    if comp:
        nomes.append(comp if isinstance(comp, str) else comp.get("en", ""))
    return [n for n in nomes if len(n) > 2]


def consultas(ev):
    """Buscas por evento: o confronto, e cada nome com palavra de ingresso."""
    nomes = nomes_do_evento(ev)
    qs = []
    if len(nomes) >= 2:
        qs.append(f"{nomes[0]} {nomes[1]} tickets")
        qs.append(f"{nomes[0]} {nomes[1]} ingressos")
    for n in nomes[:2]:
        qs.append(f"{n} tickets how to buy")
        qs.append(f"{n} entradas comprar")
    cidade = ev.get("cidade", {}).get("en") or ""
    if cidade:
        qs.append(f"{cidade} {ev.get('tipo','')} tickets travel")
    return list(dict.fromkeys(q.strip() for q in qs if q.strip()))[:5]


def nota_intencao(texto):
    t = " " + norm(texto) + " "
    if any(r in t for r in (norm(x) for x in RUIDO)):
        return 0
    n = 0
    for idioma in INTENCAO.values():
        for palavra, peso in idioma.items():
            if norm(palavra) in t:
                n += peso
    return n


def fala_do_evento(texto, ev):
    t = " " + norm(texto) + " "
    nomes = [norm(n) for n in nomes_do_evento(ev)]
    return sum(1 for n in nomes if n and f" {n} " in t)


def idioma_do_texto(texto):
    t = norm(texto)
    pt = sum(1 for w in ("ingresso", "comprar", "como", "voce", "nao", "para") if f" {w} " in f" {t} ")
    es = sum(1 for w in ("entradas", "donde", "como", "para", "partido") if f" {w} " in f" {t} ")
    return "pt" if pt > es and pt else ("es" if es else "en")


# ---------------- Fontes ----------------

def do_reddit(consulta, desde):
    url = ("https://www.reddit.com/search.json?" +
           urllib.parse.urlencode({"q": consulta, "sort": "new", "t": "month", "limit": 25, "raw_json": 1}))
    dados = baixar(url)
    achados = []
    for filho in dados.get("data", {}).get("children", []):
        d = filho.get("data", {})
        quando = datetime.datetime.fromtimestamp(d.get("created_utc", 0), datetime.timezone.utc)
        if quando < desde:
            continue
        achados.append({
            "fonte": "Reddit", "onde": "r/" + d.get("subreddit", ""), "autor": d.get("author", ""),
            "titulo": html.unescape(d.get("title", ""))[:200],
            "texto": html.unescape(d.get("selftext", ""))[:600],
            "url": "https://www.reddit.com" + d.get("permalink", ""),
            "quando": quando.date().isoformat(),
        })
    return achados


def do_bluesky(consulta, desde):
    url = ("https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?" +
           urllib.parse.urlencode({"q": consulta, "limit": 25, "sort": "latest"}))
    dados = baixar(url)
    achados = []
    for post in dados.get("posts", []):
        rec = post.get("record", {}) or {}
        criado = (rec.get("createdAt") or "")[:19]
        try:
            quando = datetime.datetime.fromisoformat(criado).replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            continue
        if quando < desde:
            continue
        autor = post.get("author", {}) or {}
        handle = autor.get("handle", "")
        rkey = (post.get("uri", "") or "").rsplit("/", 1)[-1]
        achados.append({
            "fonte": "Bluesky", "onde": "bsky.app", "autor": handle,
            "titulo": (rec.get("text", "") or "")[:140],
            "texto": (rec.get("text", "") or "")[:600],
            "url": f"https://bsky.app/profile/{handle}/post/{rkey}" if handle and rkey else "",
            "quando": quando.date().isoformat(),
        })
    return achados


FONTES = (("Reddit", do_reddit), ("Bluesky", do_bluesky))


# ---------------- Rascunhos ----------------

RASCUNHO = {
    "pt": ("Oi! Eu cuido do {site}, um guia de ingressos para {evento}. Lá tem o passo a passo de compra, "
           "o que muda para quem vem de fora e o aviso de quais vendas são confiáveis. "
           "Se preferir falar com uma pessoa, meu WhatsApp é {zap}. "
           "Aviso: o site ganha comissão quando alguém compra pelo parceiro."),
    "en": ("Hi! I run {site}, a ticket guide for {evento}. It walks through how the purchase works, what "
           "changes when you're travelling in, and how to tell a safe seller from a scam. "
           "Happy to answer on WhatsApp too: {zap}. "
           "Disclosure: the site earns a commission if you buy through the partner."),
    "es": ("¡Hola! Llevo {site}, una guía de entradas para {evento}. Explica el paso a paso de la compra, "
           "qué cambia si viajas desde fuera y cómo reconocer una venta segura. "
           "Si prefieres hablar con una persona, mi WhatsApp es {zap}. "
           "Aviso: el sitio gana comisión si compras por el socio."),
}


def rascunho(item, ev, lang):
    titulo = ev["titulo"].get(lang) or ev["titulo"].get("en", "")
    zap = WHATSAPP or "(coloque o número em WHATSAPP_CONTATO)"
    return RASCUNHO[lang].format(site=SITE, evento=titulo, zap=zap)


# ---------------- Fila ----------------

def montar_fila(itens, eventos):
    hoje = datetime.date.today().isoformat()
    por_evento = {}
    for it in itens:
        por_evento.setdefault(it["evento"], []).append(it)
    linhas = [f"# Radar de menções — {hoje}", "",
              f"{len(itens)} conversa(s) com cara de quem quer comprar, nos últimos {DIAS} dias.", "",
              "Como usar: responda **você**, uma a uma, no tom da conversa. O rascunho é ponto de partida, não",
              "texto pronto para colar em série — resposta repetida é spam, e spam derruba a conta e a marca.",
              "Cite o nome do site, não o link: quem se interessa procura, e link solto em fórum vira denúncia.",
              "Diga que o site é seu e que há comissão. Em comunidade com regra contra divulgação, não poste:",
              "responda no privado se a pessoa abrir espaço.", ""]
    if not WHATSAPP:
        linhas += ["> **Falta o WhatsApp.** Defina a variável `WHATSAPP_CONTATO` no repositório "
                   "(Settings → Secrets and variables → Actions → Variables) e os rascunhos saem com o número.", ""]
    for ev in eventos:
        lista = sorted(por_evento.get(ev["slug"], []), key=lambda x: -x["nota"])
        if not lista:
            continue
        linhas.append(f"## {ev['titulo'].get('pt', ev['slug'])} — {ev['data']}")
        linhas.append("")
        for it in lista:
            trecho = re.sub(r"\s+", " ", (it.get("titulo") or it.get("texto") or ""))[:160]
            linhas += [f"### {it['fonte']} · {it['onde']} · {it['quando']} · intenção {it['nota']}",
                       f"- **Quem:** {it['autor'] or '(sem nome)'}",
                       f"- **Sobre:** {trecho}",
                       f"- **Onde responder:** {it['url']}",
                       "",
                       "```",
                       it["rascunho"],
                       "```",
                       ""]
    return "\n".join(linhas) + "\n"


def main():
    if "--dias" in sys.argv:
        global DIAS
        DIAS = int(sys.argv[sys.argv.index("--dias") + 1])
    desde = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=DIAS)
    with open(os.path.join(RAIZ, "data", "eventos.json"), encoding="utf-8") as f:
        eventos = json.load(f)["eventos"]

    vistos, itens, falhas = set(), [], []
    for ev in eventos:
        for consulta in consultas(ev):
            for nome_fonte, fonte in FONTES:
                try:
                    achados = fonte(consulta, desde)
                except Exception as exc:
                    falhas.append(f"{nome_fonte} ({consulta[:40]}): {exc}")
                    time.sleep(1.0)
                    continue
                time.sleep(0.8)   # educação com quem serve de graça: uma consulta por vez, sem rajada
                for a in achados:
                    if not a["url"] or a["url"] in vistos:
                        continue
                    texto = f"{a['titulo']} {a['texto']}"
                    if fala_do_evento(texto, ev) < 1:
                        continue
                    nota = nota_intencao(texto)
                    if nota < 4:
                        continue
                    vistos.add(a["url"])
                    lang = idioma_do_texto(texto)
                    a.update({"evento": ev["slug"], "nota": nota, "idioma": lang})
                    a["rascunho"] = rascunho(a, ev, lang)
                    itens.append(a)

    itens.sort(key=lambda x: (-x["nota"], x["quando"]), reverse=False)
    itens = sorted(itens, key=lambda x: -x["nota"])[:LIMITE_FILA]

    os.makedirs(os.path.join(RAIZ, "radar"), exist_ok=True)
    with open(os.path.join(RAIZ, "radar", "fila.md"), "w", encoding="utf-8") as f:
        f.write(montar_fila(itens, eventos))
    with open(os.path.join(RAIZ, "data", "mencoes.json"), "w", encoding="utf-8") as f:
        json.dump({"_leia": "Escrito por scripts/radar.py. Fila de conversas públicas sobre os eventos do site.",
                   "atualizado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                   "falhas": falhas, "itens": itens}, f, ensure_ascii=False, indent=1)
        f.write("\n")

    for linha in falhas[:6]:
        print(f"  ! {linha}")
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"::warning::radar: {linha}")
    msg = f"{len(itens)} conversa(s) na fila; {len(falhas)} falha(s) de fonte."
    print(msg)
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::notice::radar: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
