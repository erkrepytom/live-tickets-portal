#!/usr/bin/env python3
"""Gera dados.json com manchetes esportivas (RSS) e placares do dia.

Roda no GitHub Actions (ver .github/workflows/noticias.yml). As manchetes
guardam apenas título + link + fonte, exibidos no site com link de
atribuição para o veículo. Os placares usam football-data.org e só são
buscados quando o secret FOOTBALL_DATA_KEY existe.
"""
import datetime
import html
import json
import os
import urllib.request
import xml.etree.ElementTree as ET

FEEDS = [
    ("ge", "https://ge.globo.com/rss/ge/"),
    ("UOL Esporte", "https://rss.uol.com.br/feed/esporte.xml"),
    ("Gazeta Esportiva", "https://www.gazetaesportiva.com/feed/"),
    ("ESPN Brasil", "https://www.espn.com.br/rss/"),
]

MAX_DESTAQUES = 12


def baixar(url, headers=None):
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (MyTicketsBot/1.0)", **(headers or {})}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def coletar_destaques():
    por_fonte = {}
    for fonte, url in FEEDS:
        try:
            root = ET.fromstring(baixar(url))
            itens = root.findall(".//item") or root.findall(
                ".//{http://www.w3.org/2005/Atom}entry"
            )
            lista = []
            for it in itens[:6]:
                titulo = (it.findtext("title") or it.findtext(
                    "{http://www.w3.org/2005/Atom}title") or "").strip()
                link = (it.findtext("link") or "").strip()
                if not link:
                    el = it.find("{http://www.w3.org/2005/Atom}link")
                    link = el.get("href", "").strip() if el is not None else ""
                if titulo and link.startswith("http"):
                    lista.append({"t": html.unescape(titulo)[:140], "u": link, "f": fonte})
            if lista:
                por_fonte[fonte] = lista
            print(f"[ok] {fonte}: {len(lista)} manchetes")
        except Exception as exc:  # fonte fora do ar não derruba o robô
            print(f"[aviso] {fonte}: {exc}")

    # intercala as fontes para variar os destaques
    mix, vistos = [], set()
    while len(mix) < MAX_DESTAQUES and any(por_fonte.values()):
        for fonte in list(por_fonte):
            if por_fonte[fonte]:
                item = por_fonte[fonte].pop(0)
                chave = item["t"].lower()
                if chave not in vistos:
                    vistos.add(chave)
                    mix.append(item)
                if len(mix) >= MAX_DESTAQUES:
                    break
    return mix


def coletar_jogos():
    chave = os.environ.get("FOOTBALL_DATA_KEY", "").strip()
    if not chave:
        print("[info] FOOTBALL_DATA_KEY ausente; placares desativados")
        return []
    try:
        hoje = datetime.date.today().isoformat()
        dados = json.loads(
            baixar(
                f"https://api.football-data.org/v4/matches?dateFrom={hoje}&dateTo={hoje}",
                headers={"X-Auth-Token": chave},
            )
        )
        jogos = []
        for m in dados.get("matches", [])[:14]:
            jogos.append(
                {
                    "liga": m["competition"]["name"],
                    "casa": m["homeTeam"].get("shortName") or m["homeTeam"].get("name", ""),
                    "fora": m["awayTeam"].get("shortName") or m["awayTeam"].get("name", ""),
                    "gc": m["score"]["fullTime"]["home"],
                    "gf": m["score"]["fullTime"]["away"],
                    "status": m["status"],
                    "hora": m["utcDate"],
                }
            )
        print(f"[ok] football-data: {len(jogos)} jogos")
        return jogos
    except Exception as exc:
        print(f"[aviso] football-data: {exc}")
        return []


def principal():
    saida = {
        "atualizado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "destaques": coletar_destaques(),
        "jogos": coletar_jogos(),
    }
    with open("dados.json", "w", encoding="utf-8") as arq:
        json.dump(saida, arq, ensure_ascii=False, indent=1)
    print(f"dados.json gerado: {len(saida['destaques'])} destaques, {len(saida['jogos'])} jogos")


if __name__ == "__main__":
    principal()
