#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Versão "cinematográfica" dos vídeos de bonecos: cada cena mostra o que a narração diz
(cidade, estádio, mapa do metrô, multidão na estação, celular com golpe) com câmera
(zoom e deslocamento), transições, luzes e partículas. Só código: Pillow + Piper + FFmpeg.

Uso:
  python scripts/cinema_bonecos.py                    # todos os eventos futuros que ainda não têm vídeo
  python scripts/cinema_bonecos.py <slug> [--forcar]  # um evento (refaz o vídeo)
  python scripts/cinema_bonecos.py --roteiro <arquivo.json> <saida.mp4>   # roteiro escrito à mão

Um vídeo por evento, no idioma do público principal: espanhol para eventos na Espanha e na América
Latina hispânica, português para eventos no Brasil e inglês para os demais (público internacional).
O roteiro de cada evento é montado a partir de data/eventos.json e salvo em data/roteiros/<chave>.json;
um roteiro com "manual": true é respeitado e não é sobrescrito.

Saída: assets/videos/bonecos/<chave>.mp4 (versão leve para o site, ~1,5 MB) e o pôster
assets/img/bonecos/<chave>.webp. O gerador do site põe o vídeo na página do evento nos três idiomas.

Tipos de cena: cidade, estadio, mapa, fila, golpe, final. O cenário do estádio muda com o esporte
(gramado, quadra de basquete ou de tênis, circuito, palco). Bonecos e cenários são genéricos: cores dos
times, nunca escudo, logo, rosto ou estádio fiel. O vídeo não vende: termina chamando para comentar e seguir.
"""
import json, math, random, re, subprocess, sys, tempfile, wave
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bonecos as B  # noqa: E402
import gerar_short as GS   # noqa: E402
import conteudo as C        # noqa: E402

W, H, FPS = B.W, B.H, 30
S = B.S
F = B.F
AM = B.AMARELO
VOZES_PIPER = {
    "it": "vits-piper-it_IT-paola-medium/it_IT-paola-medium.onnx",
    "fr": "vits-piper-fr_FR-siwis-medium/fr_FR-siwis-medium.onnx",
    "pt": "vits-piper-pt_BR-faber-medium/pt_BR-faber-medium.onnx",
    "en": "vits-piper-en_US-lessac-medium/en_US-lessac-medium.onnx",
    "es": "vits-piper-es_ES-sharvard-medium/es_ES-sharvard-medium.onnx",
}


def lerp(a, b, k):
    return a + (b - a) * k


def mix(c1, c2, k):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(lerp(x, y, k)) for x, y in zip(a, b))


def ceu(c, topo, base):
    for y in range(0, 1920, 8):
        c.rect([0, y, 1080, y + 8], fill=mix(topo, base, y / 1920))


def estrelas(c, t, n=60, seed=3):
    r = random.Random(seed)
    for _ in range(n):
        x, y = r.uniform(0, 1080), r.uniform(0, 900)
        a = 0.5 + 0.5 * math.sin(t * r.uniform(1, 4) + x)
        rr = 2 + 2 * a
        c.oval([x - rr, y - rr, x + rr, y + rr], fill="#ffffff" if a > 0.6 else "#8a93b5")


def skyline(c, t, base_y=1250, catedral=False):
    """Cidade genérica ao anoitecer com uma catedral de pináculos (silhueta, sem monumento fiel)."""
    r = random.Random(11)
    x = -20
    while x < 1100:
        w = r.randint(70, 150)
        h = r.randint(180, 480)
        c.rect([x, base_y - h, x + w, 1920], fill="#1b2238")
        for wy in range(int(base_y - h + 30), base_y, 46):
            for wx in range(int(x + 14), int(x + w - 20), 34):
                if r.random() < 0.45:
                    acesa = math.sin(t * 0.8 + wx * 0.07 + wy) > -0.6
                    c.rect([wx, wy, wx + 16, wy + 22], fill="#ffd77a" if acesa else "#2a3354")
        x += w + r.randint(4, 18)
    if not catedral:
        c.rect([0, base_y, 1080, 1920], fill="#10162a")
        return
    # catedral genérica de pináculos
    cx = 540
    c.rect([cx - 220, base_y - 330, cx + 220, 1920], fill="#2a2f4a")
    for i in range(-5, 6):
        px = cx + i * 40
        ph = 420 + (160 if i == 0 else 60 * (1 - abs(i) / 5))
        c.d.polygon([((px - 12) * S, (base_y - 300) * S), ((px + 12) * S, (base_y - 300) * S), (px * S, (base_y - ph) * S)], fill="#2a2f4a")
    c.oval([cx - 9, base_y - 600 - 18, cx + 9, base_y - 600], fill=AM)  # estatueta dourada no topo
    c.rect([0, base_y, 1080, 1920], fill="#10162a")


def estadio(c, t, cores, luz=1.0, cy=1050, esporte="football"):
    """Arena genérica vista de cima: arquibancada com torcida nas cores dos times, refletores e o piso do esporte."""
    if esporte == "f1":
        return circuito(c, t, cores, cy)
    if esporte == "concert":
        return palco(c, t, cores, cy)
    c.oval([40, cy - 520, 1040, cy + 520], fill="#2b3350")
    for anel in range(5):
        rx, ry = 480 - anel * 40, 490 - anel * 40
        for k in range(70):
            a = k / 70 * 2 * math.pi + anel * 0.2
            x, y = 540 + math.cos(a) * rx, cy + math.sin(a) * ry
            cor = cores[0] if math.cos(a) < 0 else cores[1]
            pis = math.sin(t * 6 + k + anel) > 0.7
            c.oval([x - 9, y - 9, x + 9, y + 9], fill="#ffffff" if pis else cor)
    linha = "#e8f5e9"
    if esporte == "nba":
        c.rrect([250, cy - 300, 830, cy + 300], 20, fill="#c98e4f")
        for i in range(12):
            c.line([(250 + i * 48, cy - 300), (250 + i * 48, cy + 300)], 2, fill="#b97d40")
        c.rrect([270, cy - 280, 810, cy + 280], 6, outline=linha, width=5)
        c.line([(270, cy), (810, cy)], 5, fill=linha)
        c.oval([490, cy - 50, 590, cy + 50], outline=linha, width=5)
        for sy in (-1, 1):
            y0, y1 = sorted((cy + sy * 280, cy + sy * 160))
            c.d.rectangle([470 * S, y0 * S, 610 * S, y1 * S], outline=linha, width=max(1, int(5 * S)))
    elif esporte == "tennis":
        c.rrect([250, cy - 300, 830, cy + 300], 20, fill="#2f6f3e")
        c.rect([330, cy - 260, 750, cy + 260], fill="#2a62a8")
        c.d.rectangle([330 * S, (cy - 260) * S, 750 * S, (cy + 260) * S], outline=linha, width=max(1, int(5 * S)))
        c.line([(380, cy - 260), (380, cy + 260)], 4, fill=linha)
        c.line([(700, cy - 260), (700, cy + 260)], 4, fill=linha)
        c.line([(380, cy - 130), (700, cy - 130)], 4, fill=linha)
        c.line([(380, cy + 130), (700, cy + 130)], 4, fill=linha)
        c.line([(540, cy - 130), (540, cy + 130)], 4, fill=linha)
        c.line([(310, cy), (770, cy)], 8, fill="#f4f4f4")  # rede
    else:
        c.rrect([250, cy - 300, 830, cy + 300], 30, fill="#2f8f46")
        for i in range(6):
            if i % 2:
                c.rect([250, cy - 300 + i * 100, 830, cy - 200 + i * 100], fill="#2a8040")
        c.rrect([270, cy - 280, 810, cy + 280], 10, outline=linha, width=5)
        c.line([(270, cy), (810, cy)], 5, fill=linha)
        if esporte == "rugby":
            for sy in (-1, 1):  # traves em H
                y = cy + sy * 270
                c.line([(510, y), (570, y)], 6, fill="#ffffff")
                c.line([(510, y), (510, y - sy * 50)], 6, fill="#ffffff")
                c.line([(570, y), (570, y - sy * 50)], 6, fill="#ffffff")
        else:
            c.oval([480, cy - 60, 600, cy + 60], outline=linha, width=5)
    for (fx, fy) in ((90, cy - 520), (990, cy - 520), (90, cy + 470), (990, cy + 470)):
        c.rect([fx - 6, fy, fx + 6, fy + 120], fill="#9aa4b8")
        c.rrect([fx - 40, fy - 30, fx + 40, fy + 10], 6, fill="#fff6d0" if luz > 0.5 else "#555c70")


def circuito(c, t, cores, cy=1050):
    """Circuito genérico com três carros correndo (cores de exemplo, sem equipe real)."""
    c.rrect([60, cy - 540, 1020, cy + 540], 80, fill="#1f6b3a")
    pista = [(200, cy - 420), (880, cy - 420), (900, cy - 80), (600, cy + 40), (880, cy + 300),
             (820, cy + 440), (220, cy + 440), (160, cy)]
    fech = pista + [pista[0]]
    c.line(fech, 90, fill="#3b3f4a", joint="curve")
    c.line(fech, 6, fill="#ffffff", joint="curve")
    for i in range(0, 12):  # zebras na largada
        c.rect([480 + i * 10, cy - 460, 490 + i * 10, cy - 380], fill="#ffffff" if i % 2 else "#e0252e")
    seg = [math.dist(fech[i], fech[i + 1]) for i in range(len(pista))]
    total = sum(seg)
    for k in range(3):
        d = (t * 520 + k * 140) % total
        i = 0
        while d > seg[i]:
            d -= seg[i]
            i += 1
        f = d / seg[i]
        x = lerp(fech[i][0], fech[i + 1][0], f)
        y = lerp(fech[i][1], fech[i + 1][1], f)
        cor = PALETA_CARROS[k]
        c.rrect([x - 34, y - 18, x + 34, y + 18], 10, fill=cor)
        c.oval([x - 12, y - 12, x + 12, y + 12], fill="#111111")
    for k in range(60):  # arquibancada
        x = 120 + k * 14
        pis = math.sin(t * 5 + k) > 0.6
        c.oval([x - 6, cy - 520, x + 6, cy - 508], fill="#ffffff" if pis else cores[k % 2])


PALETA_CARROS = ["#00b3a4", "#e0252e", "#ff7a1a"]


def palco(c, t, cores, cy=1050):
    """Palco com treliça, feixes de luz coloridos e a plateia com lanternas de celular."""
    c.rect([0, cy - 560, 1080, cy + 560], fill="#0a0d18")
    c.rect([140, cy - 520, 940, cy - 220], fill="#1c2236")
    c.rect([120, cy - 560, 960, cy - 520], fill="#5b6378")
    for x in (120, 940):
        c.rect([x, cy - 560, x + 20, cy - 200], fill="#5b6378")
    c.rect([100, cy - 220, 980, cy - 180], fill="#2e3550")
    for i in range(5):
        a = math.sin(t * 1.5 + i) * 0.5
        x0 = 200 + i * 170
        x1 = x0 + math.sin(a) * 400
        cor = [AM, "#ff5c8a", "#5ce1ff", "#7cff8a", "#b38bff"][i]
        c.d.polygon([(x0 * S, (cy - 520) * S), ((x1 - 70) * S, (cy + 400) * S), ((x1 + 70) * S, (cy + 400) * S)],
                    fill=mix(cor, "#0a0d18", 0.75))
    r = random.Random(1)
    for k in range(220):
        x, y = r.uniform(40, 1040), r.uniform(cy - 140, cy + 540)
        luz = math.sin(t * 3 + k) > 0.55
        c.oval([x - 9, y - 9, x + 9, y + 9], fill="#fff6c8" if luz else cores[k % 2])


def cone_luz(img, t, k):
    """Feixes de luz dos refletores (camada aditiva)."""
    if k <= 0:
        return img
    cam = Image.new("RGB", img.size, (0, 0, 0))
    d = ImageDraw.Draw(cam)
    for i, (x0, y0) in enumerate(((90, 500), (990, 500))):
        a = 0.25 * math.sin(t * 0.8 + i)
        x1 = 540 + math.sin(a) * 300
        d.polygon([(x0 * S, y0 * S), ((x1 - 260) * S, 1500 * S), ((x1 + 260) * S, 1500 * S)], fill=(int(60 * k), int(56 * k), int(36 * k)))
    cam = cam.filter(ImageFilter.GaussianBlur(18))
    from PIL import ImageChops
    return ImageChops.add(img, cam)


def particulas(c, t, cores, n=50, seed=9, vel=1.0):
    r = random.Random(seed)
    for _ in range(n):
        x = r.uniform(0, 1080)
        y = (r.uniform(0, 1920) - t * r.uniform(120, 380) * vel) % 1920
        rr = r.uniform(4, 10)
        c.oval([x - rr, y - rr, x + rr, y + rr], fill=r.choice(cores))


def fogos(c, t, seed=4):
    r = random.Random(seed)
    for i in range(5):
        t0 = i * 0.7
        k = ((t - t0) % 2.6) / 1.3
        if k > 1:
            continue
        cx, cy = r.uniform(150, 930), r.uniform(250, 700)
        cor = r.choice(["#ffc400", "#ff5c8a", "#5ce1ff", "#ffffff", "#7cff8a"])
        for j in range(16):
            a = j / 16 * 2 * math.pi
            rr = 40 + k * 180
            x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr + k * k * 60
            s = 9 * (1 - k) + 2
            c.oval([x - s, y - s, x + s, y + s], fill=cor)


def mapa(c, t, cena, cor_linha="#a27bd6"):
    """Mapa do metrô animado: a linha se desenha, o trem anda e o pino do estádio cai no destino."""
    c.rect([0, 0, 1080, 1920], fill="#eef0e6")
    r = random.Random(2)
    for _ in range(26):  # quarteirões
        x, y = r.uniform(-50, 1000), r.uniform(300, 1700)
        c.rrect([x, y, x + r.uniform(90, 220), y + r.uniform(70, 180)], 14, fill="#e1e4d6")
    c.line([(0, 1500), (1080, 1350)], 26, fill="#ffffff")
    c.line([(300, 250), (420, 1920)], 22, fill="#ffffff")
    c.oval([700, 1450, 1000, 1700], fill="#cfe3c4")  # parque
    pts = [(880, 1500), (760, 1260), (620, 1120), (470, 960), (360, 780), (260, 560)]
    k = B.ease((t - 0.3) / 2.2)
    seg = k * (len(pts) - 1)
    desenhado = [pts[0]]
    for i in range(1, len(pts)):
        if seg >= i:
            desenhado.append(pts[i])
        elif seg > i - 1:
            f = seg - (i - 1)
            desenhado.append((lerp(pts[i - 1][0], pts[i][0], f), lerp(pts[i - 1][1], pts[i][1], f)))
            break
    if len(desenhado) > 1:
        c.line(desenhado, 26, fill=cor_linha, joint="curve")
    for i, p in enumerate(pts):
        if seg >= i - 0.01:
            c.oval([p[0] - 22, p[1] - 22, p[0] + 22, p[1] + 22], fill="#ffffff", outline=cor_linha, width=8)
    tx, ty = desenhado[-1]
    c.rrect([tx - 40, ty - 26, tx + 40, ty + 26], 14, fill=cor_linha)
    c.rect([tx - 26, ty - 14, tx - 6, ty + 2], fill="#ffffff")
    c.rect([tx + 6, ty - 14, tx + 26, ty + 2], fill="#ffffff")
    c.rrect([pts[0][0] - 90, pts[0][1] + 40, pts[0][0] + 90, pts[0][1] + 100], 20, fill="#ffffff", outline="#2e3a52", width=3)
    c.text((pts[0][0], pts[0][1] + 70), cena.get("origem", "Centro"), F(34), fill="#2e3a52", anchor="mm")
    # linha e destino
    c.rrect([66, 300, 230, 380], 40, fill=cor_linha)
    c.text((148, 340), cena["linha"], F(52), fill="#ffffff", anchor="mm")
    kp = B.back((t - 2.4) / 0.5)
    if kp > 0.02:
        px, py = pts[-1][0], pts[-1][1] - 120 * kp
        c.oval([px - 60 * kp, py - 60 * kp, px + 60 * kp, py + 60 * kp], fill="#e0252e")
        c.d.polygon([((px - 40 * kp) * S, (py + 30 * kp) * S), ((px + 40 * kp) * S, (py + 30 * kp) * S), (px * S, (py + 110 * kp) * S)], fill="#e0252e")
        c.oval([px - 24 * kp, py - 24 * kp, px + 24 * kp, py + 24 * kp], fill="#ffffff")
        w = c.tlen(cena["destino"], F(44)) + 60
        c.rrect([px - w / 2 + 120, py - 170, px + w / 2 + 120, py - 90], 40, fill="#1a2234")
        c.text((px + 120, py - 130), cena["destino"], F(44), fill="#ffffff", anchor="mm")


def fila(c, t, cena, cores):
    """Estação lotada depois do jogo: a fila cresce, o relógio corre e o boneco espera tranquilo."""
    c.rect([0, 0, 1080, 1920], fill="#1a2030")
    c.rect([0, 1350, 1080, 1920], fill="#2a3048")
    c.rrect([120, 380, 960, 560], 20, fill="#e0e4ee")
    c.text((540, 470), cena["placa"], F(64), fill="#1a2234", anchor="mm")
    c.rrect([66, 610, 270, 690], 40, fill="#a27bd6")
    c.text((168, 650), cena["linha"], F(46), fill="#ffffff", anchor="mm")
    n = int(4 + B.ease(t / 3) * 18)
    for i in range(n):
        x = 980 - (i % 6) * 95 - (i // 6) % 2 * 40
        y = 1250 - (i // 6) * 110
        B.boneco(c, x, y, 0.42, cores[i % len(cores)][0], cores[i % len(cores)][1], "", t + i * 0.3, braco=0.2 * math.sin(t * 5 + i))
    # relógio que corre 20 minutos
    k = B.ease((t - 0.8) / 2.5)
    cx, cy, r = 230, 860, 110
    c.oval([cx - r, cy - r, cx + r, cy + r], fill="#ffffff", outline=AM, width=12)
    a = -math.pi / 2 + k * (20 / 60) * 2 * math.pi * 6
    c.line([(cx, cy), (cx + math.cos(a) * 85, cy + math.sin(a) * 85)], 9, fill="#e0252e")
    c.line([(cx, cy), (cx + math.cos(-math.pi / 2 + k * 2.1) * 55, cy + math.sin(-math.pi / 2 + k * 2.1) * 55)], 12, fill="#1a2234")
    c.text((cx, cy + r + 50), f"+{int(k * 20)} min", F(52), fill=AM, anchor="mm")
    B.boneco(c, 250, 1480, 1.2, cores[0][0], cores[0][1], "", t, braco=0.9, estilo=cores[0][2])  # o esperto espera com calma
    c.rrect([140, 1250, 360, 1320], 30, fill="#ffffff")
    c.text((250, 1285), cena.get("balao", "relax"), F(38), fill="#1a2234", anchor="mm")


def celular(c, t, cena):
    """Celular com três sinais de golpe que recebem um carimbo vermelho, um de cada vez."""
    c.rect([0, 0, 1080, 1920], fill="#151b2b")
    x0, y0 = 190, 300
    c.rrect([x0, y0, x0 + 700, y0 + 1240], 70, fill="#0b0e16", outline="#3a4560", width=8)
    c.rrect([x0 + 30, y0 + 70, x0 + 670, y0 + 1180], 40, fill="#eef1f6")
    c.rrect([x0 + 280, y0 + 25, x0 + 420, y0 + 45], 10, fill="#222a3a")
    for i, (ic, txt) in enumerate(cena["sinais"]):
        st = 0.5 + i * cena.get("passo", 1.6)
        k = B.ease((t - st) / 0.4)
        if k <= 0:
            continue
        y = y0 + 130 + i * 330
        x = x0 + 60 + (1 - k) * 600
        c.rrect([x, y, x + 580, y + 270], 34, fill="#ffffff", outline="#d4d9e4", width=3)
        c.oval([x + 30, y + 75, x + 150, y + 195], fill=["#ff7a1a", "#2b3bd6", "#7b2cbf"][i % 3])
        c.text((x + 90, y + 135), ic, F(56), fill="#ffffff", anchor="mm")
        for j, ln in enumerate(B.quebra(c, txt, F(38), 380)):
            c.text((x + 180, y + 80 + j * 50), ln, F(38), fill="#1a2234")
        ks = B.back((t - st - 0.7) / 0.35)
        if ks > 0.05:  # carimbo
            cx, cy = x + 470, y + 200
            r = 70 * ks
            c.oval([cx - r, cy - r, cx + r, cy + r], fill="#e0252e")
            c.line([(cx - r * .45, cy - r * .45), (cx + r * .45, cy + r * .45)], 16 * ks, fill="#ffffff")
            c.line([(cx - r * .45, cy + r * .45), (cx + r * .45, cy - r * .45)], 16 * ks, fill="#ffffff")


def camera(img, t, dur, mov):
    """Zoom e deslocamento suaves (push-in, pull-out, pan)."""
    k = B.ease(t / max(dur, 0.1))
    z0, z1, dx, dy = mov
    z = lerp(z0, z1, k)
    if abs(z - 1) < 0.002 and not dx and not dy:
        return img
    w, h = W / z, H / z
    cx = min(max(W / 2 + dx * S * k, w / 2), W - w / 2)
    cy = min(max(H / 2 + dy * S * k, h / 2), H - h / 2)
    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    return img.resize((W, H), Image.BILINEAR, box=box)


def vinheta():
    """Máscara: 255 no centro (imagem inteira), escurece só as bordas."""
    g = Image.radial_gradient("L").resize((W, H))  # 0 no centro, 255 nas bordas
    return g.point(lambda v: 255 - int(max(0, v - 120) * 0.9))


def cartela(c, cena, t):
    """Título da cena em cartela com entrada lateral."""
    if cena.get("chip"):
        B.chip(c, cena["chip"], 150, B.ease(t / 0.5))
    if cena.get("titulo"):
        k = B.back((t - 0.15) / 0.6)
        if k > 0.05:
            linhas = B.quebra(c, cena["titulo"], F(80), 960)
            alt = len(linhas) * 92 + 50
            c.rrect([40, 240, 1040, 240 + alt], 28, fill="#0f1420")
            for i, ln in enumerate(linhas):
                c.text((540, 240 + 25 + 46 + i * 92), ln, F(80 * min(k, 1.1)), fill="#ffffff", anchor="mm")


def legenda_karaoke(c, fala, p):
    """Legenda em blocos de 4 palavras com a palavra falada destacada em amarelo."""
    pal = fala.split()
    pos = min(len(pal) - 1, int(B.clamp(p) * len(pal)))
    bi = pos // 4
    bloco = pal[bi * 4:(bi + 1) * 4]
    tam = 54
    while c.tlen(" ".join(bloco), F(tam)) > 940 and tam > 34:
        tam -= 2
    total = c.tlen(" ".join(bloco), F(tam))
    c.rrect([540 - total / 2 - 30, 1690, 540 + total / 2 + 30, 1784], 22, fill="#000000")
    x = 540 - total / 2
    for j, p_ in enumerate(bloco):
        cor = AM if bi * 4 + j == pos else "#ffffff"
        c.text((x, 1737), p_, F(tam), fill=cor, anchor="lm")
        x += c.tlen(p_ + " ", F(tam))


def cena_frame(cena, t, dur, base, cores):
    c = B.Tela(base)
    tipo = cena["tipo"]
    if tipo == "cidade":
        ceu(c, "#0b1030", "#e0706a")
        estrelas(c, t)
        lua_y = 420 - t * 10
        c.oval([780, lua_y, 900, lua_y + 120], fill="#fff3c4")
        skyline(c, t, catedral=cena.get("catedral", False))
        if len(cores) == 2:
            for i, (cor, cor2, est) in enumerate(cores):
                kx = B.ease((t - 0.6) / 0.9)
                x = 540 + (-1 if i == 0 else 1) * (230 + (1 - kx) * 700)
                B.boneco(c, x, 1440, 1.25, cor, cor2, "", t + i, braco=0.6 + 0.4 * math.sin(t * 4 + i), estilo=est, olhar=1 if i == 0 else -1)
            kv = B.back((t - 1.3) / 0.4)
            if kv > 0.05:
                c.oval([540 - 75 * kv, 1420 - 75 * kv, 540 + 75 * kv, 1420 + 75 * kv], fill=AM)
                c.text((540, 1420), "VS", F(66 * kv), fill="#0f1420", anchor="mm")
        else:
            n = len(cores)
            for i, (cor, cor2, est) in enumerate(cores):
                kx = B.back((t - 0.5 - i * 0.2) / 0.6)
                x = 540 + (i - (n - 1) / 2) * 300
                B.boneco(c, x, 1440, (1.6 if n == 1 else 1.05) * kx, cor, cor2, "" if n == 1 else i + 1, t + i,
                         braco=0.5 + 0.5 * math.sin(t * 5 + i), estilo=est)
            if cena.get("nome"):
                c.text((540, 1660 if n == 1 else 1620), cena["nome"], F(60), fill=AM, anchor="mm")
    elif tipo == "estadio":
        c.rect([0, 0, 1080, 1920], fill="#0d1222")
        esp = cena.get("esporte", "football")
        estadio(c, t, [cores[0][0], cores[-1][0]], esporte=esp)
        if esp not in ("f1", "concert"):
            for i, (cor, cor2, est) in enumerate(cores[:2]):  # bonecos entram em campo
                k = B.ease((t - 0.5 - i * 0.3) / 1.2)
                x = lerp(540, 430 + i * 220, k)
                y = lerp(1450, 1000, k)
                B.boneco(c, x, y, 0.7, cor, cor2, "", t + i, braco=0.8, estilo=est)
        elif esp == "concert":
            cor, cor2, est = cores[0]
            B.boneco(c, 540, 640, 0.8 * B.back((t - 0.4) / 0.6), cor, cor2, "", t, braco=0.9, estilo=est)
        for i, n in enumerate(cena.get("numeros", [])):  # títulos mundiais como estrelas sobre cada time
            k = B.back((t - 2.0 - i * 0.5) / 0.4)
            if k > 0.05:
                x = 300 + i * 480
                c.rrect([x - 150, 1330, x + 150, 1470], 30, fill="#0f1420", outline=cores[i][0], width=6)
                c.text((x, 1375), n[0], F(70 * min(k, 1.1)), fill=AM, anchor="mm")
                c.text((x, 1435), n[1], F(32), fill="#ffffff", anchor="mm")
    elif tipo == "mapa":
        mapa(c, t, cena)
    elif tipo == "fila":
        fila(c, t, cena, cores)
    elif tipo == "golpe":
        celular(c, t, cena)
    elif tipo == "final":
        c.rect([0, 0, 1080, 1920], fill="#090d1a")
        estrelas(c, t, 40, 8)
        fogos(c, t)
        estadio(c, t, [cores[0][0], cores[-1][0]], cy=1350, esporte=cena.get("esporte", "football"))
        particulas(c, t, [AM, "#ffffff", cores[0][0], cores[-1][0]], 40)
        k = B.back((t - 0.2) / 0.6)
        if k > 0.05:
            for i, ln in enumerate(B.quebra(c, cena["pergunta"], F(76), 960)):
                c.text((540, 330 + i * 92), ln, F(76 * min(k, 1.1)), fill="#ffffff", anchor="mm")
        if t > 1.0:
            k3 = B.back((t - 1.0) / 0.5)
            pul = 1 + 0.04 * math.sin(t * 8)
            w2 = (c.tlen(cena["cta"], F(58)) / 2 + 60) * k3 * pul
            h2 = 62 * k3 * pul
            c.rrect([540 - w2, 600 - h2, 540 + w2, 600 + h2], h2, fill=AM)
            c.text((540, 600), cena["cta"], F(58 * min(k3, 1.1)), fill="#0f1420", anchor="mm")
    if tipo != "final":
        cartela(c, cena, t)
    img = c.img
    if tipo in ("estadio", "final"):
        img = cone_luz(img, t, 1.0)
    img = camera(img, t, dur, cena.get("camera", (1.0, 1.08, 0, 0)))
    c2 = B.Tela(img)
    B.marca(c2)
    if cena.get("fonte"):
        c2.text((540, 1650), cena["fonte"], F(32, False), fill="#c8cede", anchor="mm")
    legenda_karaoke(c2, cena["fala"], t / max(0.1, dur - 0.3))
    return c2.img


def transicao(a, b, k):
    """Cortina diagonal com leve desfoque de movimento."""
    if k >= 1:
        return b
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    x = lerp(-W * 0.6, W * 1.6, B.ease(k))
    d.polygon([(x - W * 0.6, 0), (x, 0), (x - W * 0.3, H), (x - W * 0.9 - W, H), (-W * 2, 0)], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(10))
    return Image.composite(b, a, m)


def falar(textos, lang, pasta):
    from piper import PiperVoice
    voz = PiperVoice.load(str(GS.PIPER_DIR / VOZES_PIPER[lang]))
    out = []
    for i, tx in enumerate(textos):
        arq = pasta / f"v{i}.wav"
        with wave.open(str(arq), "wb") as w:
            voz.synthesize_wav(tx, w)
        with wave.open(str(arq)) as w:
            out.append((arq, w.getnframes() / w.getframerate()))
    return out


TX = {
    "en": {"jogo": "WHAT'S AT STAKE", "show": "THE SHOW", "chegar": "GETTING THERE", "dica": "LOCAL TIP", "golpe": "AVOID SCAMS",
           "centro": "City centre", "balao": "relax", "metro": "Metro", "cta": "Follow us",
           "perg_jogo": "Who wins? Tell us in the comments!", "perg_show": "Which song is a must? Comment!",
           "fim_jogo": "So, who wins? Tell us in the comments, and follow us for more.",
           "fim_show": "Which song is a must? Tell us in the comments, and follow us for more.",
           "sinais": [["$", "Bank transfer to a stranger"], ["%", "Price far too low"], ["QR", "Just a screenshot"]],
           "fala_golpe": "Avoid scams: no bank transfers to strangers, be wary of prices far too low, and of screenshots."},
    "es": {"jogo": "QUÉ SE JUEGA", "show": "EL CONCIERTO", "chegar": "CÓMO LLEGAR", "dica": "CONSEJO LOCAL", "golpe": "OJO CON LAS ESTAFAS",
           "centro": "Centro", "balao": "tranqui", "metro": "Metro", "cta": "Síguenos",
           "perg_jogo": "¿Quién gana? ¡Comenta!", "perg_show": "¿Qué canción no puede faltar?",
           "fim_jogo": "¿Quién gana? Cuéntanos en los comentarios y síguenos para más.",
           "fim_show": "¿Qué canción no puede faltar? Cuéntanos en los comentarios y síguenos para más.",
           "sinais": [["$", "Transferencia a un particular"], ["%", "Precio demasiado bajo"], ["QR", "Solo una captura"]],
           "fala_golpe": "Ojo con las estafas: nada de transferencias a particulares, desconfía de precios demasiado bajos y de las capturas."},
    "pt": {"jogo": "O QUE ESTÁ EM JOGO", "show": "O SHOW", "chegar": "COMO CHEGAR", "dica": "DICA DO LOCAL", "golpe": "CUIDADO COM GOLPE",
           "centro": "Centro", "balao": "de boa", "metro": "Metrô", "cta": "Siga a gente",
           "perg_jogo": "Quem vence? Comenta aí!", "perg_show": "Qual música não pode faltar?",
           "fim_jogo": "E aí, quem vence? Comenta aí e segue a gente pra mais.",
           "fim_show": "Qual música não pode faltar? Comenta aí e segue a gente pra mais.",
           "sinais": [["R$", "Pix para pessoa física"], ["%", "Preço baixo demais"], ["QR", "Só um print"]],
           "fala_golpe": "Cuidado com golpe: nada de Pix para pessoa física, desconfie de preço baixo demais e de print."},
}
HISPANOS = {"Spain", "Mexico", "Argentina", "Colombia", "Chile", "Peru", "Uruguay", "Paraguay", "Ecuador", "Bolivia",
            "Venezuela", "Costa Rica", "Panama", "Guatemala", "Honduras", "El Salvador", "Nicaragua",
            "Dominican Republic", "Cuba", "Puerto Rico"}
ROTEIROS = GS.RAIZ / "data/roteiros"
SAIDA_MP4 = GS.RAIZ / "assets/videos/bonecos"
SAIDA_IMG = GS.RAIZ / "assets/img/bonecos"
CRF_SITE = "30"


def idioma_publico(ev):
    """Idioma do público principal: espanhol na Espanha e na América hispânica, português no Brasil, inglês nos demais."""
    pais = ev["pais"]["en"]
    return "es" if pais in HISPANOS else ("pt" if pais == "Brazil" else "en")


def linha_transporte(txt, lang):
    m = re.search(r"\b(M\d|L\d{1,2}|RER [A-Z]|U\d|[A-Z]\d)\b", txt)
    return m.group(1) if m else TX[lang]["metro"]


def elenco_evento(ev, lang):
    if ev.get("artista"):
        return [["#7b2cbf", AM, "artista"]], ev["artista"]["nome"]
    times = ev.get("times") or []
    if len(times) == 2:
        a, b = (B.cor_time(B.L(x["nome"], "en")) for x in times)
        if B.parecidas(a[0], b[0]):
            b = (b[1], b[0])
        return [[*a, "atleta"], [*b, "atleta"]], ""
    estilo = "piloto" if ev["tipo"] == "f1" else "atleta"
    return [[*B.PALETA[i], estilo] for i in range(3)], ""


def roteiro_evento(ev):
    lang = idioma_publico(ev)
    tx = TX[lang]
    show = bool(ev.get("artista"))
    elenco, nome = elenco_evento(ev, lang)
    chegar = ev["chegar"][lang] if isinstance(ev["chegar"], dict) else ev["chegar"]
    contexto = B.frases_sem_venda(B.L(ev["intro"], lang)) or B.L(ev["intro"], lang).split(". ")[0] + "."
    local = C.local_curto(ev["local"])
    esporte = "concert" if show else ev["tipo"]
    cenas = [
        {"tipo": "cidade", "chip": GS.chip_horario(ev, lang), "titulo": B.L(ev["painel"], lang), "nome": nome,
         "camera": [1.12, 1.0, 0, 0], "fala": GS.fala_abertura(ev, lang)},
        {"tipo": "estadio", "esporte": esporte, "chip": B.L(ev["competicao"]["nome"], lang).upper()[:28] if not show else tx["show"],
         "titulo": tx["show"] if show else tx["jogo"], "camera": [1.0, 1.12, 0, -80], "fala": contexto},
        {"tipo": "mapa", "chip": tx["chegar"], "linha": linha_transporte(chegar[0], lang), "origem": tx["centro"],
         "destino": local[:22], "camera": [1.0, 1.1, -60, 40], "fala": chegar[0]},
    ]
    if len(chegar) > 1:
        cenas.append({"tipo": "fila", "chip": tx["dica"], "placa": local[:22], "linha": linha_transporte(chegar[0], lang),
                      "balao": tx["balao"], "camera": [1.08, 1.0, 0, 0], "fala": chegar[1]})
    cenas.append({"tipo": "golpe", "chip": tx["golpe"], "sinais": tx["sinais"], "passo": 1.6, "camera": [1.0, 1.06, 0, 0],
                  "fala": tx["fala_golpe"]})
    cenas.append({"tipo": "final", "esporte": esporte, "pergunta": tx["perg_show" if show else "perg_jogo"], "cta": tx["cta"],
                  "camera": [1.0, 1.05, 0, 0], "fala": tx["fim_show" if show else "fim_jogo"]})
    return {"evento": ev["slug"], "idioma": lang, "cores": elenco, "cenas": cenas}


def render(R, saida, crf="24", poster=None):
    cenas, lang = R["cenas"], R["idioma"]
    cores = [tuple(x) + (("atleta",) if len(x) == 2 else ()) for x in R["cores"]]
    tmp = Path(tempfile.mkdtemp(prefix="cinema-"))
    vz = falar([c["fala"] for c in cenas], lang, tmp)
    durs = [max(d + 0.7, 3.2) for _, d in vz]
    TR = 0.35  # duração da transição
    base = B.fundo()
    vin = vinheta()
    preto = Image.new("RGB", (W, H), (0, 0, 0))
    mudo = tmp / "mudo.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(mudo)],
                         stdin=subprocess.PIPE)
    ultimo = None
    capa = None
    for i, (cena, dur) in enumerate(zip(cenas, durs)):
        for f in range(int(dur * FPS)):
            t = f / FPS
            img = cena_frame(cena, t, dur, base, cores)
            img = Image.composite(img, preto, vin)
            if ultimo is not None and t < TR:
                img = transicao(ultimo, img, t / TR)
            if i == 0 and capa is None and t >= 2.0:
                capa = img.copy()
            p.stdin.write(img.tobytes())
            final = img
        ultimo = final
    p.stdin.close()
    p.wait()
    if poster:
        (capa or final).resize((360, 640)).save(poster, quality=72)
    total = sum(durs)
    amb = tmp / "amb.wav"
    GS.ambiencia(total, amb)
    inicios = [sum(durs[:i]) for i in range(len(durs))]
    ents = ["-i", str(mudo)] + sum((["-i", str(a)] for a, _ in vz), []) + ["-i", str(amb)]
    n = len(vz)
    fil = "".join(f"[{i + 1}:a]aresample=44100,adelay={int((ini + 0.3) * 1000)}|{int((ini + 0.3) * 1000)}[d{i}];" for i, ini in enumerate(inicios))
    fil += (f"{''.join(f'[d{i}]' for i in range(n))}amix=inputs={n}:normalize=0,asplit=2[v1][v2];"
            f"[{n + 1}:a]atrim=0:{total:.3f},volume=0.3[amb];[amb][v1]sidechaincompress=threshold=0.015:ratio=8:attack=40:release=600[duck];"
            f"[duck][v2]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[a]")
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", *ents, "-filter_complex", fil, "-map", "0:v", "-map", "[a]", "-c:v", "libx264",
                        "-profile:v", "main", "-preset", "slow", "-crf", crf, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "64k", "-ac", "1",
                        "-movflags", "+faststart", "-t", f"{total:.3f}", str(saida)], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-1500:])
    print(f"ok: {saida} ({lang}, {total:.1f}s, {Path(saida).stat().st_size // 1024} KB)")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--roteiro" in sys.argv:
        render(json.loads(Path(args[0]).read_text(encoding="utf-8")), args[1])
        return
    forcar = "--forcar" in sys.argv
    eventos = json.loads((GS.RAIZ / "data/eventos.json").read_text(encoding="utf-8"))["eventos"]
    if args:
        eventos = [e for e in eventos if e["slug"] == args[0]]
        forcar = True
        if not eventos:
            sys.exit(f"slug não encontrado: {args[0]}")
    else:
        hoje = date.today().isoformat()
        eventos = [e for e in eventos if e["data"] >= hoje and not e.get("encerrado")]
    if not args:  # apaga vídeo, pôster e roteiro de evento que saiu da agenda (o site fica leve)
        ativos = {C.chave_evento(e["slug"]) for e in eventos}
        for pasta, ext in ((SAIDA_MP4, ".mp4"), (SAIDA_IMG, ".webp"), (ROTEIROS, ".json")):
            for arq in pasta.glob(f"*{ext}"):
                if arq.stem in ativos:
                    continue
                if ext == ".json" and json.loads(arq.read_text(encoding="utf-8")).get("manual"):
                    continue
                arq.unlink()
                print(f"removido: {arq.relative_to(GS.RAIZ)}")
    ROTEIROS.mkdir(parents=True, exist_ok=True)
    SAIDA_MP4.mkdir(parents=True, exist_ok=True)
    SAIDA_IMG.mkdir(parents=True, exist_ok=True)
    for ev in eventos:
        chave = C.chave_evento(ev["slug"])
        arq_r = ROTEIROS / f"{chave}.json"
        R = json.loads(arq_r.read_text(encoding="utf-8")) if arq_r.exists() else {}
        mudou = False
        if not R.get("manual"):
            novo = roteiro_evento(ev)
            mudou = novo != R  # dados do evento mudaram: o vídeo é refeito
            R = novo
            arq_r.write_text(json.dumps(R, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        mp4 = SAIDA_MP4 / f"{chave}.mp4"
        if mp4.exists() and not forcar and not mudou:
            continue
        render(R, mp4, CRF_SITE, SAIDA_IMG / f"{chave}.webp")


if __name__ == "__main__":
    main()
