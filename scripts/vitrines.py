#!/usr/bin/env python3
"""Enche as vitrines de vídeo do fim da página inicial (NBA, beisebol e shows).

Para cada vitrine de data/vitrines.json, lê os vídeos recentes dos canais oficiais indicados,
confere na página de incorporação se o dono permite a exibição fora do YouTube e guarda os dois
primeiros que passarem. Nada é baixado nem copiado: o site mostra o player do YouTube com o crédito.

Roda junto do robô de vídeos (.github/workflows/videos.yml). À mão: python scripts/vitrines.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import videos as V  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def recentes(canal):
    """Vídeos recentes de um canal, pelo feed RSS e, quando o canal não serve feed, pela aba /videos."""
    cid = V.canal_id_da_reserva({"handle": canal} if canal.startswith("@") else {"channel_id": canal})
    if not cid:
        print(f"  ! não achei o canal {canal}")
        return "", []
    try:
        itens = V.ler_feed(cid)
    except Exception as exc:
        print(f"  ! feed de {canal} indisponível: {exc}")
        return "", []
    return V.TITULO_CANAL.get(cid, canal.lstrip("@")), itens


def encher(vitrine):
    """Escolhe os vídeos da vitrine. Mantém o que já está no ar quando ainda vale, para a página
    não mudar à toa; só troca quando o canal publica algo novo ou quando um vídeo sai do ar."""
    quantos = int(vitrine.get("n", 2))
    antigos = {v["yt"]: v for v in vitrine.get("videos", [])}
    escolhidos = []
    for canal in vitrine.get("canais", []):
        if len(escolhidos) >= quantos:
            break
        nome, itens = recentes(canal)
        for it in itens:
            if len(escolhidos) >= quantos:
                break
            if any(e["yt"] == it["yt"] for e in escolhidos):
                continue
            if V.permite_embed(it["yt"]) is not True:
                print(f"  - {it['yt']} ({nome}): não permite exibição fora do YouTube")
                continue
            escolhidos.append({"yt": it["yt"], "titulo": it["titulo"][:160], "canal": nome,
                               "publicado": it.get("publicado", "")})
            print(f"+ {vitrine['id']}: {it['yt']} ({nome}) {it['titulo'][:60]}")
    if not escolhidos and antigos:
        print(f"  = {vitrine['id']}: nada novo passou na conferência; mantém o que estava no ar")
        return False
    mudou = [v["yt"] for v in escolhidos] != [v["yt"] for v in vitrine.get("videos", [])]
    vitrine["videos"] = escolhidos
    return mudou


def main():
    arq = os.path.join(RAIZ, "data", "vitrines.json")
    with open(arq, encoding="utf-8") as f:
        dados = json.load(f)
    mudou = False
    for vitrine in dados.get("vitrines", []):
        print(f"· vitrine {vitrine['id']}")
        mudou = encher(vitrine) or mudou
    if mudou:
        with open(arq, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print("data/vitrines.json atualizado.")
    else:
        print("Sem mudança nas vitrines.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
