#!/usr/bin/env python3
"""Títulos e descrições com mais clique: o Search Console aponta, a IA propõe, uma pessoa decide.

Modelo do SeatPick (auditoria contínua com Search Console + IA). Toda semana:
  1. lê do Search Console as páginas com impressões e CTR abaixo do esperado para a posição média;
  2. junta as buscas que levaram a cada página e o título/descrição atuais (do HTML gerado);
  3. pede ao Claude 3 opções de título (até 60 caracteres) e descrição (até 155), no idioma da página,
     usando só fatos que já estão na página;
  4. grava radar/ctr.md. Nada é trocado no site: os títulos vêm de scripts/conteudo.py
     (titulo_evento e ROT["desc"]); quem aprova uma opção ajusta lá.

Segredos/variáveis: ANTHROPIC_API_KEY; GSC_CREDENTIALS (JSON da conta de serviço com acesso de leitura
à propriedade no Search Console); GSC_SITE (padrão sc-domain:mytickets.tours).
Dependência só no workflow: pip install google-auth requests.
Uso: python scripts/ia_ctr.py [--dias 28] [--min-impressoes 30]
"""
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ia  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://mytickets.tours/"
SITE = os.environ.get("GSC_SITE", "sc-domain:mytickets.tours")
# CTR orgânico típico por posição (curva aproximada de estudos públicos de CTR; serve só de régua).
CTR_ESPERADO = {1: .28, 2: .15, 3: .10, 4: .07, 5: .05, 6: .04, 7: .03, 8: .025, 9: .02, 10: .018}
LIMITE = 10  # páginas por rodada


def token_gsc():
    from google.oauth2 import service_account  # só no workflow
    from google.auth.transport.requests import Request
    info = json.loads(os.environ["GSC_CREDENTIALS"])
    cred = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    cred.refresh(Request())
    return cred.token


def consulta(token, dias, dimensoes, filtro_pagina=None):
    import requests
    fim = dt.date.today() - dt.timedelta(days=3)  # o Search Console atrasa ~3 dias
    corpo = {"startDate": (fim - dt.timedelta(days=dias)).isoformat(), "endDate": fim.isoformat(),
             "dimensions": dimensoes, "rowLimit": 500}
    if filtro_pagina:
        corpo["dimensionFilterGroups"] = [{"filters": [{"dimension": "page", "operator": "equals", "expression": filtro_pagina}]}]
    url = f"https://www.googleapis.com/webmasters/v3/sites/{urllib.parse.quote(SITE, safe='')}/searchAnalytics/query"
    r = requests.post(url, json=corpo, headers={"Authorization": f"Bearer {token}"}, timeout=60)
    r.raise_for_status()
    return r.json().get("rows", [])


def meta_local(url):
    """Título e descrição atuais da página, lidos do HTML gerado no repositório."""
    caminho = urllib.parse.urlparse(url).path.strip("/")
    arq = os.path.join(RAIZ, caminho, "index.html") if caminho else os.path.join(RAIZ, "index.html")
    try:
        s = open(arq, encoding="utf-8").read()
    except OSError:
        return None
    t = re.search(r"<title>(.*?)</title>", s, re.S)
    d = re.search(r'<meta name="description" content="(.*?)"', s, re.S)
    lang = re.search(r'<html lang="([^"]+)"', s)
    texto = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S)))
    return {"titulo": html.unescape(t.group(1)) if t else "", "desc": html.unescape(d.group(1)) if d else "",
            "lang": lang.group(1) if lang else "", "texto": html.unescape(texto)[:3500]}


def candidatas(linhas, minimo):
    out = []
    for r in linhas:
        imp, ctr, pos = r["impressions"], r["ctr"], r["position"]
        if imp < minimo or pos > 10.5:
            continue
        esperado = CTR_ESPERADO.get(max(1, round(pos)), .018)
        if ctr < esperado * .7:
            out.append({"url": r["keys"][0], "impressoes": imp, "cliques": r["clicks"], "ctr": ctr, "pos": pos,
                        "perda": round(imp * (esperado - ctr))})
    return sorted(out, key=lambda x: -x["perda"])[:LIMITE]


PROMPT = """Você otimiza títulos e descrições de resultado do Google para um guia independente de ingressos (MyTickets Tours).
Idioma da página: {lang}. Escreva TUDO nesse idioma.

Título atual: {titulo}
Descrição atual: {desc}
Buscas que mostraram a página (impressões): {buscas}
Texto da página (use só fatos daqui; não invente preço, data, garantia nem selo):
{texto}

Regras: título até 60 caracteres, descrição até 155; responda à busca principal nas primeiras palavras; nada de
"oficial", "melhor preço" ou urgência falsa; o site não vende o ingresso, a venda é do parceiro.
Devolva só JSON: {{"diagnostico": "uma frase", "opcoes": [{{"titulo": "...", "descricao": "..."}}, ... 3 opções]}}"""


def main():
    dias = int(sys.argv[sys.argv.index("--dias") + 1]) if "--dias" in sys.argv else 28
    minimo = int(sys.argv[sys.argv.index("--min-impressoes") + 1]) if "--min-impressoes" in sys.argv else 30
    saida = os.path.join(RAIZ, "radar", "ctr.md")
    hoje = dt.date.today().isoformat()
    if not (ia.ativo() and os.environ.get("GSC_CREDENTIALS")):
        open(saida, "w", encoding="utf-8").write(
            f"# Títulos e descrições para testar — {hoje}\n\nAinda não rodou: faltam os segredos ANTHROPIC_API_KEY e "
            "GSC_CREDENTIALS no GitHub (veja o README, seção IA).\n")
        print("Segredos ausentes: otimizador de CTR não rodou.")
        return
    token = token_gsc()
    paginas = candidatas(consulta(token, dias, ["page"]), minimo)
    out = [f"# Títulos e descrições para testar — {hoje}", "",
           f"Páginas com CTR abaixo do esperado para a posição (últimos {dias} dias, mínimo {minimo} impressões). "
           "Escolha uma opção e ajuste o modelo em scripts/conteudo.py; nada foi trocado no site.", ""]
    for p in paginas:
        m = meta_local(p["url"])
        if not m:
            continue
        buscas = consulta(token, dias, ["query"], p["url"])[:12]
        lista = "; ".join(f'{b["keys"][0]} ({b["impressions"]})' for b in buscas) or "sem dados de busca"
        try:
            r = ia.perguntar(PROMPT.format(lang=m["lang"], titulo=m["titulo"], desc=m["desc"], buscas=lista, texto=m["texto"]),
                             max_tokens=1200)
            prop = ia.json_da_resposta(r["texto"])
        except (RuntimeError, ValueError) as erro:
            print(f"Falhou em {p['url']}: {erro}")
            continue
        out += [f"## {p['url'].replace(BASE, '/')}", "",
                f"{p['impressoes']} impressões, {p['cliques']} cliques, CTR {p['ctr']:.1%}, posição {p['pos']:.1f} "
                f"(cerca de {p['perda']} cliques a mais se chegasse ao CTR típico).", "",
                f"- Atual: **{m['titulo']}** — {m['desc']}", f"- Buscas: {lista}", f"- Diagnóstico: {prop.get('diagnostico', '')}", ""]
        for i, o in enumerate(prop.get("opcoes", [])[:3], 1):
            out.append(f"{i}. **{o['titulo']}** ({len(o['titulo'])}) — {o['descricao']} ({len(o['descricao'])})")
        out.append("")
    if len(out) <= 4:
        out.append("Nenhuma página abaixo do esperado nesta rodada.")
    open(saida, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(f"{len(paginas)} página(s) analisadas; propostas em radar/ctr.md")


if __name__ == "__main__":
    main()
