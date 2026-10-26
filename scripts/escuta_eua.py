#!/usr/bin/env python3
"""Escuta social nos EUA: encontra onde as pessoas estão comentando sobre ingressos dos eventos do site
e monta uma lista priorizada de conversas para responder (prospecção manual, nunca automática).

Roda todo dia no GitHub Actions (.github/workflows/escuta-eua.yml) ou à mão: python scripts/escuta_eua.py

De onde vem:
- Reddit: busca pública em RSS (sem login) nas comunidades de cada time, liga e cidade dos eventos dos EUA
  em data/eventos.json, mais as comunidades gerais de ingressos e viagem em COMUNIDADES_GERAIS.
- YouTube (opcional): com o secret YOUTUBE_API_KEY, busca vídeos recentes de cada jogo e lê os comentários.

O que sai (nada vai para o site nem para o repositório):
- relatorios/escuta-eua.json: todas as conversas com nota, intenção e evento ligado.
- relatorios/escuta-eua.md: as melhores, em tabela, com a resposta sugerida (docs/prospeccao-eua.md).
- No Actions, a tabela também aparece no resumo da execução e os dois arquivos ficam como artefato.

Nota de cada conversa (0 a 100): intenção de compra no texto, evento do site citado e quanto é recente.
"""
import datetime as dt
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
import xml.etree.ElementTree as ET

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "relatorios")
UA = "Mozilla/5.0 (compatible; MyTicketsToursBot/1.0; +https://mytickets.tours/)"
ATOM = {"a": "http://www.w3.org/2005/Atom"}
DIAS = 30  # janela da busca

# Comunidade de cada time, liga e cidade. Time sem entrada aqui é buscado só nas comunidades gerais.
SUBREDDITS = {
 "Dallas Cowboys": "cowboys", "San Francisco 49ers": "49ers", "Philadelphia Eagles": "eagles",
 "Los Angeles Lakers": "lakers", "Miami Heat": "heat", "New York Knicks": "NYKnicks", "Denver Nuggets": "denvernuggets",
 "NFL": "nfl", "NBA": "nba",
 "Dallas": "Dallas", "Los Angeles": "LosAngeles", "New York": "nyc",
}
# Onde turistas e compradores de ingresso perguntam, independente do time.
COMUNIDADES_GERAIS = ["tickets", "travel", "solotravel", "TravelNoPics", "AskAnAmerican"]

# Sinais de que a pessoa está decidindo uma compra ou planejando ir. Peso entre parênteses.
INTENCAO = [
 (r"\b(where|how) (to|do i|can i|should i) (buy|get|find)\b", 30, "onde_comprar"),
 (r"\b(legit|scam|fake|safe|trust(ed|worthy)?)\b", 25, "confianca"),
 (r"\b(cheap(est)?|price|cost|how much|budget|deal)\b", 20, "preco"),
 (r"\b(first (time|game)|visiting|tourist|from (brazil|abroad|europe|the uk|mexico)|trip|travel(l)?ing)\b", 20, "turista"),
 (r"\b(seats?|section|lower bowl|upper deck|view)\b", 15, "setor"),
 (r"\b(tickets?|resale|stubhub|seatgeek|ticketmaster|vivid)\b", 15, "ingresso"),
 (r"\b(parking|get(ting)? there|uber|metro|tailgat\w*)\b", 10, "chegar"),
]
# Conversas que não adiantam: vendedor anunciando, sorteio, briga.
DESCARTE = re.compile(r"\b(for sale|selling|wts|giveaway|venmo me|dm me for)\b", re.I)


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()


def eventos_eua():
    with open(os.path.join(RAIZ, "data", "eventos.json"), encoding="utf-8") as f:
        evs = json.load(f)["eventos"]
    hoje = dt.date.today().isoformat()
    return [e for e in evs if e.get("pais", {}).get("en") in ("USA", "United States") and e["data"] >= hoje]


def nomes(ev):
    """Nomes que identificam o evento numa conversa: times, apelidos (última palavra), local e cidade."""
    out = set()
    for t in ev.get("times", []):
        out.add(norm(t["nome"]))
        out.add(norm(t["nome"]).split()[-1])  # "cowboys", "lakers", "49ers"
    out.add(norm(ev["local"]))
    return {n for n in out if len(n) > 3}


def buscas(evs):
    """(subreddit, termo, evento) a consultar. Comunidade de time busca "tickets"; geral busca o nome do time."""
    pares = []
    for ev in evs:
        times = [t["nome"] for t in ev.get("times", [])]
        lugares = times + [ev["competicao"]["nome"], ev["cidade"]["en"]]
        for nome in lugares:
            sub = SUBREDDITS.get(nome)
            if sub:
                pares.append((sub, "tickets", ev["slug"]))
        for sub in COMUNIDADES_GERAIS:
            if times:
                pares.append((sub, f'"{times[0].split()[-1]}" tickets', ev["slug"]))
    vistos, unicos = set(), []
    for p in pares:
        if p[:2] not in vistos:
            vistos.add(p[:2])
            unicos.append(p)
    return unicos


def baixar(url, tentativas=2):
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError) as erro:
            if i + 1 == tentativas:
                print(f"  falhou {url}: {erro}", file=sys.stderr)
            time.sleep(3)
    return None


def ler_atom(xml_txt, fonte, comunidade):
    """Itens de um feed Atom do Reddit: título, link, data e o começo do texto."""
    itens = []
    try:
        raiz = ET.fromstring(xml_txt)
    except ET.ParseError:
        return itens
    for ent in raiz.findall("a:entry", ATOM):
        link = ent.find("a:link", ATOM)
        corpo = ent.findtext("a:content", "", ATOM)
        texto = re.sub(r"<[^>]+>", " ", html.unescape(corpo))
        itens.append({
            "fonte": fonte, "comunidade": comunidade,
            "titulo": (ent.findtext("a:title", "", ATOM) or "").strip(),
            "url": link.get("href") if link is not None else "",
            "data": (ent.findtext("a:updated", "", ATOM) or "")[:10],
            "texto": re.sub(r"\s+", " ", texto).strip()[:600],
        })
    return itens


def reddit(sub, termo):
    q = urllib.parse.urlencode({"q": termo, "restrict_sr": "1", "sort": "new", "t": "month"})
    xml_txt = baixar(f"https://www.reddit.com/r/{sub}/search.rss?{q}")
    return ler_atom(xml_txt, "reddit", f"r/{sub}") if xml_txt else []


def youtube(ev, chave):
    """Comentários de vídeos recentes sobre o jogo (YouTube Data API v3, cota gratuita)."""
    termo = ev["titulo"]["en"] + " tickets"
    depois = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=DIAS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    q = urllib.parse.urlencode({"part": "snippet", "q": termo, "type": "video", "maxResults": 5,
                                "publishedAfter": depois, "regionCode": "US", "key": chave})
    busca = baixar(f"https://www.googleapis.com/youtube/v3/search?{q}")
    itens = []
    for v in json.loads(busca).get("items", []) if busca else []:
        vid = v["id"]["videoId"]
        q2 = urllib.parse.urlencode({"part": "snippet", "videoId": vid, "maxResults": 50, "order": "relevance",
                                     "textFormat": "plainText", "key": chave})
        coms = baixar(f"https://www.googleapis.com/youtube/v3/commentThreads?{q2}")
        for c in json.loads(coms).get("items", []) if coms else []:
            s = c["snippet"]["topLevelComment"]["snippet"]
            itens.append({"fonte": "youtube", "comunidade": v["snippet"]["channelTitle"],
                          "titulo": v["snippet"]["title"],
                          "url": f"https://www.youtube.com/watch?v={vid}&lc={c['id']}",
                          "data": s["publishedAt"][:10], "texto": s["textDisplay"][:600]})
    return itens


def avaliar(item, evs, hoje):
    """Nota de 0 a 100 e intenção principal. None quando a conversa deve ser descartada."""
    texto = norm(item["titulo"] + " " + item["texto"])
    if DESCARTE.search(texto):
        return None
    pontos, intencoes = 0, []
    for padrao, peso, nome in INTENCAO:
        if re.search(padrao, texto):
            pontos += peso
            intencoes.append(nome)
    if not intencoes:
        return None
    evento = next((e["slug"] for e in evs if any(n in texto for n in nomes(e))), "")
    if evento:
        pontos += 20
    try:
        idade = (hoje - dt.date.fromisoformat(item["data"])).days
    except ValueError:
        idade = DIAS
    pontos += max(0, 15 - idade)  # até 15 pontos para conversas de hoje
    return {**item, "nota": min(100, pontos), "intencao": intencoes[0], "sinais": intencoes, "evento": evento}


def relatorio_md(itens, total_buscas, falhas):
    linhas = [f"# Escuta EUA ({dt.date.today().isoformat()})", "",
              f"{len(itens)} conversas com intenção de compra em {total_buscas} buscas"
              + (f" ({falhas} sem resultado ou bloqueadas)" if falhas else "") + ".",
              "Responda à mão seguindo `docs/prospeccao-eua.md`. Resposta sugerida = modelo da seção 3.", "",
              "| Nota | Onde | Conversa | Evento | Resposta sugerida |", "| --- | --- | --- | --- | --- |"]
    for i in itens[:40]:
        titulo = i["titulo"].replace("|", "/")[:90]
        linhas.append(f"| {i['nota']} | {i['comunidade']} | [{titulo}]({i['url']}) | {i['evento'] or '—'} | {i['intencao']} |")
    return "\n".join(linhas) + "\n"


def main():
    hoje = dt.date.today()
    evs = eventos_eua()
    if not evs:
        print("Nenhum evento futuro nos EUA em data/eventos.json.")
        return
    lista, falhas = buscas(evs), 0
    brutos = []
    for sub, termo, _slug in lista:
        achados = reddit(sub, termo)
        falhas += 0 if achados else 1
        brutos += achados
        time.sleep(2)  # educação com a busca pública
    chave = os.environ.get("YOUTUBE_API_KEY")
    if chave:
        for ev in evs:
            brutos += youtube(ev, chave)
    vistos, itens = set(), []
    for b in brutos:
        if b["url"] in vistos:
            continue
        vistos.add(b["url"])
        a = avaliar(b, evs, hoje)
        if a:
            itens.append(a)
    itens.sort(key=lambda x: x["nota"], reverse=True)

    os.makedirs(SAIDA, exist_ok=True)
    with open(os.path.join(SAIDA, "escuta-eua.json"), "w", encoding="utf-8") as f:
        json.dump({"gerado": hoje.isoformat(), "buscas": len(lista), "falhas": falhas, "itens": itens},
                  f, ensure_ascii=False, indent=1)
    md = relatorio_md(itens, len(lista), falhas)
    with open(os.path.join(SAIDA, "escuta-eua.md"), "w", encoding="utf-8") as f:
        f.write(md)
    resumo = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumo:
        with open(resumo, "a", encoding="utf-8") as f:
            f.write(md)
    print(f"{len(itens)} conversas relevantes de {len(brutos)} lidas em {len(lista)} buscas ({falhas} sem resultado).")


if __name__ == "__main__":
    main()
