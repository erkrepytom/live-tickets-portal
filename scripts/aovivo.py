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
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import videos as V  # noqa: E402  (nota_evento, canal_id_da_reserva, UA, _json_depois)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANTES = datetime.timedelta(hours=4)    # a janela é larga porque o eventos.json guarda a hora local, sem fuso
DEPOIS = datetime.timedelta(hours=5)


def quando_do_evento(ev):
    """Horário do evento em UTC aproximado (o eventos.json guarda a hora local, sem fuso)."""
    h, m = (ev.get("hora") or "20:00").split(":")[:2]
    return datetime.datetime.fromisoformat(ev["data"]).replace(
        hour=int(h), minute=int(m), tzinfo=datetime.timezone.utc)


def eventos_na_janela(eventos, agora):
    """Eventos cujo horário está por acontecer ou acabou de passar."""
    dentro = []
    for ev in eventos:
        try:
            quando = quando_do_evento(ev)
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
            if titulo:
                vistos.add(vid)
                achados.append({"yt": vid, "titulo": titulo, "selo_vivo": _marcado_ao_vivo(no)})
        for v in no.values():
            _colher_ao_vivo(v, achados, vistos)
    elif isinstance(no, list):
        for v in no:
            _colher_ao_vivo(v, achados, vistos)


def _pagina(url):
    req = urllib.request.Request(url, headers={"User-Agent": V.UA, "Accept-Language": "pt-BR,pt;q=0.9"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")


def ao_vivo_agora(canal_id):
    """O atalho /channel/<id>/live: quando o canal está transmitindo, essa página É o vídeo ao vivo
    (o canonical aponta para watch?v=...). Quando não está, cai na página do canal e não devolve nada."""
    try:
        html = _pagina(f"https://www.youtube.com/channel/{canal_id}/live")
    except Exception as exc:
        print(f"  ! /live de {canal_id} indisponível: {exc}")
        return []
    m = re.search(r'<link rel="canonical" href="https://www\.youtube\.com/watch\?v=([A-Za-z0-9_-]{11})"', html)
    if not m:
        return []
    t = re.search(r'<meta property="og:title" content="([^"]{1,120})"', html)
    return [{"yt": m.group(1), "titulo": (t.group(1) if t else ""), "selo_vivo": True}]


def transmissoes_do_canal(canal_id):
    """Candidatos a transmissão ao vivo: primeiro o atalho /live, depois as abas /streams e /videos.
    O selo da aba é só um indício; quem confirma é a página de incorporação, em estado()."""
    achados, vistos = [], set()
    for item in ao_vivo_agora(canal_id):
        vistos.add(item["yt"])
        achados.append(item)
    for aba in ("streams", "videos"):
        try:
            html = _pagina(f"https://www.youtube.com/channel/{canal_id}/{aba}")
        except Exception as exc:
            print(f"  ! aba /{aba} de {canal_id} indisponível: {exc}")
            continue
        dados = V._json_depois(html, "ytInitialData")
        if dados is None:
            continue
        parciais = []
        _colher_ao_vivo(dados, parciais, vistos)
        parciais.sort(key=lambda a: not a["selo_vivo"])
        achados += parciais[:4]
    return achados[:8]


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
        tipos = r.get("tipos") or []            # vazio = o canal serve para qualquer tipo de evento
        alvos = [ev for ev in eventos if not tipos or ev.get("tipo") in tipos]
        if not alvos:
            continue
        try:
            lives = transmissoes_do_canal(cid)
        except Exception as exc:
            print(f"  ! aba /streams de {r.get('canal','?')} indisponível: {exc}")
            continue
        print(f"· {r.get('canal','?')}: {len(lives)} transmissão(ões) recentes para conferir")
        for live in lives:
            ev = max(alvos, key=lambda x: V.nota_evento(live["titulo"], "", x), default=None)
            if ev is None or V.nota_evento(live["titulo"], "", ev) < 2:
                continue
            situacao, confirmado_vivo = estado(live["yt"])
            if situacao == "ok" and not confirmado_vivo:
                continue        # transmissão encerrada: vira vídeo comum, não é faixa AO VIVO
            if situacao == "geo" and not (confirmado_vivo or live["selo_vivo"]):
                continue        # bloqueado por país e sem nenhum sinal de que está no ar
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
            if any(a["evento"] == ev["slug"] for a in achados):
                continue        # um evento, uma transmissão: a primeira que passou na conferência
            achados.append({"yt": live["yt"], "titulo": live["titulo"], "canal": r.get("canal", ""),
                            "idioma": r.get("idioma", "pt"), "evento": ev["slug"],
                            "regiao": r.get("regiao", ""), "checado": situacao,
                            "desde": agora.isoformat(timespec="seconds")})
            print(f"+ {live['yt']} ({r.get('canal','?')}) ao vivo em {ev['slug']} [{situacao}]")
    # vários jogos ao mesmo tempo é o caso normal de fim de semana: o site mostra todos,
    # e quem começou primeiro aparece primeiro.
    ordem = {ev["slug"]: quando_do_evento(ev) for ev in eventos}
    achados.sort(key=lambda a: ordem.get(a["evento"], datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)))
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
        V.aviso(f"{nome}: {len(lives)} transmissão(ões) recentes na aba /streams.")
        for live in lives[:5]:
            situacao, vivo = estado(live["yt"])
            V.aviso(f"   {live['yt']} [{situacao}{', AO VIVO' if vivo else ''}"
                    f"{', selo' if live['selo_vivo'] else ''}] {live['titulo'][:70]}")
    return 0


def rodada(agora, eventos, dados_videos):
    """Uma passada: procura, grava data/aovivo.json e diz se a lista mudou."""
    arq = os.path.join(RAIZ, "data", "aovivo.json")
    try:
        with open(arq, encoding="utf-8") as f:
            antigo = json.load(f)
    except (OSError, ValueError):
        antigo = {}

    na_janela = eventos_na_janela(eventos, agora)
    if not na_janela:
        achados = []
        print("Nenhum evento na janela de jogo agora.")
    else:
        print("Na janela: " + ", ".join(ev["slug"] for ev in na_janela))
        achados = procurar(dados_videos, na_janela, agora)
        # havendo jogo na janela, o que mais estiver no ar vira opção extra na faixa
        achados += transmissoes_das_vitrines(agora, {t["yt"] for t in achados})

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
    return mudou


def _git(*args, falha_ok=False):
    r = subprocess.run(("git",) + args, cwd=RAIZ, capture_output=True, text=True)
    saida = (r.stdout + r.stderr).strip()
    if saida:
        print(f"  git {' '.join(args)}: {saida[:300]}")
    if r.returncode and not falha_ok:
        raise RuntimeError(f"git {' '.join(args)} falhou")
    return r.returncode


def publicar():
    """Dentro do vigia: manda a mudança para o repositório e pede o deploy, sem esperar a rodada acabar."""
    _git("config", "user.name", "aovivo-bot")
    _git("config", "user.email", "actions@users.noreply.github.com")
    _git("add", "data/aovivo.json")
    if _git("diff", "--cached", "--quiet", falha_ok=True) == 0:
        return
    _git("commit", "-m", "Faixa AO VIVO: atualiza as transmissões no ar")
    _git("pull", "--rebase", "-q", falha_ok=True)
    if _git("push", "-q", falha_ok=True):
        print("  ! não deu para enviar agora; a próxima volta tenta de novo.")
        return
    r = subprocess.run(["gh", "workflow", "run", "pages.yml"], cwd=RAIZ, capture_output=True, text=True)
    print(f"  deploy pedido: {(r.stdout + r.stderr).strip()[:200]}")


def ha_evento_ate(eventos, agora, horas):
    """Tem jogo na janela agora, ou começando dentro das próximas N horas?"""
    limite = agora + datetime.timedelta(hours=horas)
    for ev in eventos:
        try:
            quando = quando_do_evento(ev)
        except Exception:
            continue
        if quando - ANTES <= limite and agora <= quando + DEPOIS:
            return True
    return False


def vigiar(minutos, eventos, dados_videos):
    """O agendamento do GitHub engasga em frequência alta, então uma rodada por hora fica aqui dentro
    olhando de 3 em 3 minutos: a faixa acompanha o jogo mesmo quando o cron de 10 minutos atrasa."""
    fim = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=minutos)
    while True:
        agora = datetime.datetime.now(datetime.timezone.utc)
        if rodada(agora, eventos, dados_videos):
            publicar()
        sobra = (fim - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        if sobra < 180:
            break
        # sem jogo nenhum pela frente nesta hora, não vale segurar o runner
        proximos = [ev for ev in eventos
                    if quando_do_evento(ev) - ANTES <= fim and agora <= quando_do_evento(ev) + DEPOIS]
        if not proximos:
            print("Nada por vir nesta hora; o vigia encerra.")
            break
        time.sleep(min(180, sobra))
    # o agendamento de poucos minutos do GitHub não é confiável; se ainda há jogo pela frente,
    # o próprio vigia chama o próximo turno antes de encerrar.
    if ha_evento_ate(eventos, datetime.datetime.now(datetime.timezone.utc), 6) and os.environ.get("GITHUB_ACTIONS"):
        r = subprocess.run(["gh", "workflow", "run", "aovivo-vigia.yml"], cwd=RAIZ, capture_output=True, text=True)
        print(f"Próximo turno do vigia pedido: {(r.stdout + r.stderr).strip()[:160]}")
    return 0


def transmissoes_das_vitrines(agora, ja_vistos):
    """Além dos eventos do site, o que os canais das vitrines (NBA, beisebol, shows) estiverem
    transmitindo agora. Serve para a faixa AO VIVO ter mais opções quando há jogo: o visitante
    escolhe o que assistir e cada opção leva ao ingresso daquela categoria."""
    try:
        with open(os.path.join(RAIZ, "data", "vitrines.json"), encoding="utf-8") as f:
            vitrines = json.load(f).get("vitrines", [])
    except (OSError, ValueError):
        return []
    achados = []
    for v in vitrines:
        for canal in v.get("canais", []):
            cid = V.canal_id_da_reserva({"handle": canal} if canal.startswith("@") else {"channel_id": canal})
            if not cid:
                continue
            for live in ao_vivo_agora(cid):
                if live["yt"] in ja_vistos:
                    continue
                situacao, confirmado = estado(live["yt"])
                if situacao != "ok" or not confirmado:
                    continue
                ja_vistos.add(live["yt"])
                achados.append({"yt": live["yt"], "titulo": live["titulo"], "canal": V.TITULO_CANAL.get(cid, canal.lstrip("@")),
                                "idioma": "pt", "evento": "", "categoria": v["id"], "regiao": "",
                                "checado": situacao, "desde": agora.isoformat(timespec="seconds")})
                print(f"+ {live['yt']} ({canal}) ao vivo na vitrine {v['id']}")
                break
    return achados


def main():
    agora = datetime.datetime.now(datetime.timezone.utc)
    with open(os.path.join(RAIZ, "data", "eventos.json"), encoding="utf-8") as f:
        eventos = json.load(f)["eventos"]
    with open(os.path.join(RAIZ, "data", "videos.json"), encoding="utf-8") as f:
        dados_videos = json.load(f)
    if "--agora" in sys.argv:
        return diagnostico(dados_videos)
    if "--vigiar" in sys.argv:
        i = sys.argv.index("--vigiar")
        minutos = int(sys.argv[i + 1]) if len(sys.argv) > i + 1 else 55
        return vigiar(minutos, eventos, dados_videos)
    rodada(agora, eventos, dados_videos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
