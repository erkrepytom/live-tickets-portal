"""Lê o menor preço de cada evento no parceiro (SportsEvents365) e grava em data/precos.json.

A página de evento do parceiro traz os lotes à venda nos dados estruturados (JSON-LD, "offers" com
"price" e "priceCurrency"). Guardamos o menor preço em estoque, a moeda e quando foi conferido.
O gerador usa esse preço na página e no JSON-LD só enquanto ele é recente (PRECO_VALIDADE_H);
se a leitura falhar, o preço anterior fica guardado, mas some do site quando envelhece.

Roda no GitHub Actions (.github/workflows/precos.yml). Uso local: python scripts/precos.py
"""
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQ = RAIZ / "data" / "precos.json"
DOMINIO = {"pt": "https://365tickets.com.br", "en": "https://www.sportsevents365.com", "es": "https://sportsevents365.es"}
UA = "Mozilla/5.0 (compatible; MyTicketsToursBot/1.0; +https://mytickets.tours/)"


def ofertas(html):
    """Lista (preço, moeda) dos lotes em estoque no JSON-LD da página."""
    achados = []
    for bloco in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        try:
            dados = json.loads(bloco)
        except ValueError:
            continue
        nos = dados.get("@graph", [dados]) if isinstance(dados, dict) else dados
        for no in nos if isinstance(nos, list) else []:
            if not isinstance(no, dict) or "offers" not in no:
                continue
            ofs = no["offers"] if isinstance(no["offers"], list) else [no["offers"]]
            for o in ofs:
                if not isinstance(o, dict) or "InStock" not in str(o.get("availability", "InStock")):
                    continue
                try:
                    preco = float(o.get("price") if o.get("price") is not None else o.get("lowPrice"))
                except (TypeError, ValueError):
                    continue
                if preco > 0 and re.fullmatch(r"[A-Z]{3}", str(o.get("priceCurrency", ""))):
                    achados.append((preco, o["priceCurrency"]))
    return achados


def ler(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def main():
    eventos = json.loads((RAIZ / "data" / "eventos.json").read_text(encoding="utf-8"))["eventos"]
    hoje = dt.date.today().isoformat()
    try:
        precos = json.loads(ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        precos = {}
    agora = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    ok = falhas = 0
    for ev in eventos:
        if ev["data"] < hoje:
            precos.pop(str(ev["id"]), None)
            continue
        for lang, dom in DOMINIO.items():
            url = f"{dom}/event/{ev['id']}"
            try:
                lista = ofertas(ler(url))
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                print(f"- {ev['slug']} [{lang}]: falhou ({e}); mantém o preço anterior, se houver.")
                falhas += 1
                continue
            if not lista:
                print(f"- {ev['slug']} [{lang}]: nenhum lote em estoque nos dados da página.")
                precos.setdefault(str(ev["id"]), {}).pop(lang, None)
                continue
            moeda = lista[0][1]
            menor = min(p for p, m in lista if m == moeda)
            precos.setdefault(str(ev["id"]), {})[lang] = {"min": round(menor, 2), "moeda": moeda, "lotes": len(lista),
                                                          "conferido": agora, "fonte": url}
            print(f"- {ev['slug']} [{lang}]: a partir de {menor:,.0f} {moeda} ({len(lista)} lotes)")
            ok += 1
            time.sleep(1.5)
    ARQ.write_text(json.dumps(precos, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Pronto: {ok} preço(s) lido(s), {falhas} falha(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
