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
import json
import os
import re
import sys
import unicodedata
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


def ler_feed(canal_id=None):
    url = FEED if not canal_id else f"https://www.youtube.com/feeds/videos.xml?channel_id={canal_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (mytickets.tours videos bot)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raiz = ET.fromstring(r.read())
    if canal_id:  # guarda o nome do canal para o chamador conferir de quem é o feed
        TITULO_CANAL[canal_id] = (raiz.findtext("a:title", default="", namespaces=NS) or "").strip()
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
            cid = r.get("channel_id", "")
            if not re.fullmatch(r"UC[A-Za-z0-9_-]{22}", cid):
                print(f"  ! canal de reserva sem channel_id válido: {r.get('canal','?')}")
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


def main():
    arq = os.path.join(RAIZ, "data", "videos.json")
    with open(arq, encoding="utf-8") as f:
        dados = json.load(f)
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
