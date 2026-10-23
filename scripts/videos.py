#!/usr/bin/env python3
"""Puxa os vídeos novos do canal do YouTube para data/videos.json (o site funciona como o Blogger: publicou no
YouTube, o vídeo aparece no site na próxima rodada, já ligado ao evento e ao botão de ingressos).

Roda a cada 6 horas no GitHub Actions (.github/workflows/videos.yml) ou à mão: python scripts/videos.py

Como cada vídeo novo é preenchido:
- yt, titulo, publicado: do feed RSS público do canal (sem chave de API).
- idioma: pelo título (palavras típicas de PT/EN/ES); pode corrigir no JSON.
- evento: o evento de data/eventos.json cujos nomes (times, artista, competição, cidade) mais aparecem no título.
  Sem evento claro, fica vazio e o vídeo só aparece em /videos/ e na home, com o botão "Ver guia" escondido.
- cta: {"tipo": "evento"} quando há evento (botão "Ver ingressos"). Edite para "viagem" ou "url" quando quiser.

O script nunca apaga nem reescreve o que já está no JSON: só acrescenta IDs novos e reordena por data.
"""
import datetime
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANAL_ID = os.environ.get("YOUTUBE_CHANNEL_ID", "UCIUejr6o9Rdvsg_07x6kziA")  # @Tickets.Sports.Events
FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CANAL_ID}"
UA = "Mozilla/5.0 (compatible; MyTicketsToursBot/1.0; +https://mytickets.tours/)"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "media": "http://search.yahoo.com/mrss/"}

PALAVRAS = {
    "pt": {"ingressos", "ingresso", "como", "jogo", "partida", "saindo", "brasil", "viagem", "estádio", "estadio", "final", "veja", "onde", "comprar", "do", "da", "no", "na"},
    "en": {"tickets", "ticket", "how", "game", "match", "from", "abroad", "trip", "stadium", "watch", "where", "buy", "the", "to", "guide"},
    "es": {"entradas", "entrada", "cómo", "como", "partido", "desde", "viaje", "estadio", "mira", "dónde", "comprar", "del", "en", "el", "la", "guía"},
}


TITULO_CANAL = {}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s)


def idioma(titulo, descricao=""):
    toks = set(norm(titulo + " " + descricao[:200]).split())
    pontos = {l: len(toks & {norm(w).strip() for w in ws}) for l, ws in PALAVRAS.items()}
    if "ingress" in norm(titulo) or " x " in f" {norm(titulo)} ":
        pontos["pt"] += 2
    if "entradas" in norm(titulo):
        pontos["es"] += 2
    melhor = max(pontos, key=pontos.get)
    return melhor if pontos[melhor] else "pt"


def nomes_evento(ev):
    nomes = set()
    for tm in ev.get("times", []):
        nomes.add(norm(tm["nome"] if isinstance(tm["nome"], str) else tm["nome"].get("en", "")))
    if ev.get("artista"):
        nomes.add(norm(ev["artista"]["nome"]))
    comp = ev.get("competicao", {}).get("nome")
    if comp:
        nomes.add(norm(comp if isinstance(comp, str) else comp.get("en", "")))
    for l in ("pt", "en", "es"):
        nomes.add(norm(ev["cidade"].get(l, "")))
        nomes.add(norm(ev["titulo"].get(l, "")))
    return {n.strip() for n in nomes if len(n.strip()) >= 3}


def nota_evento(titulo, descricao, ev):
    """Quanto o título/descrição falam deste evento (mesmos pesos de casar_evento)."""
    texto = " " + norm(titulo + " " + descricao[:300]) + " "
    n = 0
    for nome in nomes_evento(ev):
        if f" {nome} " in texto:
            n += 3 if len(nome) > 8 else 2
    if ev["data"][:4] in titulo:
        n += 1
    return n


def casar_evento(titulo, descricao, eventos):
    texto = " " + norm(titulo + " " + descricao[:300]) + " "
    melhor, nota = None, 0
    for ev in eventos:
        n = 0
        for nome in nomes_evento(ev):
            if f" {nome} " in texto:
                n += 3 if len(nome) > 8 else 2
        # o ano no título (2026) ajuda a separar edições do mesmo confronto
        if ev["data"][:4] in titulo:
            n += 1
        if n > nota:
            melhor, nota = ev, n
    return melhor["slug"] if melhor and nota >= 2 else ""


def _baixar_feed(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (mytickets.tours videos bot)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _json_depois(html, marca):
    """Pega o objeto JSON que vem depois de uma marca no HTML, contando as chaves."""
    i = html.find(marca)
    if i < 0:
        return None
    i = html.find("{", i)
    if i < 0:
        return None
    nivel, dentro, escapa = 0, False, False
    for j in range(i, len(html)):
        c = html[j]
        if escapa:
            escapa = False
            continue
        if c == "\\" and dentro:
            escapa = True
        elif c == '"':
            dentro = not dentro
        elif not dentro and c == "{":
            nivel += 1
        elif not dentro and c == "}":
            nivel -= 1
            if nivel == 0:
                try:
                    return json.loads(html[i:j + 1])
                except Exception:
                    return None
    return None


def _texto_de(no, limite=3):
    """Primeiro texto com cara de título dentro de um nó (aguenta os dois formatos do YouTube:
    title.runs/simpleText nos renderers antigos e title.content no lockupViewModel novo)."""
    if limite < 0:
        return ""
    if isinstance(no, dict):
        for chave in ("simpleText", "content"):
            v = no.get(chave)
            if isinstance(v, str) and len(v.strip()) > 8:
                return v.strip()
        runs = no.get("runs")
        if isinstance(runs, list):
            t = "".join(r.get("text", "") for r in runs if isinstance(r, dict)).strip()
            if len(t) > 8:
                return t
        for chave in ("title", "headline", "metadata", "lockupMetadataViewModel", "accessibility"):
            if chave in no:
                t = _texto_de(no[chave], limite - 1)
                if t:
                    return t
    return ""


def _colher_videos(no, achados, vistos):
    """Anda pelo ytInitialData juntando (videoId, título, "há 3 dias")."""
    if isinstance(no, dict):
        vid = no.get("videoId") or no.get("contentId")
        if isinstance(vid, str) and re.fullmatch(r"[A-Za-z0-9_-]{11}", vid) and vid not in vistos:
            texto = _texto_de(no)
            if texto:
                quando = no.get("publishedTimeText")
                quando = quando.get("simpleText", "") if isinstance(quando, dict) else (quando if isinstance(quando, str) else "")
                if not quando:
                    quando = _texto_de(no.get("metadata", {}), 2) if isinstance(no.get("metadata"), dict) else ""
                vistos.add(vid)
                achados.append({"yt": vid, "titulo": texto, "quando": quando})
        for v in no.values():
            _colher_videos(v, achados, vistos)
    elif isinstance(no, list):
        for v in no:
            _colher_videos(v, achados, vistos)


def _data_aproximada(quando):
    """"há 3 dias" / "3 days ago" → data aproximada, só para ordenar a faixa."""
    m = re.search(r"(\d+)\s*(hora|hour|dia|day|semana|week|m[eê]s|month|ano|year)", quando or "", re.I)
    hoje = datetime.date.today()
    if not m:
        return hoje.isoformat()
    n, u = int(m.group(1)), m.group(2).lower()
    dias = {"hora": 0, "hour": 0, "dia": 1, "day": 1, "semana": 7, "week": 7}.get(u, 30 if u.startswith(("m", "mê")) else 365)
    return (hoje - datetime.timedelta(days=n * dias)).isoformat()


def videos_da_pagina(canal_id):
    """Plano C: alguns canais não servem feed RSS (a CazéTV é um deles). Aí os vídeos recentes
    saem da própria aba /videos do canal, lendo o ytInitialData da página."""
    req = urllib.request.Request(f"https://www.youtube.com/channel/{canal_id}/videos",
                                 headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"})
    with urllib.request.urlopen(req, timeout=25) as r:
        html = r.read().decode("utf-8", "replace")
    dados = _json_depois(html, "ytInitialData")
    if dados is None:
        print(f"  ! não achei o ytInitialData na aba /videos de {canal_id} ({len(html)} bytes)")
        return "", []
    achados, vistos = [], set()
    _colher_videos(dados, achados, vistos)
    nome = ""
    meta = re.search(r'<meta property="og:title" content="([^"]{1,80})"', html)
    if meta:
        nome = meta.group(1)
    print(f"  · aba /videos de {canal_id}: {len(achados)} vídeo(s) lidos da página")
    itens = [{"yt": a["yt"], "titulo": a["titulo"], "publicado": _data_aproximada(a["quando"]), "descricao": ""}
             for a in achados[:30]]
    return nome, itens


def ler_feed(canal_id=None):
    if not canal_id:
        dados = _baixar_feed(FEED)
    else:
        try:
            dados = _baixar_feed(f"https://www.youtube.com/feeds/videos.xml?channel_id={canal_id}")
        except urllib.error.HTTPError as exc:
            # Alguns canais não servem o feed por channel_id; o da playlist de uploads (UC... → UU...) responde.
            if exc.code != 404:
                raise
            try:
                dados = _baixar_feed(f"https://www.youtube.com/feeds/videos.xml?playlist_id=UU{canal_id[2:]}")
            except urllib.error.HTTPError as exc2:
                if exc2.code != 404:
                    raise
                nome, itens = videos_da_pagina(canal_id)   # plano C: a aba /videos do canal
                if nome:
                    TITULO_CANAL[canal_id] = nome
                return itens
    raiz = ET.fromstring(dados)
    if canal_id:  # guarda o nome do canal para o chamador conferir de quem é o feed
        autor = raiz.find("a:author/a:name", NS)
        TITULO_CANAL[canal_id] = ((autor.text if autor is not None and autor.text else "")
                                  or (raiz.findtext("a:title", default="", namespaces=NS) or "")).strip()
    itens = []
    for en in raiz.findall("a:entry", NS):
        vid = en.findtext("yt:videoId", default="", namespaces=NS)
        titulo = en.findtext("a:title", default="", namespaces=NS).strip()
        pub = en.findtext("a:published", default="", namespaces=NS)[:10]
        grupo = en.find("media:group", NS)
        desc = grupo.findtext("media:description", default="", namespaces=NS) if grupo is not None else ""
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
            itens.append({"yt": vid, "titulo": titulo, "publicado": pub, "descricao": desc.strip()})
    return itens



def permite_embed(yt):
    """True se o vídeo pode ser exibido fora do YouTube.

    Alguns donos de canal (LALIGA, ligas e emissoras) bloqueiam a exibição em sites de terceiros.
    O player então mostra "Vídeo indisponível" no lugar do vídeo, o que fica péssimo na página.
    A página /embed/ traz "playableInEmbed": false nesses casos.
    Em caso de erro de rede devolve None, e aí o chamador não mexe no que já está publicado.
    """
    req = urllib.request.Request(f"https://www.youtube.com/embed/{yt}",
                                headers={"User-Agent": UA, "Accept-Language": "en"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            html = r.read().decode("utf-8", "replace")
    except Exception as exc:
        print(f"  ! não deu para checar o embed de {yt}: {exc}")
        return None
    if '"playableInEmbed":false' in html.replace(" ", ""):
        return False
    if '"status":"UNPLAYABLE"' in html.replace(" ", ""):
        return False
    return True


def revisar_embeds(dados):
    """Desativa os vídeos que o dono do canal bloqueou para exibição fora do YouTube.
    Devolve a lista dos que saíram do ar, para o canal de reserva repor o jogo."""
    mudou = []
    for v in dados.get("videos", []):
        if not v.get("ativo", True):
            continue
        ok = permite_embed(v["yt"])
        if ok is False:
            v["ativo"] = False
            v["nota_embed"] = "O canal bloqueia a exibição fora do YouTube; desativado automaticamente."
            print(f"- {v['yt']} ({v.get('canal','?')}): bloqueado para embed, desativado.")
            mudou.append(v)
    return mudou


def repor_bloqueados(dados, eventos, desativados):
    """Quando o canal da liga bloqueia a exibição fora do YouTube, procura o mesmo jogo
    nos canais de reserva de data/videos.json (campo canais_reserva) — emissoras e canais
    que transmitem a competição com direitos, não recortes de terceiros.

    Só entra vídeo que (1) fala do mesmo evento, (2) é do canal de reserva e (3) permite embed.
    """
    reservas = dados.get("canais_reserva", [])
    if not reservas or not desativados:
        return 0
    por_slug = {ev["slug"]: ev for ev in eventos}
    ja = {v["yt"] for v in dados.get("videos", [])}
    ativos = {v.get("evento") for v in dados.get("videos", []) if v.get("ativo", True)}
    postos = 0
    for v in desativados:
        slug = v.get("evento")
        ev = por_slug.get(slug)
        if not ev or slug in ativos:   # o evento já tem outro vídeo no ar
            continue
        for r in reservas:
            cid = canal_id_da_reserva(r)
            if not cid:
                print(f"  ! canal de reserva sem channel_id nem @handle que resolva: {r.get('canal','?')}")
                continue
            try:
                itens = ler_feed(cid)
            except Exception as exc:
                print(f"  ! feed do canal de reserva {r.get('canal','?')} indisponível: {exc}")
                continue
            nome_feed = TITULO_CANAL.get(cid, "")
            if nome_feed and norm(r.get("canal", "")).strip() not in norm(nome_feed):
                print(f"  ! o channel_id de {r.get('canal','?')} aponta para \"{nome_feed}\"; "
                      f"confira o ID em data/videos.json. Nada foi reposto por ele.")
                continue
            candidatos = sorted(((nota_evento(i["titulo"], i["descricao"], ev), i) for i in itens),
                                key=lambda x: x[0], reverse=True)
            for nota, it in candidatos:
                if nota < 2 or it["yt"] in ja:
                    continue
                if permite_embed(it["yt"]) is not True:
                    continue
                novo = {"yt": it["yt"], "titulo": it["titulo"], "canal": r.get("canal", ""),
                        "idioma": r.get("idioma") or idioma(it["titulo"], it["descricao"]),
                        "publicado": it["publicado"], "evento": slug,
                        "cta": {"tipo": "evento"}, "ativo": True,
                        "nota_embed": f"Entrou no lugar de {v['yt']} ({v.get('canal','?')}), que bloqueia a exibição fora do YouTube."}
                if it["descricao"]:
                    novo["descricao"] = it["descricao"][:300]
                dados["videos"].append(novo)
                ja.add(it["yt"])
                ativos.add(slug)
                postos += 1
                print(f"+ {it['yt']} ({novo['canal']}) repõe {v['yt']} em {slug}")
                break
            if slug in ativos:
                break
    return postos


def resolver_canal(handle):
    """Descobre o channel_id (UC...) a partir do @handle do canal, porque o feed RSS do YouTube
    só aceita channel_id. Devolve "" quando não achar."""
    handle = (handle or "").strip().lstrip("@")
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,30}", handle):
        return ""
    req = urllib.request.Request(f"https://www.youtube.com/@{handle}",
                                 headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            html = r.read().decode("utf-8", "replace")
    except Exception as exc:
        print(f"  ! não deu para abrir o canal @{handle}: {exc}")
        return ""
    for padrao in (r'"(?:channelId|externalId)":"(UC[A-Za-z0-9_-]{22})"',
                   r'itemprop="identifier"\s+content="(UC[A-Za-z0-9_-]{22})"',
                   r'/channel/(UC[A-Za-z0-9_-]{22})'):
        m = re.search(padrao, html)
        if m:
            return m.group(1)
    return ""


def canal_id_da_reserva(r):
    """O channel_id escrito em data/videos.json; sem ele, resolve pelo @handle."""
    cid = (r.get("channel_id") or "").strip()
    if re.fullmatch(r"UC[A-Za-z0-9_-]{22}", cid):
        return cid
    return resolver_canal(r.get("handle", ""))


def aviso(texto, erro=False):
    """No GitHub Actions também deixa o texto como anotação da execução, que aparece no resumo."""
    print(texto)
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::{'error' if erro else 'notice'}::{texto}")


def conferir_reservas(dados):
    """python scripts/videos.py --conferir: diz se cada channel_id de canais_reserva é mesmo
    do canal escrito ao lado. Sai com código 1 quando algum não bate, para o Actions acusar."""
    reservas = dados.get("canais_reserva", [])
    if not reservas:
        print("Nenhum canal de reserva em data/videos.json.")
        return 0
    erros = 0
    for r in reservas:
        nome = r.get("canal", "?")
        cid = canal_id_da_reserva(r)
        if not cid:
            aviso(f"{nome}: sem channel_id válido e o @handle {r.get('handle','(vazio)')} não resolveu.", True)
            erros += 1
            continue
        if cid != (r.get("channel_id") or ""):
            aviso(f"{nome}: channel_id resolvido pelo handle → {cid} (vale escrever em data/videos.json).")
        try:
            itens = ler_feed(cid)
        except Exception as exc:
            aviso(f"{nome}: feed de {cid} indisponível ({exc}).", True)
            try:  # diz de quem é o ID, para saber se o erro é do ID ou do feed
                req = urllib.request.Request(f"https://www.youtube.com/channel/{cid}",
                                             headers={"User-Agent": UA, "Accept-Language": "pt-BR"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    html = r.read().decode("utf-8", "replace")
                m = re.search(r'<meta property="og:title" content="([^"]{1,80})"', html)
                c = re.search(r'"canonicalBaseUrl":"/(@[A-Za-z0-9._-]{3,30})"', html)
                aviso(f"{nome}: a página /channel/{cid} responde como \"{m.group(1) if m else '?'}\""
                      f"{' (' + c.group(1) + ')' if c else ''}.")
            except Exception as exc2:
                aviso(f"{nome}: a página /channel/{cid} também não abriu ({exc2}).")
            erros += 1
            continue
        feed = TITULO_CANAL.get(cid, "")
        bate = norm(nome).strip() in norm(feed)
        aviso(f"{nome} → feed de \"{feed}\", {len(itens)} vídeo(s) recentes; "
              f"{'o ID bate com o nome' if bate else 'O ID NÃO BATE com o nome'}.", not bate)
        for it in itens[:3]:
            aviso(f"   {nome}: {it['publicado']} {it['titulo'][:70]}")
        erros += 0 if bate else 1
    return 1 if erros else 0


def main():
    arq = os.path.join(RAIZ, "data", "videos.json")
    with open(arq, encoding="utf-8") as f:
        dados = json.load(f)
    if "--conferir" in sys.argv:
        return conferir_reservas(dados)
    with open(os.path.join(RAIZ, "data", "eventos.json"), encoding="utf-8") as f:
        eventos = json.load(f)["eventos"]
    existentes = {v["yt"] for v in dados.get("videos", [])}
    try:
        feed = ler_feed()
    except Exception as exc:  # feed fora do ar não derruba o robô
        print(f"Feed do YouTube indisponível: {exc}")
        return 0
    novos = 0
    for it in feed:
        if it["yt"] in existentes:
            continue
        slug = casar_evento(it["titulo"], it["descricao"], eventos)
        v = {"yt": it["yt"], "titulo": it["titulo"], "canal": "Tickets Sports & Events", "idioma": idioma(it["titulo"], it["descricao"]), "publicado": it["publicado"],
             "evento": slug, "cta": {"tipo": "evento"} if slug else {}, "ativo": True}
        if it["descricao"]:
            v["descricao"] = it["descricao"][:300]
        dados.setdefault("videos", []).append(v)
        novos += 1
        print(f"+ {it['yt']} [{v['idioma']}] {it['titulo'][:60]} → {slug or '(sem evento)'}")
    desativados = revisar_embeds(dados)
    bloqueados = len(desativados)
    # os que já estavam desativados por bloqueio também entram na fila: se o evento ficou sem vídeo,
    # o canal de reserva repõe o jogo na próxima rodada.
    antigos = [v for v in dados.get("videos", [])
               if not v.get("ativo", True) and "bloquei" in v.get("nota_embed", "").lower()
               and v not in desativados]
    repostos = repor_bloqueados(dados, eventos, desativados + antigos)
    if novos or bloqueados or repostos:
        dados["videos"].sort(key=lambda v: v.get("publicado", ""), reverse=True)
        with open(arq, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=1)
            f.write("\n")
    print(f"{novos} vídeo(s) novo(s); {bloqueados} desativado(s) por bloqueio de embed; "
          f"{repostos} reposto(s) por canal de reserva; {len(dados.get('videos', []))} no total.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
