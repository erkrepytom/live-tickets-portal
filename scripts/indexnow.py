"""Avisa Bing, Yandex, Seznam e Naver (IndexNow) sobre as páginas que mudaram neste deploy.

Compara os sitemap-*.xml do commit atual com os do commit anterior e envia só as URLs
novas ou com lastmod diferente. Roda no GitHub Actions depois do deploy (pages.yml).

O Google não participa do IndexNow e não aceita mais "ping" de sitemap: para ele, o
caminho é o sitemap enviado uma vez no Search Console, que é relido sozinho.

Uso: python scripts/indexnow.py            (compara HEAD~1 com HEAD)
     python scripts/indexnow.py --tudo     (envia todas as URLs, útil na primeira vez)
"""
import json
import pathlib
import re
import subprocess
import sys
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from gerar_paginas import BASE_URL, INDEXNOW_KEY  # noqa: E402

PADRAO = re.compile(r"<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>")


def urls(texto):
    return dict(PADRAO.findall(texto))


def no_commit(ref, arquivo):
    r = subprocess.run(["git", "show", f"{ref}:{arquivo}"], cwd=RAIZ, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def main():
    if not INDEXNOW_KEY:
        print("INDEXNOW_KEY vazio; nada a fazer.")
        return
    atuais, anteriores = {}, {}
    for arq in sorted(RAIZ.glob("sitemap-*.xml")):
        atuais.update(urls(arq.read_text(encoding="utf-8")))
        anteriores.update(urls(no_commit("HEAD~1", arq.name)))
    if "--tudo" in sys.argv:
        lista = sorted(atuais)
    else:
        lista = sorted(u for u, d in atuais.items() if anteriores.get(u) != d)
    if not lista:
        print("Nenhuma página mudou; IndexNow não foi chamado.")
        return
    host = BASE_URL.split("://", 1)[1]
    corpo = json.dumps({"host": host, "key": INDEXNOW_KEY, "keyLocation": f"{BASE_URL}/{INDEXNOW_KEY}.txt",
                        "urlList": lista[:10000]}).encode("utf-8")
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=corpo,
                                 headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"IndexNow: {len(lista)} URLs enviadas, resposta {r.status}.")
    except urllib.error.HTTPError as erro:
        # 202 = aceito e a chave ainda está sendo validada; 4xx não deve derrubar o deploy.
        print(f"IndexNow respondeu {erro.code}: {erro.read()[:200]!r}")
    except OSError as erro:
        print(f"IndexNow indisponível agora ({erro}); o deploy segue normalmente.")


if __name__ == "__main__":
    main()
