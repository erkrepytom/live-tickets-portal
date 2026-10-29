#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera os shorts verticais (1080x1920) dos eventos, com narração, a partir de
data/eventos.json — 100% open-source: Pillow (visual), Kokoro TTS (voz,
Apache-2.0), NumPy/SciPy (ambiência sintética) e FFmpeg (montagem).

Uso:
  python scripts/gerar_short.py <slug> [pt|en|es|todos]        # gera 1 ou 3 idiomas
  python scripts/gerar_short.py <slug> pt --sem-voz            # só para rascunho visual

Saída: assets/videos/short-<slug>.mp4 (PT), -en.mp4, -es.mp4

Regras do projeto respeitadas:
- nenhum vídeo sai mudo (--sem-voz existe só para pré-visualizar; avisa no console);
- falas cronometradas por cena (~2,5 palavras/s) com 0,25 s de folga;
- ambiência abaixa sob a voz (sidechaincompress) e o volume final vai a
  loudnorm I=-14:TP=-1.5;
- voz nativa por idioma (Kokoro: pf_dora PT-BR, af_heart EN, ef_dora ES).
"""
import json, os, subprocess, sys, tempfile, unicodedata
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
AMARELO = (255, 196, 0)          # --signal do site (#FFC400)
BRANCO = (255, 255, 255)
FONTE_BOLD = RAIZ / "scripts/fontes/DejaVuSansCondensed-Bold.ttf"
FONTE_REG = RAIZ / "scripts/fontes/DejaVuSansCondensed.ttf"

VOZES = {"pt": "pf_dora", "en": "af_heart", "es": "ef_dora"}
LANG_KOKORO = {"pt": "p", "en": "a", "es": "e"}
MES = {
    "pt": ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"],
    "en": ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"],
    "es": ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"],
}
T = {
    "pt": {"como_chegar": "COMO CHEGAR", "dica": "DICA", "guia": "GUIA COMPLETO",
           "cta_tit": "INGRESSOS COM\nGARANTIA DE ENTREGA",
           "cta_sub": "Setores, dicas e onde comprar\ncom segurança: mytickets.tours",
           "aviso": "Link de afiliado: o MyTickets Tours pode receber comissão.",
           "fala_cta": "Setores, dicas e onde comprar com segurança: tudo no guia completo em mytickets ponto tours."},
    "en": {"como_chegar": "GETTING THERE", "dica": "TIP", "guia": "FULL GUIDE",
           "cta_tit": "TICKETS WITH\nGUARANTEED DELIVERY",
           "cta_sub": "Sections, tips and where to buy\nsafely: mytickets.tours",
           "aviso": "Affiliate link: MyTickets Tours may earn a commission.",
           "fala_cta": "Sections, tips and where to buy safely: it is all in the full guide at mytickets dot tours."},
    "es": {"como_chegar": "CÓMO LLEGAR", "dica": "CONSEJO", "guia": "GUÍA COMPLETA",
           "cta_tit": "ENTRADAS CON\nENTREGA GARANTIZADA",
           "cta_sub": "Sectores, consejos y dónde comprar\ncon seguridad: mytickets.tours",
           "aviso": "Enlace de afiliado: MyTickets Tours puede recibir comisión.",
           "fala_cta": "Sectores, consejos y dónde comprar con seguridad: todo en la guía completa en mytickets punto tours."},
}


def idioma_de(valor, lang):
    """Campo que pode ser string ou {pt,en,es}."""
    if isinstance(valor, dict):
        return valor.get(lang) or valor.get("pt") or next(iter(valor.values()))
    return valor


def chip_horario(ev, lang):
    ini = datetime.fromisoformat(ev["inicio"])
    cidade = idioma_de(ev["cidade"], lang).upper()
    mes = MES[lang][ini.month - 1]
    if lang == "en":
        h = ini.strftime("%I:%M %p").lstrip("0").replace(":00 ", " ")
        return f"{mes} {ini.day} · {h} ({cidade})"
    hh = f"{ini.hour}H{ini.minute:02d}" if lang == "pt" else f"{ini.hour}:{ini.minute:02d}"
    return f"{ini.day} {mes} · {hh} ({cidade})"


def fala_abertura(ev, lang):
    tit = idioma_de(ev["titulo"], lang)
    local = ev["local"].split("(")[0].strip()
    cidade = idioma_de(ev["cidade"], lang)
    ini = datetime.fromisoformat(ev["inicio"])
    meses_pt = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
                "agosto", "setembro", "outubro", "novembro", "dezembro"]
    meses_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    meses_en = ["January", "February", "March", "April", "May", "June", "July",
                "August", "September", "October", "November", "December"]
    if lang == "pt":
        return f"{tit}, no {local}, em {cidade}, dia {ini.day} de {meses_pt[ini.month-1]}."
    if lang == "es":
        return f"{tit}, en el {local}, en {cidade}, el {ini.day} de {meses_es[ini.month-1]}."
    return f"{tit} at {local}, {cidade}, on {meses_en[ini.month-1]} {ini.day}."


def cenas_do_evento(ev, lang):
    """Roteiro: texto na tela + fala por cena."""
    t = T[lang]
    chegar = [idioma_de(x, lang) if isinstance(x, dict) else x for x in ev["chegar"][lang]] \
        if isinstance(ev["chegar"], dict) else ev["chegar"]
    headline2 = chegar[0].split(",")[0].split(".")[0].upper()
    resto2 = chegar[0][len(headline2):].lstrip(" ,.")
    corpo2 = (resto2[0].upper() + resto2[1:]) if resto2 else chegar[0]
    return [
        dict(chip=chip_horario(ev, lang), tit=idioma_de(ev["painel"], lang),
             corpo=idioma_de(ev["intro"], lang), fala=f"{fala_abertura(ev, lang)} {idioma_de(ev['intro'], lang)}"),
        dict(chip=t["como_chegar"], tit=headline2, corpo=corpo2, fala=chegar[0]),
        dict(chip=t["dica"], tit=None, corpo=chegar[1] if len(chegar) > 1 else chegar[0],
             fala=chegar[1] if len(chegar) > 1 else chegar[0]),
        dict(chip=t["guia"], tit=t["cta_tit"], corpo=None, destaque=t["cta_sub"],
             aviso=t["aviso"], fala=t["fala_cta"]),
    ]


# ---------- visual ----------

def quebra(draw, texto, fonte, max_w):
    linhas, atual = [], ""
    for p in texto.split():
        teste = (atual + " " + p).strip()
        if draw.textlength(teste, font=fonte) <= max_w:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def overlay_cena(cena, caminho):
    """PNG RGBA 1080x1920: gradiente escuro embaixo + chip + textos + marca."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    # gradiente inferior
    grad = Image.new("L", (1, 900))
    for y in range(900):
        grad.putpixel((0, y), int(235 * (y / 900) ** 1.4))
    im.paste(Image.new("RGBA", (W, 900), (5, 8, 12, 255)), (0, H - 900),
             grad.resize((W, 900)))
    f_chip = ImageFont.truetype(str(FONTE_BOLD), 34)
    f_tit = ImageFont.truetype(str(FONTE_BOLD), 86)
    f_corpo = ImageFont.truetype(str(FONTE_BOLD), 44)
    f_marca = ImageFont.truetype(str(FONTE_BOLD), 40)
    f_aviso = ImageFont.truetype(str(FONTE_REG), 28)
    x, y = 66, H - 760
    # chip amarelo
    txt = cena["chip"]
    tw = dr.textlength(txt, font=f_chip)
    dr.rounded_rectangle([x, y, x + tw + 48, y + 58], 29, fill=AMARELO)
    dr.text((x + 24, y + 11), txt, font=f_chip, fill=(27, 21, 0))
    y += 96
    if cena.get("tit"):
        for ln in cena["tit"].split("\n"):
            for l2 in quebra(dr, ln, f_tit, W - 2 * x):
                dr.text((x, y), l2, font=f_tit, fill=BRANCO)
                y += 96
        y += 10
    if cena.get("corpo"):
        for l2 in quebra(dr, cena["corpo"], f_corpo, W - 2 * x):
            dr.text((x, y), l2, font=f_corpo, fill=(235, 238, 242))
            y += 58
    if cena.get("destaque"):
        for ln in cena["destaque"].split("\n"):
            dr.text((x, y), ln, font=f_corpo, fill=AMARELO)
            y += 58
    # marca
    ym = H - 170
    dr.text((x, ym), "MYTICKETS", font=f_marca, fill=BRANCO)
    dr.text((x + dr.textlength("MYTICKETS", font=f_marca), ym), ".TOURS",
            font=f_marca, fill=AMARELO)
    if cena.get("aviso"):
        dr.text((x, ym + 54), cena["aviso"], font=f_aviso, fill=(200, 205, 210))
    im.save(caminho)


# ---------- áudio ----------

def tts_kokoro(falas, lang, pasta):
    """Gera 1 wav por fala; devolve [(arquivo, duração_s)]."""
    from kokoro import KPipeline
    import numpy as np, wave
    pipe = KPipeline(lang_code=LANG_KOKORO[lang], repo_id="hexgrad/Kokoro-82M")
    saidas = []
    for i, fala in enumerate(falas):
        pedacos = [audio for (_, _, audio) in pipe(fala, voice=VOZES[lang])]
        audio = np.concatenate(pedacos)
        arq = pasta / f"voz{i}.wav"
        with wave.open(str(arq), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
            w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
        saidas.append((arq, len(audio) / 24000))
    return saidas


def ambiencia(dur, arq):
    """Ruído 'de arquibancada' sintético: marrom filtrado com ondulação lenta."""
    import numpy as np
    from scipy.signal import butter, lfilter
    sr = 44100
    n = int(dur * sr)
    rng = np.random.default_rng(7)
    ruido = np.cumsum(rng.standard_normal(n)).astype("f4")
    ruido /= np.abs(ruido).max() + 1e-9
    b, a = butter(2, [120 / (sr / 2), 1200 / (sr / 2)], btype="band")
    ruido = lfilter(b, a, ruido).astype("f4")
    t = np.arange(n) / sr
    onda = 0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t) * np.sin(2 * np.pi * 0.047 * t + 1.3)
    ruido *= onda.astype("f4")
    ruido /= np.abs(ruido).max() + 1e-9
    import wave
    with wave.open(str(arq), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((ruido * 0.5 * 32767).astype("<i2").tobytes())


# ---------- montagem ----------

def montar(ev, lang, sem_voz=False):
    cenas = cenas_do_evento(ev, lang)
    tmp = Path(tempfile.mkdtemp(prefix=f"short-{ev['slug']}-{lang}-"))
    # 1) voz primeiro: a duração de cada cena segue a fala (+0,5 s de folga)
    if sem_voz:
        print("AVISO: --sem-voz é só pré-visualização; nenhum vídeo sai mudo.")
        duracoes = [5.0, 4.5, 4.5, 5.0]
        vozes = []
    else:
        vozes = tts_kokoro([c["fala"] for c in cenas], lang, tmp)
        duracoes = [max(d + 0.5, 3.5) for (_, d) in vozes]
    total = sum(duracoes)
    inicios = [sum(duracoes[:i]) for i in range(len(duracoes))]
    # 2) overlays
    for i, c in enumerate(cenas):
        overlay_cena(c, tmp / f"ov{i}.png")
    # 3) fundo com Ken Burns
    banner = RAIZ / "assets/img" / ev["banner"]
    frames_tot = int(total * FPS) + FPS
    fil = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
           f"crop={W}:{H},zoompan=z='1+0.0016*in':x='iw/2-(iw/zoom/2)':"
           f"y='ih/2-(ih/zoom/2)':d={frames_tot}:s={W}x{H}:fps={FPS},"
           f"format=yuv420p[bg];")
    ents = ["-loop", "1", "-i", str(banner)]
    atual = "bg"
    for i, (ini, dur) in enumerate(zip(inicios, duracoes)):
        ents += ["-loop", "1", "-t", f"{dur:.3f}", "-i", str(tmp / f"ov{i}.png")]
        fade_out = max(dur - 0.35, 0.1)
        fil += (f"[{i+1}:v]format=rgba,fade=t=in:st=0:d=0.35:alpha=1,"
                f"fade=t=out:st={fade_out:.3f}:d=0.35:alpha=1,"
                f"setpts=PTS-STARTPTS+{ini:.3f}/TB[ov{i}];"
                f"[{atual}][ov{i}]overlay=0:0:eof_action=pass[v{i}];")
        atual = f"v{i}"
    fil += f"[{atual}]trim=0:{total:.3f},setpts=PTS-STARTPTS[vout]"
    # 4) áudio: vozes posicionadas + ambiência com ducking + loudnorm
    n_ents = 1 + len(cenas)
    if not sem_voz:
        amb = tmp / "amb.wav"
        ambiencia(total, amb)
        for arq, _ in vozes:
            ents += ["-i", str(arq)]
        ents += ["-i", str(amb)]
        vozfil = ""
        rot = []
        for i, ini in enumerate(inicios):
            ms = int((ini + 0.25) * 1000)
            vozfil += f"[{n_ents+i}:a]aresample=44100,adelay={ms}|{ms}[d{i}];"
            rot.append(f"[d{i}]")
        vozfil += (f"{''.join(rot)}amix=inputs={len(rot)}:normalize=0[voz];"
                   f"[{n_ents+len(cenas)}:a]atrim=0:{total:.3f},volume=0.35[ambi];"
                   f"[ambi][voz]sidechaincompress=threshold=0.015:ratio=8:attack=40:release=600[duck];"
                   f"[duck][voz]amix=inputs=2:normalize=0,"
                   f"loudnorm=I=-14:TP=-1.5:LRA=9[aout]")
        fil = fil + ";" + vozfil
        mapa = ["-map", "[vout]", "-map", "[aout]"]
    else:
        fil += f";anullsrc=r=44100:cl=stereo,atrim=0:{total:.3f}[aout]"
        mapa = ["-map", "[vout]", "-map", "[aout]"]
    sufixo = {"pt": "", "en": "-en", "es": "-es"}[lang]
    saida = RAIZ / f"assets/videos/short-{ev['slug']}{sufixo}.mp4"
    cmd = (["ffmpeg", "-y", "-v", "error"] + ents +
           ["-filter_complex", fil] + mapa +
           ["-c:v", "libx264", "-preset", "medium", "-crf", "21", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart", "-t", f"{total:.3f}", str(saida)])
    subprocess.run(cmd, check=True)
    print(f"ok: {saida.relative_to(RAIZ)} ({total:.1f}s)")
    return saida


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sem_voz = "--sem-voz" in sys.argv
    if not args:
        sys.exit(__doc__)
    slug = args[0]
    langs = ["pt", "en", "es"] if (len(args) < 2 or args[1] == "todos") else [args[1]]
    dados = json.loads((RAIZ / "data/eventos.json").read_text(encoding="utf-8"))
    ev = next((e for e in dados["eventos"] if e["slug"] == slug), None)
    if not ev:
        sys.exit(f"slug não encontrado: {slug}")
    for lang in langs:
        montar(ev, lang, sem_voz=sem_voz)


if __name__ == "__main__":
    main()
