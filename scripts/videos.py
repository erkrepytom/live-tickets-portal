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
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "media": "http://search.yahoo.com/mrss/"}

PALAVRAS = {
    "pt": {"ingressos", "ingresso", "como", "jogo", "partida", "saindo", "brasil", "viagem", "estádio", "estadio", "final", "veja", "onde", "comprar", "do", "da", "no", "na"},
    "en": {"tickets", "ticket", "how", "game", "match", "from", "abroad", "trip", "stadium", "watch", "where", "buy", "the", "to", "guide"},
    "es": {"entradas", "entrada", "cómo", "como", "partido", "desde", "viaje", "estadio", "mira", "dónde", "comprar", "del", "en", "el", "la", "guía"},
}


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


def ler_feed():
    req = urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0 (mytickets.tours videos bot)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raiz = ET.fromstring(r.read())
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
    if novos:
        dados["videos"].sort(key=lambda v: v.get("publicado", ""), reverse=True)
        with open(arq, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=1)
            f.write("\n")
    print(f"{novos} vídeo(s) novo(s); {len(dados.get('videos', []))} no total.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
