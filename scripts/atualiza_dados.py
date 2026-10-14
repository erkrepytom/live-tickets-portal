#!/usr/bin/env python3
"""Gera dados.json com notícias esportivas internacionais, um bloco por país, e os placares do dia.

Roda a cada hora no GitHub Actions (.github/workflows/noticias.yml).

Como as notícias são escolhidas:
1. Ordem dos países: países que mais visitam o site no Google Analytics 4 (últimos 28 dias).
   Sem GA4 configurado, usa ORDEM_PADRAO.
2. Assuntos: só entram manchetes sobre os esportes, ligas, times, cidades e artistas do site
   (data/eventos.json e a lista ASSUNTOS abaixo).
3. Prioridade dentro de cada país: assuntos em alta no Google Trends daquele país e, com GA4,
   os eventos mais vistos no site.
4. Variedade: no máximo 2 manchetes por veículo em cada país.

As manchetes guardam só título, link e veículo, e o site sempre dá o crédito com link.

GA4 (opcional): secrets GA4_PROPERTY_ID e GA4_CREDENTIALS (JSON de uma conta de serviço
com acesso de leitor à propriedade). Os placares usam football-data.org quando o secret
FOOTBALL_DATA_KEY existe.
"""
import datetime
import html
import json
import math
import os
import re
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAISES = {
    "BR": {"nome": {"pt": "Brasil", "en": "Brazil", "es": "Brasil"}, "feeds": [
        ("ge", "https://ge.globo.com/rss/ge/"),
        ("UOL Esporte", "https://rss.uol.com.br/feed/esporte.xml"),
        ("Gazeta Esportiva", "https://www.gazetaesportiva.com/feed/"),
        ("ESPN Brasil", "https://www.espn.com.br/rss/")]},
    "US": {"nome": {"pt": "Estados Unidos", "en": "United States", "es": "Estados Unidos"}, "feeds": [
        ("CBS Sports", "https://www.cbssports.com/rss/headlines/"),
        ("Yahoo Sports", "https://sports.yahoo.com/rss/"),
        ("ESPN", "https://www.espn.com/espn/rss/news")]},
    "PT": {"nome": {"pt": "Portugal", "en": "Portugal", "es": "Portugal"}, "feeds": [
        ("Record", "https://www.record.pt/rss"),
        ("A Bola", "https://www.abola.pt/rss-articles.xml")]},
    "ES": {"nome": {"pt": "Espanha", "en": "Spain", "es": "España"}, "feeds": [
        ("Marca", "https://e00-marca.uecdn.es/rss/portada.xml"),
        ("Mundo Deportivo", "https://www.mundodeportivo.com/feed/rss/home")]},
    "GB": {"nome": {"pt": "Reino Unido", "en": "United Kingdom", "es": "Reino Unido"}, "feeds": [
        ("BBC Sport", "https://feeds.bbci.co.uk/sport/rss.xml"),
        ("Sky Sports", "https://www.skysports.com/rss/12040"),
        ("The Guardian", "https://www.theguardian.com/uk/sport/rss")]},
    "MX": {"nome": {"pt": "México", "en": "Mexico", "es": "México"}, "feeds": [
        ("Excélsior", "https://www.excelsior.com.mx/rss/adrenalina.xml")]},
    "AR": {"nome": {"pt": "Argentina", "en": "Argentina", "es": "Argentina"}, "feeds": [
        ("Olé", "https://www.ole.com.ar/rss/ultimas-noticias/"),
        ("Infobae", "https://www.infobae.com/arc/outboundfeeds/rss/category/deportes/")]},
    "IT": {"nome": {"pt": "Itália", "en": "Italy", "es": "Italia"}, "feeds": [
        ("La Gazzetta dello Sport", "https://www.gazzetta.it/rss/home.xml")]},
    "FR": {"nome": {"pt": "França", "en": "France", "es": "Francia"}, "feeds": [
        ("L'Équipe", "https://dwh.lequipe.fr/api/edito/rss?path=/")]},
}
ORDEM_PADRAO = ["BR", "US", "PT", "ES", "GB", "MX", "AR", "IT", "FR"]
POR_PAIS = 4
MAX_POR_VEICULO = 2

# Assuntos do site em várias línguas (além dos times, ligas, cidades e artistas de data/eventos.json).
ASSUNTOS = [
    "futebol", "football", "futbol", "calcio", "soccer", "champions", "libertadores", "la liga", "laliga", "serie a",
    "premier league", "bundesliga", "ligue 1", "nations league", "mundial", "world cup", "copa do mundo",
    "tenis", "tennis", "australian open", "open da australia", "open de australia", "roland garros", "wimbledon", "us open", "atp", "wta",
    "nba", "basquete", "basketball", "baloncesto", "knicks", "nuggets", "lakers", "celtics",
    "formula 1", "formula1", "f1", "grande premio", "grand prix", "gran premio", "verstappen", "hamilton", "leclerc", "norris",
    "rugby", "rugbi", "six nations", "springboks", "all blacks",
    "nfl", "super bowl", "mlb", "beisebol", "baseball", "nhl", "hockey",
    "show", "concert", "concerto", "concierto", "turne", "tour", "celine dion", "shakira", "oasis", "bts", "dua lipa",
    "barcelona", "barca", "real madrid", "atletico", "milan", "inter", "juventus", "roma", "lazio", "napoli",
    "manchester city", "man city", "manchester united", "liverpool", "arsenal", "chelsea", "tottenham",
    "psg", "paris saint-germain", "benfica", "porto", "sporting", "bayern", "dortmund", "boca", "river plate",
    "flamengo", "palmeiras", "corinthians", "sao paulo", "santos", "vasco", "fluminense", "botafogo", "gremio", "internacional", "cruzeiro", "atletico-mg",
    "america", "chivas", "cruz azul", "pumas", "tigres", "monterrey",
]


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))


def baixar(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MyTicketsBot/2.0", **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def limpar(t):
    t = re.sub(r"<!\[CDATA\[|\]\]>", "", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def ler_feed_tolerante(bruto, limite):
    """Para feeds com XML quebrado: extrai título e link por expressão regular."""
    s = bruto.decode("utf-8", "ignore")
    saida = []
    for bloco in re.findall(r"<item.*?</item>", s, re.S)[:limite]:
        t = re.search(r"<title[^>]*>(.*?)</title>", bloco, re.S)
        l = re.search(r"<link[^>]*>(.*?)</link>", bloco, re.S)
        if t and l and limpar(l.group(1)).startswith("http"):
            saida.append((limpar(t.group(1)), limpar(l.group(1))))
    return saida


def ler_feed(url, limite=30):
    bruto = baixar(url)
    try:
        root = ET.fromstring(bruto)
    except ET.ParseError:
        return ler_feed_tolerante(bruto, limite)
    atom = "{http://www.w3.org/2005/Atom}"
    itens = root.findall(".//item") or root.findall(f".//{atom}entry")
    saida = []
    for it in itens[:limite]:
        titulo = (it.findtext("title") or it.findtext(f"{atom}title") or "").strip()
        link = (it.findtext("link") or "").strip()
        if not link:
            el = it.find(f"{atom}link")
            link = el.get("href", "").strip() if el is not None else ""
        if titulo and link.startswith("http"):
            saida.append((limpar(titulo), link))
    return saida


def assuntos_do_site():
    """Palavras-chave dos eventos do site, com peso extra (são o que vendemos)."""
    pesos = {sem_acento(a): 1.0 for a in ASSUNTOS}
    try:
        with open(os.path.join(RAIZ, "data", "eventos.json"), encoding="utf-8") as f:
            eventos = json.load(f)["eventos"]
    except (OSError, ValueError, KeyError):
        return pesos, {}
    por_slug = {}
    for ev in eventos:
        chaves = set()
        nomes = [ev["competicao"]["nome"]] + [t["nome"] for t in ev.get("times", [])] + [ev["local"]]
        if ev.get("artista"):
            nomes.append(ev["artista"]["nome"])
        for n in nomes:
            for v in (n.values() if isinstance(n, dict) else [n]):
                chaves.add(sem_acento(v.split("(")[0].strip()))
        for c in chaves:
            if len(c) >= 3:
                pesos[c] = max(pesos.get(c, 1.0), 1.5)
        por_slug[ev["slug"]] = chaves
    return pesos, por_slug


def contem(texto, chave):
    return re.search(r"(?<![a-z0-9])" + re.escape(chave) + r"(?![a-z0-9])", texto) is not None


def tendencias(pais):
    """Buscas em alta no Google Trends do país: {termo: peso}."""
    try:
        s = baixar(f"https://trends.google.com/trending/rss?geo={pais}").decode("utf-8", "ignore")
    except Exception as exc:
        print(f"[aviso] Trends {pais}: {exc}")
        return {}
    termos = {}
    for bloco in re.findall(r"<item>(.*?)</item>", s, re.S):
        t = re.search(r"<title>([^<]+)</title>", bloco)
        tr = re.search(r"<ht:approx_traffic>([\d,.]+)", bloco)
        if t:
            volume = int(re.sub(r"[^\d]", "", tr.group(1)) or 100) if tr else 100
            termos[sem_acento(html.unescape(t.group(1)))] = math.log10(volume + 10)
    return termos


def analytics():
    """Ordem de países e peso por assunto vindos do GA4. Retorna (None, {}) se não configurado."""
    prop, cred = os.environ.get("GA4_PROPERTY_ID", "").strip(), os.environ.get("GA4_CREDENTIALS", "").strip()
    if not prop or not cred:
        print("[info] GA4 não configurado; usando a ordem padrão de países")
        return None, {}
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy, RunReportRequest
        from google.oauth2 import service_account
        cliente = BetaAnalyticsDataClient(credentials=service_account.Credentials.from_service_account_info(json.loads(cred)))
        periodo = [DateRange(start_date="28daysAgo", end_date="today")]
        r = cliente.run_report(RunReportRequest(property=f"properties/{prop}", date_ranges=periodo, dimensions=[Dimension(name="countryId")],
                                                metrics=[Metric(name="activeUsers")], order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)], limit=50))
        ordem = [row.dimension_values[0].value for row in r.rows if row.dimension_values[0].value in PAISES]
        r2 = cliente.run_report(RunReportRequest(property=f"properties/{prop}", date_ranges=periodo, dimensions=[Dimension(name="pagePath")],
                                                 metrics=[Metric(name="screenPageViews")], limit=500))
        vistas = {row.dimension_values[0].value: int(row.metric_values[0].value) for row in r2.rows}
        print(f"[ok] GA4: {len(ordem)} países com visitas, {len(vistas)} páginas")
        return ordem, vistas
    except Exception as exc:
        print(f"[aviso] GA4: {exc}")
        return None, {}


def coletar_paises():
    pesos, por_slug = assuntos_do_site()
    ordem_ga, vistas = analytics()
    # assuntos dos eventos mais vistos no site ganham peso (até +1)
    if vistas:
        total = max(vistas.values()) or 1
        for slug, chaves in por_slug.items():
            v = sum(n for p, n in vistas.items() if slug in p)
            for c in chaves:
                pesos[c] = pesos.get(c, 1.0) + v / total
    ordem = (ordem_ga or []) + [p for p in ORDEM_PADRAO if p not in (ordem_ga or [])]
    resultado = []
    for cod in ordem:
        pais = PAISES[cod]
        em_alta = tendencias(cod)
        candidatos, vistos = [], set()
        for fonte, url in pais["feeds"]:
            try:
                itens = ler_feed(url)
                print(f"[ok] {cod} {fonte}: {len(itens)}")
            except Exception as exc:
                print(f"[aviso] {cod} {fonte}: {exc}")
                continue
            for pos, (titulo, link) in enumerate(itens):
                t = sem_acento(titulo)
                if t in vistos:
                    continue
                vistos.add(t)
                assunto = sum(p for c, p in pesos.items() if contem(t, c))
                if not assunto:
                    continue  # fora dos assuntos do site
                alta = sum(p for termo, p in em_alta.items() if termo and contem(t, termo))
                nota = assunto + 2 * alta + max(0, 1 - pos / 30)  # recência dentro do feed
                candidatos.append({"t": titulo[:150], "u": link, "f": fonte, "nota": round(nota, 2), "alta": alta > 0})
        candidatos.sort(key=lambda x: -x["nota"])
        escolhidas, por_veiculo = [], {}
        for c in candidatos:
            if por_veiculo.get(c["f"], 0) < MAX_POR_VEICULO:
                escolhidas.append(c)
                por_veiculo[c["f"]] = por_veiculo.get(c["f"], 0) + 1
            if len(escolhidas) >= POR_PAIS:
                break
        if escolhidas:
            resultado.append({"pais": cod, "nome": pais["nome"], "noticias": [{k: c[k] for k in ("t", "u", "f", "alta")} for c in escolhidas]})
    return resultado, ("analytics" if ordem_ga else "padrao")


def coletar_jogos():
    chave = os.environ.get("FOOTBALL_DATA_KEY", "").strip()
    if not chave:
        print("[info] FOOTBALL_DATA_KEY ausente; placares desativados")
        return []
    try:
        hoje = datetime.date.today().isoformat()
        dados = json.loads(baixar(f"https://api.football-data.org/v4/matches?dateFrom={hoje}&dateTo={hoje}", headers={"X-Auth-Token": chave}))
        jogos = [{"liga": m["competition"]["name"],
                  "casa": m["homeTeam"].get("shortName") or m["homeTeam"].get("name", ""),
                  "fora": m["awayTeam"].get("shortName") or m["awayTeam"].get("name", ""),
                  "gc": m["score"]["fullTime"]["home"], "gf": m["score"]["fullTime"]["away"],
                  "status": m["status"], "hora": m["utcDate"]} for m in dados.get("matches", [])[:14]]
        print(f"[ok] football-data: {len(jogos)} jogos")
        return jogos
    except Exception as exc:
        print(f"[aviso] football-data: {exc}")
        return []


def principal():
    paises, ordem = coletar_paises()
    # "destaques" mantém o formato antigo: a primeira manchete de cada país, na ordem do ranking
    destaques = [dict(p["noticias"][0], pais=p["pais"]) for p in paises if p["noticias"]]
    saida = {
        "atualizado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "ordem_paises": ordem,
        "paises": paises,
        "destaques": destaques,
        "jogos": coletar_jogos(),
    }
    with open(os.path.join(RAIZ, "dados.json"), "w", encoding="utf-8") as arq:
        json.dump(saida, arq, ensure_ascii=False, indent=1)
    print(f"dados.json gerado: {len(paises)} países, {sum(len(p['noticias']) for p in paises)} notícias, ordem={ordem}")


if __name__ == "__main__":
    principal()
