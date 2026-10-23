#!/usr/bin/env python3
"""Procura transmissão ao vivo liberada para os eventos do site e escreve data/aovivo.json.

A faixa "AO VIVO" das páginas em português lê esse arquivo no navegador: enquanto houver
transmissão, a faixa aparece; quando o jogo acaba, o robô esvazia o arquivo e a faixa some.

Regra de uso, que é o que mantém tudo dentro da lei:
- só entra vídeo do player oficial do YouTube, de canal que detém os direitos (data/videos.json → canais_reserva);
- só entra se o dono deixou a incorporação ligada ("playableInEmbed"); se ele desligou, o robô desiste;
- nada é baixado, regravado ou retransmitido: o que aparece é o player do YouTube, com o crédito do canal.

Roda de 5 em 5 minutos no GitHub Actions, mas só gasta rede nos dias de evento, dentro da
janela do jogo. À mão: python scripts/aovivo.py
"""
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import videos as V  # noqa: E402  (nota_evento, canal_id_da_reserva, UA, _json_depois)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANTES = datetime.timedelta(hours=4)    # a janela é larga porque o eventos.json guarda a hora local, sem fuso
DEPOIS = datetime.timedelta(hours=5)


def eventos_na_janela(eventos, agora):
    """Eventos cujo horário está por acontecer ou acabou de passar."""
    dentro = []
    for ev in eventos:
        try:
            h, m = (ev.get("hora") or "20:00").split(":")[:2]
            quando = datetime.datetime.fromisoformat(ev["data"]).replace(
                hour=int(h), minute=int(m), tzinfo=datetime.timezone.utc)
        except Exception:
            continue
        if quando - ANTES <= agora <= quando + DEPOIS:
            dentro.append(ev)
    return dentro


def _marcado_ao_vivo(no):
    try:
        bruto = json.dumps(no, ensure_ascii=False)[:6000]
    except Exception:
        return False
    return '"style":"LIVE"' in bruto or '"isLive":true' in bruto or '"iconType":"LIVE"' in bruto


def _colher_ao_vivo(no, achados, vistos):
    if isinstance(no, dict):
        vid = no.get("videoId") or no.get("contentId")
        if isinstance(vid, str) and re.fullmatch(r"[A-Za-z0-9_-]{11}", vid) and vid not in vistos:
            titulo = V._texto_de(no)
            if titulo and _marcado_ao_vivo(no):
                vistos.add(vid)
                achados.append({"yt": vid, "titulo": titulo})
        for v in no.values():
            _colher_ao_vivo(v, achados, vistos)
    elif isinstance(no, list):
        for v in no:
            _colher_ao_vivo(v, achados, vistos)


def transmissoes_do_canal(canal_id):
    """O que o canal está exibindo ao vivo agora, pela aba /streams."""
    req = urllib.request.Request(f"https://www.youtube.com/channel/{canal_id}/streams",
                                 headers={"User-Agent": V.UA, "Accept-Language": "pt-BR,pt;q=0.9"})
    with urllib.request.urlopen(req, timeout=25) as r:
        html = r.read().decode("utf-8", "replace")
    dados = V._json_depois(html, "ytInitialData")
    if dados is None:
        return []
    achados, vistos = [], set()
    _colher_ao_vivo(dados, achados, vistos)
    return achados[:10]


def estado(yt):
    """Lê a página de incorporação: ('ok'|'embed'|'geo'|'indisponivel'|'erro', ao_vivo)."""
    req = urllib.request.Request(f"https://www.youtube.com/embed/{yt}",
                                 headers={"User-Agent": V.UA, "Accept-Language": "pt-BR,pt;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            html = r.read().decode("utf-8", "replace")
    except Exception as exc:
        print(f"  ! não deu para checar {yt}: {exc}")
        return "erro", False
    seco = html.replace(" ", "")
    ao_vivo = '"isLiveNow":true' in seco or '"isLive":true' in seco
    if '"playableInEmbed":false' in seco:
        return "embed", ao_vivo
    if '"status":"UNPLAYABLE"' in seco or '"status":"ERROR"' in seco:
        motivo = (re.search(r'"reason":\{"simpleText":"(.{0,200}?)"', html)
                  or re.search(r'"reason":"(.{0,200}?)"', html))
        texto = (motivo.group(1) if motivo else "").lower()
        if any(p in texto for p in ("country", "país", "pais", "region", "território", "territorio")):
            return "geo", ao_vivo
        return "indisponivel", ao_vivo
    return "ok", ao_vivo


def procurar(dados_videos, eventos, agora):
    achados = []
    for r in dados_videos.get("canais_reserva", []):
        cid = V.canal_id_da_reserva(r)
        if not cid:
            print(f"  ! canal de reserva sem channel_id: {r.get('canal','?')}")
            continue
        try:
            lives = transmissoes_do_canal(cid)
        except Exception as exc:
            print(f"  ! aba /streams de {r.get('canal','?')} indisponível: {exc}")
            continue
        print(f"· {r.get('canal','?')}: {len(lives)} transmissão(ões) ao vivo no canal")
        for live in lives:
            ev = max(eventos, key=lambda x: V.nota_evento(live["titulo"], "", x), default=None)
            if ev is None or V.nota_evento(live["titulo"], "", ev) < 2:
                continue
            situacao, confirmado_vivo = estado(live["yt"])
            if situacao == "embed":
                print(f"  - {live['yt']}: o canal desligou a incorporação; fora.")
                continue
            if situacao == "geo" and not r.get("confiar_quando_geo"):
                print(f"  - {live['yt']}: bloqueado por país onde o robô roda; fora "
                      f"(ligue confiar_quando_geo no canal se a transmissão for legítima no Brasil).")
                continue
            if situacao in ("indisponivel", "erro"):
                print(f"  - {live['yt']}: {situacao}; fora.")
                continue
            achados.append({"yt": live["yt"], "titulo": live["titulo"], "canal": r.get("canal", ""),
                            "idioma": r.get("idioma", "pt"), "evento": ev["slug"],
                            "regiao": r.get("regiao", ""), "checado": situacao,
                            "desde": agora.isoformat(timespec="seconds")})
            print(f"+ {live['yt']} ({r.get('canal','?')}) ao vivo em {ev['slug']} [{situacao}]")
    return achados


def diagnostico(dados_videos):
    """python scripts/aovivo.py --agora: mostra o que os canais de reserva estão transmitindo
    agora e se cada transmissão poderia entrar no site. Não escreve nada."""
    for r in dados_videos.get("canais_reserva", []):
        nome = r.get("canal", "?")
        cid = V.canal_id_da_reserva(r)
        if not cid:
            V.aviso(f"{nome}: sem channel_id.", True)
            continue
        try:
            lives = transmissoes_do_canal(cid)
        except Exception as exc:
            V.aviso(f"{nome}: aba /streams indisponível ({exc}).", True)
            continue
        V.aviso(f"{nome}: {len(lives)} transmissão(ões) ao vivo agora.")
        for live in lives[:5]:
            situacao, vivo = estado(live["yt"])
            V.aviso(f"   {live['yt']} [{situacao}{', ao vivo' if vivo else ''}] {live['titulo'][:70]}")
    return 0


def main():
    agora = datetime.datetime.now(datetime.timezone.utc)
    arq = os.path.join(RAIZ, "data", "aovivo.json")
    try:
        with open(arq, encoding="utf-8") as f:
            antigo = json.load(f)
    except (OSError, ValueError):
        antigo = {}
    with open(os.path.join(RAIZ, "data", "eventos.json"), encoding="utf-8") as f:
        eventos = json.load(f)["eventos"]
    with open(os.path.join(RAIZ, "data", "videos.json"), encoding="utf-8") as f:
        dados_videos = json.load(f)
    if "--agora" in sys.argv:
        return diagnostico(dados_videos)

    na_janela = eventos_na_janela(eventos, agora)
    if not na_janela:
        achados = []
        print("Nenhum evento na janela de jogo agora.")
    else:
        print("Na janela: " + ", ".join(ev["slug"] for ev in na_janela))
        achados = procurar(dados_videos, na_janela, agora)

    # mantém o "desde" de quem já estava no ar, para o site mostrar há quanto tempo começou
    antes = {t["yt"]: t for t in antigo.get("transmissoes", [])}
    for t in achados:
        if t["yt"] in antes:
            t["desde"] = antes[t["yt"]].get("desde", t["desde"])

    novo = {"_leia": ("Escrito por scripts/aovivo.py. A faixa AO VIVO das páginas em português lê este arquivo. "
                      "Só entra transmissão do canal detentor dos direitos, pelo player oficial do YouTube e com a "
                      "incorporação liberada pelo dono. Lista vazia = nada no ar, e a faixa não aparece."),
            "atualizado": agora.isoformat(timespec="seconds"),
            "transmissoes": achados}

    mudou = [t["yt"] for t in achados] != [t["yt"] for t in antigo.get("transmissoes", [])]
    if mudou or not antigo:
        with open(arq, "w", encoding="utf-8") as f:
            json.dump(novo, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print(f"data/aovivo.json atualizado: {len(achados)} transmissão(ões).")
    else:
        print(f"Sem mudança ({len(achados)} transmissão(ões)); arquivo mantido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
