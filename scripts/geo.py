#!/usr/bin/env python3
"""Monitor GEO: o MyTickets aparece quando alguém pergunta a uma IA onde comprar ingresso?

Modelo copiado do SeatPick, que mede citações e "share of voice" em ChatGPT, Perplexity e AI Overviews.
Aqui o teste é feito com o Claude e a busca na web da própria API: para cada evento do site faz as
perguntas que um comprador faria, nos 3 idiomas, e registra quais sites a resposta cita.

Saídas (nada vai para o site):
  data/geo.json   histórico de cada rodada (pergunta, sites citados, se o MyTickets apareceu)
  radar/geo.md    relatório: % de perguntas em que cada site é citado e o que fazer com isso

Custo: cada pergunta usa até GEO_BUSCAS buscas (padrão 3). Com o padrão de 12 perguntas por rodada,
são no máximo 36 buscas (cerca de US$ 0,36) mais os tokens, uma vez por semana.
Uso: python scripts/geo.py [--max 12]
"""
import datetime as dt
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ia  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOSSO = "mytickets.tours"
# Concorrentes acompanhados (os do estudo de modus operandi) e outros comuns nesse nicho.
CONCORRENTES = ["stubhub", "viagogo", "seatpick", "ticombo", "p1travel", "sportsevents365", "365tickets",
                "footballticketnet", "livefootballtickets", "fanpass", "ticketmaster", "seatgeek", "vividseats",
                "tickpick", "sportsbreaks", "superingressos"]
LOCAL = {"pt": {"country": "BR", "timezone": "America/Sao_Paulo"}, "en": {"country": "US"}, "es": {"country": "MX"}}
PERGUNTAS = {
    "pt": ["Onde comprar ingresso para {t} em {d}? É seguro comprar pela internet sendo do Brasil?",
           "Quanto custa ver {t} ao vivo e como chegar ao {l}?"],
    "en": ["Where can I buy tickets for {t} on {d}? Which sites are safe?",
           "How much are tickets for {t} and how do I get to {l}?"],
    "es": ["¿Dónde comprar entradas para {t} el {d}? ¿Qué webs son seguras?",
           "¿Cuánto cuestan las entradas para {t} y cómo llegar al {l}?"],
}
SISTEMA = ("Responda como um assistente de busca ajudaria um torcedor comum: procure na web, recomende onde comprar "
           "e cite as fontes. Responda no idioma da pergunta, em até 150 palavras.")


def dominio(url):
    host = urllib.parse.urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def marca(host):
    for c in [NOSSO] + CONCORRENTES:
        if c.split(".")[0] in host:
            return c.split(".")[0]
    return None


def perguntas_da_rodada(eventos, maximo, semana):
    """Gira as perguntas semana a semana para cobrir todos os eventos e idiomas sem estourar o custo."""
    todas = []
    for ev in eventos:
        for lang, modelos in PERGUNTAS.items():
            for i, m in enumerate(modelos):
                titulo = ev["titulo"][lang] if isinstance(ev["titulo"], dict) else ev["titulo"]
                todas.append({"slug": ev["slug"], "lang": lang, "modelo": i,
                              "pergunta": m.format(t=titulo, d=ev["data"], l=ev["local"].split(" (")[0])})
    if not todas:
        return []
    ini = (semana * maximo) % len(todas)
    return (todas[ini:] + todas[:ini])[:maximo]


def relatorio(historico):
    """radar/geo.md: share of voice das últimas 4 rodadas e a lista do que fazer."""
    rodadas = historico[-4:]
    linhas = [r for rod in rodadas for r in rod["respostas"]]
    hoje = dt.date.today().isoformat()
    out = [f"# Presença em respostas de IA (GEO) — {hoje}", ""]
    if not linhas:
        out += ["Ainda sem rodada. Cadastre o segredo ANTHROPIC_API_KEY no GitHub para o monitor rodar.", ""]
        return "\n".join(out)
    total = len(linhas)
    cont = {}
    for r in linhas:
        for m in set(r["marcas"]):
            cont[m] = cont.get(m, 0) + 1
    nosso = cont.get("mytickets", 0)
    out += [f"Base: {total} perguntas em {len(rodadas)} rodada(s). O MyTickets foi citado em {nosso} "
            f"({100 * nosso // total}%).", "", "| Site | Perguntas em que foi citado | % |", "| --- | --- | --- |"]
    for m, n in sorted(cont.items(), key=lambda x: -x[1]):
        out.append(f"| {m} | {n} | {100 * n // total}% |")
    out += ["", "## Perguntas em que o MyTickets não apareceu", "",
            "Para cada uma: a página do evento responde exatamente isso, nas primeiras linhas? Se não, ajuste o texto "
            "e confira se a página está indexada. Os sites citados no lugar mostram o formato que a IA preferiu.", ""]
    for r in linhas:
        if "mytickets" not in r["marcas"]:
            citados = ", ".join(sorted({dominio(c) for c in r["citados"]})[:6]) or "nenhum site"
            out.append(f"- [{r['lang']}] {r['pergunta']} → citou: {citados}")
    out.append("")
    return "\n".join(out)


def main():
    maximo = int(os.environ.get("GEO_MAX", "12"))
    if "--max" in sys.argv:
        maximo = int(sys.argv[sys.argv.index("--max") + 1])
    buscas = int(os.environ.get("GEO_BUSCAS", "3"))
    arq = os.path.join(RAIZ, "data", "geo.json")
    try:
        historico = json.load(open(arq, encoding="utf-8"))
    except (OSError, ValueError):
        historico = []
    if not ia.ativo():
        print("ANTHROPIC_API_KEY ausente: monitor GEO não rodou.")
        open(os.path.join(RAIZ, "radar", "geo.md"), "w", encoding="utf-8").write(relatorio(historico))
        return
    eventos = json.load(open(os.path.join(RAIZ, "data", "eventos.json"), encoding="utf-8"))["eventos"]
    hoje = dt.date.today()
    eventos = [ev for ev in eventos if ev["data"] >= hoje.isoformat()]
    respostas = []
    for p in perguntas_da_rodada(eventos, maximo, hoje.isocalendar()[1]):
        try:
            r = ia.perguntar(p["pergunta"], sistema=SISTEMA, buscas=buscas, max_tokens=900, local=LOCAL[p["lang"]])
        except RuntimeError as erro:
            print(f"Falhou: {p['pergunta']}: {erro}")
            continue
        citados = [c["url"] for c in r["citacoes"] if not c.get("so_resultado")] or [c["url"] for c in r["citacoes"]]
        marcas = sorted({m for m in (marca(dominio(u)) for u in citados) if m})
        if "mytickets" in r["texto"].lower().replace(" ", "") and "mytickets" not in marcas:
            marcas.append("mytickets")
        respostas.append(dict(p, citados=citados, marcas=marcas, buscas=r["buscas"]))
        print(f"[{p['lang']}] {'SIM' if 'mytickets' in marcas else 'não'} · {p['pergunta'][:70]}")
    historico.append({"data": hoje.isoformat(), "modelo": ia.MODELO, "respostas": respostas})
    historico = historico[-26:]  # meio ano de rodadas semanais
    json.dump(historico, open(arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(RAIZ, "radar", "geo.md"), "w", encoding="utf-8").write(relatorio(historico))
    print(f"{len(respostas)} pergunta(s) feitas; relatório em radar/geo.md")


if __name__ == "__main__":
    main()
