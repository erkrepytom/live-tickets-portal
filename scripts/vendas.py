#!/usr/bin/env python3
"""Monitor de venda: lê a página oficial de ingressos de cada evento (VENDA_OFICIAL em conteudo.py) e o estoque do
parceiro (data/precos.json) e grava data/vendas.json com o status: a_venda, em_breve, esgotado ou desconhecido.

A página do evento mostra o status. O campo "mudancas" guarda as últimas transições (os alertas de venda por
e-mail foram retirados do site em 25/10/2026; o histórico fica para um futuro aviso pelo WhatsApp).

Leitura das páginas: Scrapling (Fetcher, sem navegador; cabeçalhos realistas e TLS de navegador) quando instalado,
senão urllib. Com SCRAPLING_STEALTH=1 e os navegadores instalados (`scrapling install`), usa o StealthyFetcher
para páginas que bloqueiam clientes HTTP comuns. Roda no GitHub Actions (.github/workflows/vendas.yml) ou à mão.

Como classifica: procura, no texto visível da página, janelas de ~400 caracteres ao redor das palavras que
identificam o evento (ex.: "real madrid") e conta sinais de cada status em vários idiomas. Sem janela com o
evento, usa a página inteira com confiança baixa. Nunca inventa: sem sinal, fica "desconhecido".
"""
import datetime as dt
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import conteudo as C  # noqa: E402

ARQ = RAIZ / "data" / "vendas.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"

SINAIS = {
 "esgotado": ["sold out", "soldout", "esgotado", "esgotados", "agotado", "agotadas", "complet", "esaurito", "esauriti", "ausverkauft", "no tickets available", "não há ingressos", "sin entradas"],
 "a_venda": ["buy tickets", "buy now", "get tickets", "tickets available", "on sale now", "now on sale", "book now", "purchase tickets",
             "comprar ingressos", "comprar entradas", "entradas disponibles", "ingressos disponíveis", "à venda", "a la venta", "en venta",
             "acheter", "billets disponibles", "en vente", "acquista", "biglietti disponibili", "in vendita", "tickets kaufen", "jetzt kaufen", "add to basket", "add to cart", "select seats"],
 "em_breve": ["coming soon", "on sale from", "on sale soon", "sale starts", "sales open", "tickets will be available", "register your interest", "register interest",
              "presale", "pre-sale", "waiting list", "waitlist", "em breve", "vendas abrem", "abertura das vendas", "próximamente", "proximamente", "a la venta el",
              "venta a partir", "prochainement", "mise en vente", "ouverture de la billetterie", "prossimamente", "in vendita dal", "bald verfügbar", "ballot", "application window"],
}
PRIORIDADE = ["esgotado", "a_venda", "em_breve"]


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s)


def _texto_de_html(html):
    html = re.sub(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"&nbsp;|&#160;", " ", html)
    return re.sub(r"\s+", " ", html)


def ler(url):
    """Texto visível da página e código HTTP. Scrapling quando disponível; urllib como reserva."""
    try:
        from scrapling.fetchers import Fetcher, StealthyFetcher  # type: ignore
    except Exception:  # scrapling não instalado
        Fetcher = StealthyFetcher = None
    if Fetcher is not None:
        try:
            if os.environ.get("SCRAPLING_STEALTH") == "1":
                try:
                    pg = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
                except TypeError:
                    pg = StealthyFetcher().fetch(url, headless=True, network_idle=True, timeout=60000)
            else:
                try:
                    pg = Fetcher.get(url, stealthy_headers=True, follow_redirects=True, timeout=30)
                except TypeError:
                    pg = Fetcher().get(url, stealthy_headers=True, follow_redirects=True, timeout=30)
            status = int(getattr(pg, "status", 200) or 200)
            try:
                texto = pg.get_all_text(ignore_tags=("script", "style", "noscript"))
            except Exception:
                texto = _texto_de_html(getattr(pg, "body", b"").decode("utf-8", "replace") if isinstance(getattr(pg, "body", b""), bytes) else str(getattr(pg, "body", "")))
            return re.sub(r"\s+", " ", texto or ""), status, "scrapling"
        except Exception as e:  # cai para urllib
            print(f"  scrapling falhou ({e.__class__.__name__}); tentando urllib")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en,pt;q=0.8,es;q=0.7", "Accept": "text/html,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return _texto_de_html(r.read().decode("utf-8", "replace")), r.status, "urllib"


def classificar(texto, palavras):
    """(status, confianca 0-1, trecho) a partir do texto da página e das palavras do evento."""
    t = norm(texto)
    janelas = []
    for p in palavras:
        p = norm(p)
        for m in re.finditer(re.escape(p), t):
            janelas.append(t[max(0, m.start() - 400): m.end() + 400])
    alvo, conf_base = (janelas, 0.8) if janelas else ([t], 0.35)
    contagem = {k: 0 for k in SINAIS}
    trecho = ""
    for j in alvo:
        for k, lista in SINAIS.items():
            for s in lista:
                for m in re.finditer(re.escape(norm(s)), j):
                    contagem[k] += 1
                    if not trecho:
                        trecho = j[max(0, m.start() - 80): m.end() + 80].strip()
    total = sum(contagem.values())
    if not total:
        return "desconhecido", 0.0, ""
    # esgotado perto do evento vence; depois "a venda" (há um botão de compra); "em breve" só quando é o único sinal forte
    if contagem["esgotado"] and janelas:
        st = "esgotado"
    elif contagem["a_venda"] >= max(1, contagem["em_breve"]):
        st = "a_venda"
    elif contagem["em_breve"]:
        st = "em_breve"
    else:
        st = max(contagem, key=contagem.get)
    conf = round(min(1.0, conf_base * (0.6 + 0.1 * min(4, contagem[st]))), 2)
    return st, conf, trecho[:240]


def status_parceiro(ev, precos, agora):
    """Estoque no parceiro a partir de data/precos.json (lido pelo robô de preços)."""
    linhas = precos.get(str(ev["id"]), {})
    if not linhas:
        return {"status": "desconhecido", "conferido": agora}
    melhor = None
    for lang, pr in linhas.items():
        if pr.get("lotes", 0) > 0 and (melhor is None or pr["min"] < melhor["min"]):
            melhor = {**pr, "lang": lang}
    if melhor:
        return {"status": "a_venda", "min": melhor["min"], "moeda": melhor["moeda"], "lotes": melhor["lotes"], "conferido": melhor["conferido"], "fonte": melhor.get("fonte", "")}
    recente = max(linhas.values(), key=lambda p: p.get("conferido", ""))
    return {"status": "esgotado", "lotes": 0, "conferido": recente.get("conferido", agora), "fonte": recente.get("fonte", "")}


def main():
    eventos = json.loads((RAIZ / "data" / "eventos.json").read_text(encoding="utf-8"))["eventos"]
    hoje = dt.date.today().isoformat()
    try:
        vendas = json.loads(ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        vendas = {}
    try:
        precos = json.loads((RAIZ / "data" / "precos.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        precos = {}
    agora = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    vendas.pop("_leia", None)
    for slug in list(vendas):
        if not any(ev["slug"] == slug and ev["data"] >= hoje for ev in eventos):
            vendas.pop(slug)
    for ev in eventos:
        if ev["data"] < hoje:
            continue
        reg = vendas.setdefault(ev["slug"], {"mudancas": []})
        anterior = (reg.get("oficial") or {}).get("status"), (reg.get("parceiro") or {}).get("status")
        fonte = C.VENDA_OFICIAL.get(C.chave_evento(ev["slug"]))
        if fonte:
            nome, url, palavras = fonte
            try:
                texto, http, motor = ler(url)
                st, conf, trecho = classificar(texto, palavras) if http < 400 else ("desconhecido", 0.0, f"HTTP {http}")
                reg["oficial"] = {"nome": nome, "status": st, "confianca": conf, "trecho": trecho, "fonte": url, "http": http, "motor": motor, "conferido": agora}
                print(f"- {ev['slug']}: oficial={st} ({conf}) via {motor} [{http}]")
            except Exception as e:
                reg.setdefault("oficial", {"nome": nome, "status": "desconhecido", "fonte": url})
                reg["oficial"].update({"erro": f"{e.__class__.__name__}: {str(e)[:120]}", "tentado": agora})
                print(f"- {ev['slug']}: oficial indisponível ({e.__class__.__name__}); mantém o status anterior")
            time.sleep(2)
        reg["parceiro"] = status_parceiro(ev, precos, agora)
        print(f"  parceiro={reg['parceiro']['status']}" + (f" {reg['parceiro'].get('lotes')} lotes desde {reg['parceiro'].get('min')} {reg['parceiro'].get('moeda')}" if reg["parceiro"].get("lotes") else ""))
        atual = reg["oficial"]["status"] if reg.get("oficial") else None, reg["parceiro"]["status"]
        for canal, de, para in (("oficial", anterior[0], atual[0]), ("parceiro", anterior[1], atual[1])):
            if de != para and para is not None and de is not None:
                reg["mudancas"].append({"canal": canal, "de": de, "para": para, "em": agora})
        reg["mudancas"] = reg["mudancas"][-12:]
    saida = {"_leia": "Gerado por scripts/vendas.py. status: a_venda | em_breve | esgotado | desconhecido. 'mudancas' guarda as últimas transições (a tarefa de alertas usa 'para' == 'a_venda').", **vendas}
    ARQ.write_text(json.dumps(saida, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Pronto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
