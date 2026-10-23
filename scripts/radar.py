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


def _contato():
    """data/contato.json guarda o que é público (WhatsApp, ID do mecanismo de busca);
    a variável de ambiente, quando existe, manda."""
    try:
        with open(os.path.join(RAIZ, "data", "contato.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


_CONTATO = _contato()
WHATSAPP = (os.environ.get("WHATSAPP_CONTATO") or _CONTATO.get("whatsapp", "")).strip()
DIAS = 30
LIMITE_FILA = 40
LIMITE_GOOGLE = 60   # a cota grátis da busca do Google é de 100 consultas por dia; sobra folga para um teste à mão

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
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        # o motivo vem no corpo da resposta; sem ele, "403" não diz nada e o conserto vira adivinhação
        try:
            corpo = exc.read().decode("utf-8", "replace")
            motivo = (json.loads(corpo).get("error", {}).get("message", "") or corpo)[:200]
        except Exception:
            motivo = ""
        raise RuntimeError(f"HTTP {exc.code}: {motivo or exc.reason}") from None


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


# Onde mora conversa de gente de verdade. A busca vai atrás destes lugares em vez de página de loja.
LUGARES = ("reddit.com", "quora.com", "tripadvisor.com", "forum", "community")


def consultas(ev):
    """Buscas por evento. Metade procura a conversa (fórum, pergunta, comentário) e metade procura
    o rastro na busca, com o site: dos lugares onde as pessoas conversam."""
    nomes = nomes_do_evento(ev)
    dupla = f"{nomes[0]} {nomes[1]}" if len(nomes) >= 2 else (nomes[0] if nomes else "")
    cidade = ev.get("cidade", {}).get("en") or ""
    qs = []
    if dupla:
        qs += [f"{dupla} tickets", f"{dupla} ingressos",
               f'site:reddit.com {dupla} tickets', f'"{dupla}" entradas comprar foro']
    for n in nomes[:2]:
        qs += [f"{n} tickets how to buy", f'site:quora.com {n} tickets']
    if cidade:
        qs.append(f"{cidade} {ev.get('tipo','')} tickets travel forum")
    return list(dict.fromkeys(q.strip() for q in qs if q.strip()))[:7]


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


# --- Reddit pela API oficial (app grátis do tipo "script"): os endpoints públicos .json respondem
# 403 para servidor, então a varredura automática precisa do app. Sem as chaves, cai no público. ---
_TOKEN = {}


def _token_reddit():
    cid, seg = os.environ.get("REDDIT_ID", ""), os.environ.get("REDDIT_SECRET", "")
    if not (cid and seg):
        return ""
    if _TOKEN.get("valor") and _TOKEN.get("ate", 0) > datetime.datetime.now().timestamp():
        return _TOKEN["valor"]
    import base64
    cab = {"Authorization": "Basic " + base64.b64encode(f"{cid}:{seg}".encode()).decode(),
           "User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"}
    req = urllib.request.Request("https://www.reddit.com/api/v1/access_token",
                                 data=b"grant_type=client_credentials", headers=cab)
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.loads(r.read().decode())
    _TOKEN["valor"] = d.get("access_token", "")
    _TOKEN["ate"] = datetime.datetime.now().timestamp() + int(d.get("expires_in", 3600)) - 60
    return _TOKEN["valor"]


def do_reddit_api(consulta, desde):
    tk = _token_reddit()
    if not tk:
        raise RuntimeError("sem REDDIT_ID/REDDIT_SECRET")
    url = ("https://oauth.reddit.com/search?" +
           urllib.parse.urlencode({"q": consulta, "sort": "new", "t": "month", "limit": 25, "raw_json": 1}))
    dados = baixar(url, {"Authorization": f"bearer {tk}"})
    achados = []
    for filho in dados.get("data", {}).get("children", []):
        d = filho.get("data", {})
        quando = datetime.datetime.fromtimestamp(d.get("created_utc", 0), datetime.timezone.utc)
        if quando < desde:
            continue
        achados.append({"fonte": "Reddit", "onde": "r/" + d.get("subreddit", ""), "autor": d.get("author", ""),
                        "titulo": html.unescape(d.get("title", ""))[:200],
                        "texto": html.unescape(d.get("selftext", ""))[:600],
                        "url": "https://www.reddit.com" + d.get("permalink", ""),
                        "quando": quando.date().isoformat()})
    return achados


def do_youtube(consulta, desde):
    """Comentários sob os vídeos do jogo: é onde o torcedor pergunta de ingresso sem rodeio."""
    chave = os.environ.get("YOUTUBE_API_KEY", "")
    if not chave:
        raise RuntimeError("sem YOUTUBE_API_KEY")
    busca = ("https://www.googleapis.com/youtube/v3/search?" + urllib.parse.urlencode(
        {"part": "snippet", "q": consulta, "type": "video", "maxResults": 3, "order": "relevance",
         "publishedAfter": desde.replace(microsecond=0).isoformat().replace("+00:00", "Z"), "key": chave}))
    videos = [i["id"]["videoId"] for i in baixar(busca).get("items", []) if i.get("id", {}).get("videoId")]
    achados = []
    for vid in videos:
        try:
            com = baixar("https://www.googleapis.com/youtube/v3/commentThreads?" + urllib.parse.urlencode(
                {"part": "snippet", "videoId": vid, "maxResults": 50, "order": "relevance",
                 "textFormat": "plainText", "key": chave}))
        except Exception:
            continue
        for it in com.get("items", []):
            t = it["snippet"]["topLevelComment"]["snippet"]
            try:
                quando = datetime.datetime.fromisoformat(t["publishedAt"].replace("Z", "+00:00"))
            except ValueError:
                continue
            if quando < desde:
                continue
            achados.append({"fonte": "YouTube", "onde": "comentários do vídeo", "autor": t.get("authorDisplayName", ""),
                            "titulo": (t.get("textDisplay", "") or "")[:140],
                            "texto": (t.get("textDisplay", "") or "")[:600],
                            "url": f"https://www.youtube.com/watch?v={vid}&lc={it.get('id','')}",
                            "quando": quando.date().isoformat()})
    return achados


def do_google(consulta, desde):
    """Os rastros que ficam na busca: o Google guarda o pedaço do comentário, do tópico de fórum e da
    pergunta mesmo quando a página inteira não abre. O trecho já é sinal; o resto você lê no link."""
    chave = os.environ.get("GOOGLE_CSE_KEY", "")
    cx = (os.environ.get("GOOGLE_CSE_CX") or _CONTATO.get("google_cse_cx", "")).strip()
    if not (chave and cx):
        raise RuntimeError("sem GOOGLE_CSE_KEY/GOOGLE_CSE_CX")
    meses = max(1, min(12, round(DIAS / 30) or 1))
    url = "https://www.googleapis.com/customsearch/v1?" + urllib.parse.urlencode(
        {"key": chave, "cx": cx, "q": consulta, "num": 10, "dateRestrict": f"m{meses}", "safe": "active"})
    dados = baixar(url)
    achados = []
    for it in dados.get("items", []):
        link = it.get("link", "")
        dominio = urllib.parse.urlparse(link).netloc.replace("www.", "")
        achados.append({"fonte": "Google", "onde": dominio, "autor": "",
                        "titulo": (it.get("title", "") or "")[:200],
                        "texto": (it.get("snippet", "") or "")[:600],
                        "url": link, "quando": datetime.date.today().isoformat(), "trecho": True})
    return achados


def fontes_ativas():
    """Usa o que há de chave no ambiente; sem chave nenhuma, tenta os endpoints públicos
    (que funcionam do seu computador, mas servidores levam 403)."""
    fs = []
    if os.environ.get("GOOGLE_CSE_KEY") and (os.environ.get("GOOGLE_CSE_CX") or _CONTATO.get("google_cse_cx")):
        fs.append(("Google", do_google))
    if os.environ.get("REDDIT_ID") and os.environ.get("REDDIT_SECRET"):
        fs.append(("Reddit", do_reddit_api))
    else:
        fs.append(("Reddit", do_reddit))
    if os.environ.get("YOUTUBE_API_KEY"):
        fs.append(("YouTube", do_youtube))
    fs.append(("Bluesky", do_bluesky))
    return tuple(fs)


FONTES = fontes_ativas()


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
    zap = f"+{WHATSAPP}" if WHATSAPP.isdigit() else (WHATSAPP or "(coloque o número em data/contato.json)")
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
              "responda no privado se a pessoa abrir espaço.",
              "",
              "O que esses sinais dizem em conjunto está em `radar/inteligencia.md`.", ""]
    if not WHATSAPP:
        linhas += ["> **Falta o WhatsApp.** Escreva o número em `data/contato.json` e os rascunhos saem com ele.", ""]
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



# ---------------- Inteligência: o que os sinais dizem, e o que fazer com isso ----------------

PARADAS = set("""a o as os um uma de do da dos das no na nos nas em para por com que e ou se ao aos
sem sobre como onde quando qual quais eu voce vocês ele ela isso esse essa este esta tem ter vai ir
the a an of for to in on at and or if is are was were be been this that these those with from how
what where when which who you your my it its el la los las un una de del y o si es son estar como
donde cuando cual quien por para con sin sobre mas más muito muy very just can get got nao não sim""".split())

# Cada padrão vira uma ação concreta quando aparece de verdade nos sinais. Nada de conselho genérico:
# a regra só entra no relatório com a contagem e um exemplo ao lado.
REGRAS = [
    (("golpe", "scam", "estafa", "fake", "falso", "fraude", "legit"),
     "Alerta de golpe", "Artigo e FAQ sobre como reconhecer vendedor confiável, no idioma em que a dúvida apareceu, "
     "e um short de 30s com os três sinais de golpe. É o assunto que mais converte para um site que se vende como o seguro."),
    (("revenda", "resale", "reventa", "secondary", "cambista", "tout"),
     "Revenda", "Página explicando o que o clube aceita de revenda e o que anula o ingresso. Quem pergunta isso está "
     "a um passo de comprar no lugar errado."),
    (("nominal", "name change", "titular", "personalizado", "id check", "passaporte", "passport"),
     "Ingresso nominal", "Guia do ingresso nominal por evento (já há vídeo pronto): o que fazer quando o nome não é o seu."),
    (("setor", "section", "away", "visitante", "curva", "seats", "asiento"),
     "Setores", "Mapa simples de setores do estádio com a visão de cada um, e onde fica a torcida visitante."),
    (("hotel", "hospedagem", "stay", "alojamiento", "airbnb", "hostel"),
     "Onde ficar", "Bloco de hospedagem na página do evento, com o parceiro de viagem; é a pergunta que vem logo depois do ingresso."),
    (("quanto custa", "how much", "cuanto cuesta", "price", "preco", "preço", "precio", "caro"),
     "Preço", "Faixa de preço atualizada na página do evento (o monitor de preços já guarda o mínimo) e um post curto comparando lotes."),
    (("visto", "visa", "documento", "document"),
     "Documentos", "Artigo sobre documentos e entrada no país para quem viaja só pelo jogo."),
    (("metro", "chegar", "get there", "transport", "airport", "aeroporto"),
     "Como chegar", "Transformar a seção 'como chegar' que já existe em short vertical: é conteúdo pronto virando vídeo."),
    (("stream", "assistir", "watch", "transmissao", "transmissão", "tv"),
     "Onde assistir", "A faixa AO VIVO e um post sobre onde assistir legalmente: atrai quem não vai ao estádio e "
     "ainda assim vira público do site."),
]


def termos(itens, nomes_fora):
    """Palavras e duplas que se repetem nos sinais, tirando nome de evento e palavra de ligação."""
    conta = {}
    for it in itens:
        t = norm(f"{it.get('titulo','')} {it.get('texto','')}")
        for nome in nomes_fora:
            t = t.replace(nome, " ")
        palavras = [p for p in t.split() if len(p) > 2 and p not in PARADAS and not p.isdigit()]
        vistos = set()
        for i, p in enumerate(palavras):
            for g in (p, " ".join(palavras[i:i + 2])):
                if g in vistos or len(g.split()) > 2:
                    continue
                vistos.add(g)
                d = conta.setdefault(g, {"n": 0, "ex": it.get("url", "")})
                d["n"] += 1
    return sorted(conta.items(), key=lambda kv: -kv[1]["n"])


def perguntas(itens):
    saida = []
    for it in itens:
        texto = re.sub(r"\s+", " ", f"{it.get('titulo','')} {it.get('texto','')}").strip()
        if "?" in texto or re.match(r"(?i)^(como|onde|quando|qual|how|where|when|which|d[oó]nde|cu[aá]l)\b", texto):
            saida.append((texto[:150], it.get("url", ""), it.get("fonte", "")))
    return saida[:12]


def inteligencia(itens, historico, eventos):
    """Relatório que vira plano: o que as pessoas perguntam, onde elas perguntam, e o que produzir por causa disso."""
    base = historico + itens
    hoje = datetime.date.today().isoformat()
    nomes_fora = [norm(n) for ev in eventos for n in nomes_do_evento(ev)] + ["ingresso", "ingressos", "ticket", "tickets", "entradas"]
    l = [f"# Inteligência de divulgação — {hoje}", "",
         f"Base: {len(base)} sinal(is) guardados ({len(itens)} desta rodada). Um sinal é um pedaço de conversa",
         "pública sobre um evento do site — às vezes só o trecho que sobrou na busca, e isso já basta para",
         "saber o que a pessoa queria.", ""]
    if not base:
        l += ["Ainda não há sinal guardado. Assim que uma fonte estiver com chave, este relatório se enche sozinho",
              "e passa a mandar no calendário de conteúdo.", ""]
        return "\n".join(l) + "\n"

    todos = termos(base, nomes_fora)
    repetidos = [(t, d) for t, d in todos if d["n"] >= 2]
    l += ["## O que as pessoas perguntam", ""]
    if len(repetidos) < 5:
        l += ["(Ainda com pouca repetição: a lista abaixo é o que apareceu, não um padrão.)", ""]
        repetidos = todos[:10]
    for termo, d in repetidos[:15]:
        l.append(f"- **{termo}** — {d['n']} vez(es) · exemplo: {d['ex']}")
    l += ["", "## Onde a conversa acontece", ""]
    onde = {}
    for it in base:
        chave = f"{it.get('fonte','')} · {it.get('onde','')}".strip(" ·")
        onde[chave] = onde.get(chave, 0) + 1
    for chave, n in sorted(onde.items(), key=lambda kv: -kv[1])[:12]:
        l.append(f"- {chave} — {n} sinal(is)")
    l += ["", "Estar nesses lugares vale mais do que anunciar: entre como leitor, responda o que sabe e só cite o",
          "site quando ele for mesmo a resposta. Comunidade percebe vendedor disfarçado em uma frase.", ""]

    l += ["## Perguntas em estado bruto", "", "Use como título de artigo e de vídeo: é a dúvida com as palavras de quem tem a dúvida.", ""]
    for texto, url, fonte in perguntas(base):
        l.append(f"- \"{texto}\" — {fonte}: {url}")

    l += ["", "## Procura por evento", ""]
    por_ev = {}
    for it in base:
        por_ev[it.get("evento", "")] = por_ev.get(it.get("evento", ""), 0) + 1
    for ev in eventos:
        n = por_ev.get(ev["slug"], 0)
        l.append(f"- {ev['titulo'].get('pt', ev['slug'])} — {n} sinal(is)")
    l += ["", "Evento com muito sinal e pouca página merece conteúdo novo; evento com sinal nenhum talvez não",
          "mereça o mesmo esforço de divulgação, por melhor que seja o jogo.", ""]

    l += ["## O que produzir por causa disso", ""]
    texto_todo = " ".join(norm(f"{i.get('titulo','')} {i.get('texto','')}") for i in base)
    alguma = False
    for gatilhos, nome, acao in REGRAS:
        achados = [g for g in gatilhos if norm(g) in texto_todo]
        if not achados:
            continue
        alguma = True
        n = sum(texto_todo.count(norm(g)) for g in achados)
        l.append(f"- **{nome}** ({n} menção(ões): {', '.join(achados[:4])}) — {acao}")
    if not alguma:
        l.append("- Nenhum padrão forte ainda. Com mais rodadas, as regras acima acendem sozinhas.")
    l += ["", "## Formas de divulgar que saem daqui", "",
          "1. **Responder perguntas reais** (radar/fila.md), uma a uma, dizendo que o site é seu.",
          "2. **Transformar a pergunta repetida em página**: título com as palavras da pessoa, resposta completa, "
          "e o botão de ingressos no fim. É o que o Google premia e o que a comunidade aceita como link.",
          "3. **Short vertical por dúvida**: cada regra acima vira um vídeo de 30s com a resposta e a chamada.",
          "4. **Pin e post sazonal**: o pico de procura começa semanas antes do jogo; o calendário sai da seção "
          "'Procura por evento'.",
          "5. **Parceria com quem já tem a audiência**: os domínios da seção 'Onde a conversa acontece' mostram "
          "quem publica sobre o assunto antes de você.", ""]
    return "\n".join(l) + "\n"


def main():
    if "--dias" in sys.argv:
        global DIAS
        DIAS = int(sys.argv[sys.argv.index("--dias") + 1])
    desde = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=DIAS)
    with open(os.path.join(RAIZ, "data", "eventos.json"), encoding="utf-8") as f:
        eventos = json.load(f)["eventos"]

    vistos, itens, falhas, desistir = set(), [], [], set()
    gastas = {"google": 0}
    # o evento mais próximo primeiro: é onde a procura está acontecendo agora
    hoje = datetime.date.today().isoformat()
    eventos = sorted(eventos, key=lambda e: abs((datetime.date.fromisoformat(e["data"]) - datetime.date.fromisoformat(hoje)).days))
    for ev in eventos:
        for consulta in consultas(ev):
            for nome_fonte, fonte in FONTES:
                if nome_fonte in desistir:        # fonte que já disse não: não insiste e não gasta cota
                    continue
                if nome_fonte == "Google":
                    if gastas["google"] >= LIMITE_GOOGLE:
                        continue
                    gastas["google"] += 1
                try:
                    achados = fonte(consulta, desde)
                except Exception as exc:
                    falhas.append(f"{nome_fonte} ({consulta[:40]}): {exc}")
                    texto_erro = str(exc)
                    # erro de configuração ou de cota não melhora na consulta seguinte: desliga a fonte
                    if any(m in texto_erro for m in ("HTTP 403", "HTTP 429", "HTTP 401")):
                        desistir.add(nome_fonte)
                        print(f"  ! {nome_fonte} desligada nesta rodada: {texto_erro[:120]}")
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
                    # o trecho do Google é curto por natureza: duas palavras de intenção já são sinal
                    if nota < (3 if a.get("trecho") else 4):
                        continue
                    vistos.add(a["url"])
                    lang = idioma_do_texto(texto)
                    a.update({"evento": ev["slug"], "nota": nota, "idioma": lang})
                    a["rascunho"] = rascunho(a, ev, lang)
                    itens.append(a)

    itens.sort(key=lambda x: (-x["nota"], x["quando"]), reverse=False)
    itens = sorted(itens, key=lambda x: -x["nota"])[:LIMITE_FILA]

    # histórico: o relatório fica melhor a cada rodada, então o que foi visto não se perde
    try:
        with open(os.path.join(RAIZ, "data", "mencoes.json"), encoding="utf-8") as f:
            antes = json.load(f)
    except (OSError, ValueError):
        antes = {}
    corte = (datetime.date.today() - datetime.timedelta(days=120)).isoformat()
    historico, urls = [], {i["url"] for i in itens}
    for i in antes.get("historico", []) + antes.get("itens", []):
        if i.get("url") in urls or i.get("quando", "") < corte:
            continue
        urls.add(i["url"])
        historico.append({k: i.get(k, "") for k in ("fonte", "onde", "titulo", "texto", "url", "quando", "evento", "nota")})

    os.makedirs(os.path.join(RAIZ, "radar"), exist_ok=True)
    with open(os.path.join(RAIZ, "radar", "inteligencia.md"), "w", encoding="utf-8") as f:
        f.write(inteligencia(itens, historico, eventos))
    with open(os.path.join(RAIZ, "radar", "fila.md"), "w", encoding="utf-8") as f:
        f.write(montar_fila(itens, eventos))
    with open(os.path.join(RAIZ, "data", "mencoes.json"), "w", encoding="utf-8") as f:
        json.dump({"_leia": "Escrito por scripts/radar.py. Fila de conversas públicas sobre os eventos do site "
                            "e o histórico de 120 dias que alimenta radar/inteligencia.md.",
                   "atualizado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                   "falhas": falhas, "itens": itens, "historico": historico}, f, ensure_ascii=False, indent=1)
        f.write("\n")

    unicas, vistas_falhas = [], set()
    for linha in falhas:
        chave = linha.split("(")[0] + linha.split("): ")[-1][:60]
        if chave in vistas_falhas:
            continue
        vistas_falhas.add(chave)
        unicas.append(linha)
    falhas = unicas
    for linha in falhas[:6]:
        print(f"  ! {linha}")
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"::warning::radar: {linha}")
    msg = (f"{len(itens)} conversa(s) na fila; {len(falhas)} falha(s) de fonte; "
           f"{gastas['google']} consulta(s) de {LIMITE_GOOGLE} no Google.")
    print(msg)
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::notice::radar: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
