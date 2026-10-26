#!/usr/bin/env python3
"""Confere o site gerado e reprova a publicação se alguma página afirmar algo falso.

Nasceu de um erro real: o jogo acabou e a página continuou no ar com preço,
botão de compra e dados estruturados dizendo que havia ingresso à venda. Um
site que afirma fato falso perde a pessoa e perde a citação do assistente de IA.

Roda depois do gerar_paginas.py:  python scripts/conferir_site.py
Sai com código 1 se houver erro, 0 se estiver limpo.
"""

import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.parse

RAIZ = pathlib.Path(__file__).resolve().parent.parent
HOJE = dt.date.today().isoformat()
IGNORAR = ("go/", "ir/", "radar/", "scripts/", "tools/", "node_modules/")

erros, avisos = [], []


def erro(pagina, texto):
    erros.append(f"{pagina}: {texto}")


def aviso(pagina, texto):
    avisos.append(f"{pagina}: {texto}")


def paginas():
    for caminho in sorted(RAIZ.glob("**/index.html")):
        rel = caminho.relative_to(RAIZ).as_posix()
        if rel.startswith(IGNORAR) or "/node_modules/" in rel:
            continue
        yield rel, caminho


def blocos_ld(html, pagina):
    saida = []
    for bruto in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            dado = json.loads(bruto)
        except json.JSONDecodeError as exc:
            erro(pagina, f"JSON-LD inválido ({exc.msg})")
            continue
        saida += dado.get("@graph", [dado])
    return saida


def eventos_por_slug():
    try:
        dados = json.loads((RAIZ / "data" / "eventos.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {ev["slug"]: ev for ev in dados.get("eventos", [])}


EVENTOS = eventos_por_slug()


def slug_da_pagina(pagina):
    partes = [p for p in pagina.split("/") if p and p != "index.html"]
    return partes[-1] if partes and partes[-1] in EVENTOS else None


# --------------------------------------------------------------- conferências

def conferir_evento_passado(pagina, html, nos, slug):
    """O erro que originou este arquivo: evento que já passou ainda vendendo."""
    ev = EVENTOS.get(slug)
    if not ev or ev["data"] >= HOJE:
        return
    if re.search(r'href="[^"]*/go/[^"]*"', html):
        erro(pagina, f"evento de {ev['data']} já passou e a página ainda tem link de compra")
    for no in nos:
        if no.get("@type") in ("SportsEvent", "MusicEvent") and no.get("offers"):
            erro(pagina, f"evento de {ev['data']} já passou e o JSON-LD ainda declara offers")
    if "ev-fim" not in html:
        erro(pagina, f"evento de {ev['data']} já passou e falta o aviso de encerrado")


def conferir_grafo(pagina, nos):
    ids = {n.get("@id") for n in nos if n.get("@id")}
    for no in nos:
        for chave, valor in no.items():
            if isinstance(valor, dict) and list(valor.keys()) == ["@id"] and valor["@id"] not in ids:
                erro(pagina, f"@graph aponta para {valor['@id']} ({chave}), que não existe nesta página")


def conferir_canonical(pagina, html):
    achado = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    if not achado:
        erro(pagina, "sem canonical")
        return
    esperado = "https://mytickets.tours/" + ("" if pagina == "index.html" else pagina.replace("index.html", ""))
    if achado.group(1).rstrip("/") != esperado.rstrip("/"):
        erro(pagina, f"canonical aponta para {achado.group(1)}, não para a própria página")


def conferir_hreflang(pagina, html):
    alt = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', html)
    if not alt:
        return
    idiomas = {l for l, _ in alt}
    if "x-default" not in idiomas:
        aviso(pagina, "hreflang sem x-default")
    propria = "https://mytickets.tours/" + ("" if pagina == "index.html" else pagina.replace("index.html", ""))
    if not any(u.rstrip("/") == propria.rstrip("/") for l, u in alt if l != "x-default"):
        erro(pagina, "hreflang não inclui a própria página (reciprocidade quebrada)")


def conferir_preco(pagina, html, nos):
    visivel = re.sub(r"<[^>]+>", " ", html)
    for no in nos:
        oferta = no.get("offers") if isinstance(no.get("offers"), dict) else None
        if not oferta:
            continue
        valor = oferta.get("lowPrice") or oferta.get("price")
        if not valor:
            continue
        inteiro = str(valor).split(".")[0]
        if inteiro not in visivel.replace(",", "").replace(".", ""):
            erro(pagina, f"JSON-LD declara preço {valor} que não aparece no texto visível")


def conferir_links(pagina, html, caminho):
    base = caminho.parent
    for href in re.findall(r'href="([^"#?]+)"', html):
        if href.startswith(("http://", "https://", "mailto:", "tel:", "data:", "//")):
            continue
        alvo = (base / urllib.parse.unquote(href)).resolve()
        if alvo.is_dir():
            alvo = alvo / "index.html"
        try:
            alvo.relative_to(RAIZ)
        except ValueError:
            erro(pagina, f"link sai da raiz do site: {href}")
            continue
        if not alvo.exists():
            erro(pagina, f"link interno quebrado: {href}")


def conferir_links_ocultos(pagina, html):
    if re.search(r'display:\s*none[^>]{0,120}>\s*<a\s', html) or re.search(r'<a [^>]*style="[^"]*display:\s*none', html):
        erro(pagina, "link escondido no HTML — é sinal de spam para o Google")


def conferir_robots():
    arq = RAIZ / "robots.txt"
    if not arq.exists():
        erros.append("robots.txt: não existe")
        return
    txt = arq.read_text(encoding="utf-8")
    if re.search(r"^\s*Disallow:\s*/\s*$", txt, re.M):
        erros.append("robots.txt: há um Disallow: / que bloquearia o site inteiro")
    for agente in ("OAI-SearchBot", "PerplexityBot", "ChatGPT-User", "Bingbot", "Googlebot"):
        bloco = re.search(rf"^User-agent:\s*{agente}\s*$(.*?)(?=^User-agent:|\Z)", txt, re.M | re.S)
        if bloco and "Disallow: /_internal/" not in bloco.group(1):
            erros.append(f"robots.txt: o grupo de {agente} existe sem repetir as proibições — "
                         f"esse robô passará a ignorar o grupo * inteiro")


def principal():
    conferir_robots()
    total = 0
    for pagina, caminho in paginas():
        total += 1
        html = caminho.read_text(encoding="utf-8", errors="replace")
        nos = blocos_ld(html, pagina)
        slug = slug_da_pagina(pagina)
        if slug:
            conferir_evento_passado(pagina, html, nos, slug)
        conferir_grafo(pagina, nos)
        conferir_canonical(pagina, html)
        conferir_hreflang(pagina, html)
        conferir_preco(pagina, html, nos)
        conferir_links(pagina, html, caminho)
        conferir_links_ocultos(pagina, html)

    for texto in avisos:
        print(f"aviso  {texto}")
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"::warning::{texto}")
    for texto in erros:
        print(f"ERRO   {texto}")
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"::error::{texto}")

    resumo = f"{total} páginas conferidas: {len(erros)} erro(s), {len(avisos)} aviso(s)"
    print(resumo)
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::notice::{resumo}")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(principal())
