#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Peças de desenho dos vídeos com bonecos (mascotes genéricos), usadas por scripts/cinema_bonecos.py:
tela escalada (desenho pensado em 1080x1920, saída 720x1280), boneco, bola, chip, quebra de texto,
cores de uniforme e o filtro que tira frases de venda do roteiro.

Regras: bonecos genéricos, só a cor do time como uniforme e o nome como texto. Nada de rosto de
atleta, escudo, logo de liga, de patrocinador ou de equipe.
"""
import math, re, sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gerar_short as GS  # noqa: E402  (voz, ambiência, textos de data e local)

RAIZ = GS.RAIZ
W, H, FPS = 720, 1280, 30
S = W / 1080  # escala: o desenho foi pensado em 1080x1920
AMARELO, FUNDO_TXT = "#ffc400", "#0f1420"
F_BOLD, F_REG = str(GS.FONTE_BOLD), str(GS.FONTE_REG)

# Cores de uniforme (só a cor, nunca o escudo). Times fora da lista ganham uma cor fixa pelo nome.
CORES = {
    "FC Barcelona": ("#a50044", "#004d98"), "Real Madrid": ("#f4f4f4", "#febe10"),
    "AC Milan": ("#e2231a", "#111111"), "Inter": ("#0068a8", "#111111"),
    "Manchester City": ("#6cabdd", "#1c2c5b"), "Italy": ("#0066cc", "#ffffff"),
    "France": ("#1f3f9e", "#ffffff"), "England": ("#f4f4f4", "#cf081f"),
    "Croatia": ("#e2231a", "#ffffff"), "Mexico": ("#006847", "#ffffff"),
    "Jamaica": ("#fed100", "#009b3a"), "Ireland": ("#169b62", "#ffffff"),
    "South Africa": ("#007a4d", "#ffb612"), "Los Angeles Lakers": ("#552583", "#fdb927"),
    "Boston Celtics": ("#007a33", "#ffffff"), "New York Knicks": ("#006bb6", "#f58426"),
    "Denver Nuggets": ("#0e2240", "#fec524"), "New Orleans Pelicans": ("#0c2340", "#c8102e"),
    "San Antonio Spurs": ("#c4ced4", "#111111"),
}
PALETA = [("#00b3a4", "#ffffff"), ("#e0252e", "#ffffff"), ("#2b3bd6", "#ffffff"),
          ("#ff7a1a", "#ffffff"), ("#7b2cbf", "#ffffff"), ("#18a957", "#ffffff")]

# Frases de venda ficam fora do vídeo (o canal ainda está formando público).
VENDA = re.compile(r"ingress|ticket|entrada|bilhete|boleto|esgot|sold out|agotad|vend|sale|compr|buy", re.I)

_fontes = {}


def F(px, bold=True):
    px = max(1, int(px * S))
    k = (px, bold)
    if k not in _fontes:
        _fontes[k] = ImageFont.truetype(F_BOLD if bold else F_REG, px)
    return _fontes[k]


def clamp(x):
    return max(0.0, min(1.0, x))


def ease(x):
    return 1 - (1 - clamp(x)) ** 3


def back(x):
    x = clamp(x)
    return 1 + 2.7 * (x - 1) ** 3 + 1.7 * (x - 1) ** 2


def L(v, lang):
    return GS.idioma_de(v, lang)


def parecidas(c1, c2):
    rgb = [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in (c1, c2)]
    return sum((x - y) ** 2 for x, y in zip(*rgb)) ** 0.5 < 110


def cor_time(nome_en):
    if nome_en in CORES:
        return CORES[nome_en]
    return PALETA[sum(map(ord, nome_en)) % len(PALETA)]


# ---------- desenho (coordenadas em 1080x1920, escaladas por S) ----------

class Tela:
    def __init__(self, fundo):
        self.img = fundo.copy()
        self.d = ImageDraw.Draw(self.img)

    def _p(self, pts):
        return [tuple(x * S for x in v) if isinstance(v, tuple) else v * S for v in pts]

    def rect(self, box, **k):
        if box[2] > box[0] and box[3] > box[1]:
            self.d.rectangle(self._p(box), **k)

    def rrect(self, box, r, **k):
        r = min(r, (box[2] - box[0]) / 2 - 0.5, (box[3] - box[1]) / 2 - 0.5)
        if r > 0:
            if "width" in k:
                k["width"] = max(1, int(k["width"] * S))
            self.d.rounded_rectangle(self._p(box), radius=r * S, **k)

    def oval(self, box, **k):
        if box[2] > box[0] and box[3] > box[1]:
            if "width" in k:
                k["width"] = max(1, int(k["width"] * S))
            self.d.ellipse(self._p(box), **k)

    def line(self, pts, w, **k):
        self.d.line(self._p(pts), width=max(1, int(w * S)), **k)

    def text(self, xy, txt, font, **k):
        self.d.text((xy[0] * S, xy[1] * S), txt, font=font, **k)

    def tlen(self, txt, font):
        return self.d.textlength(txt, font=font) / S


def fundo():
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        f = y / H
        d.line([(0, y), (W, y)], fill=(int(14 + 20 * f), int(18 + 18 * f), int(30 + 36 * f)))
    return im


def boneco(c, cx, cy, s, cor, cor2, num="", t=0.0, braco=0.0, estilo="atleta", olhar=0):
    """Mascote genérico. estilo: atleta (cabeça de brinquedo), piloto (capacete) ou artista (microfone)."""
    if s < 0.05:
        return
    cy += math.sin(t * 6) * 6 * s
    for lado in (-1, 1):
        ang = -0.9 + (braco * 2.2 if lado == 1 else 0)
        x0, y0 = cx + lado * 55 * s, cy + 70 * s
        x1, y1 = x0 + lado * math.cos(ang) * 75 * s, y0 - math.sin(ang) * 75 * s
        c.line([(x0, y0), (x1, y1)], 26 * s, fill=cor)
        c.oval([x1 - 18 * s, y1 - 18 * s, x1 + 18 * s, y1 + 18 * s], fill="#f4f4f4")
        if estilo == "artista" and lado == 1:
            c.line([(x1, y1), (x1 + 8 * s, y1 - 40 * s)], 8 * s, fill="#333333")
            c.oval([x1 - 6 * s, y1 - 66 * s, x1 + 22 * s, y1 - 38 * s], fill="#555555")
    c.rrect([cx - 62 * s, cy + 35 * s, cx + 62 * s, cy + 175 * s], 40 * s, fill=cor)
    c.rect([cx - 62 * s, cy + 95 * s, cx + 62 * s, cy + 110 * s], fill=cor2)
    if num != "":
        c.text((cx, cy + 142 * s), str(num), F(44 * s), fill=cor2 if cor2 != cor else "#ffffff", anchor="mm")
    piscar = 0.15 if (t * 10) % 31 < 1 else 1
    if estilo == "piloto":
        c.oval([cx - 75 * s, cy - 95 * s, cx + 75 * s, cy + 55 * s], fill=cor, outline="#ffffff", width=6 * s)
        c.rect([cx - 8 * s, cy - 95 * s, cx + 8 * s, cy - 40 * s], fill=cor2)
        c.rrect([cx - 55 * s, cy - 38 * s, cx + 55 * s, cy + 6 * s], 20 * s, fill="#141414")
        olho_y, olho_c = -16, "#ffffff"
    else:
        c.oval([cx - 72 * s, cy - 92 * s, cx + 72 * s, cy + 50 * s], fill="#f1f1f1", outline=cor, width=6 * s)
        c.d.arc([(cx - 30 * s + olhar * 8 * s) * S, (cy - 5 * s) * S, (cx + 30 * s + olhar * 8 * s) * S, (cy + 28 * s) * S],
                20, 160, fill="#222222", width=max(1, int(6 * s * S)))
        if estilo == "atleta":
            c.rrect([cx - 72 * s, cy - 92 * s, cx + 72 * s, cy - 55 * s], 18 * s, fill=cor)  # faixa na cor do time
        olho_y, olho_c = -22, "#222222"
    for ex in (-20, 20):
        ex += olhar * 8
        c.oval([cx + (ex - 9) * s, cy + (olho_y - 10 * piscar) * s, cx + (ex + 9) * s, cy + (olho_y + 10 * piscar) * s], fill=olho_c)


def bola(c, cx, cy, r, esporte, t=0.0):
    if r < 2:
        return
    if esporte == "rugby":
        c.oval([cx - r * 1.4, cy - r * 0.85, cx + r * 1.4, cy + r * 0.85], fill="#8a4b22", outline="#ffffff", width=4)
        c.line([(cx - r * 0.5, cy), (cx + r * 0.5, cy)], 5, fill="#ffffff")
    elif esporte == "nba":
        c.oval([cx - r, cy - r, cx + r, cy + r], fill="#e8742b", outline="#3a1b06", width=4)
        c.line([(cx - r, cy), (cx + r, cy)], 4, fill="#3a1b06")
        c.line([(cx, cy - r), (cx, cy + r)], 4, fill="#3a1b06")
    elif esporte == "tennis":
        c.oval([cx - r * 0.7, cy - r * 0.7, cx + r * 0.7, cy + r * 0.7], fill="#d7e83a")
    else:
        c.oval([cx - r, cy - r, cx + r, cy + r], fill="#ffffff", outline="#222222", width=4)
        a = t * 3
        pts = [(cx + math.cos(a + k * 1.2566) * r * 0.4, cy + math.sin(a + k * 1.2566) * r * 0.4) for k in range(5)]
        c.d.polygon([(x * S, y * S) for x, y in pts], fill="#222222")


def chip(c, txt, y=150, k=1.0):
    if k <= 0.02:
        return
    f = F(40)
    w = c.tlen(txt, f) + 56
    x = 66 - (1 - k) * 600
    c.rrect([x, y, x + w, y + 70], 35, fill=AMARELO)
    c.text((x + 28, y + 35), txt, f, fill=FUNDO_TXT, anchor="lm")


def quebra(c, txt, font, max_w):
    linhas, cur = [], ""
    for p in txt.split():
        teste = (cur + " " + p).strip()
        if c.tlen(teste, font) <= max_w or not cur:
            cur = teste
        else:
            linhas.append(cur)
            cur = p
    if cur:
        linhas.append(cur)
    return linhas


def cartao_texto(c, txt, y, t, cor="#ffffff", tam=52, entra=0.3):
    k = ease((t - entra) / 0.5)
    if k <= 0:
        return y
    f = F(tam)
    linhas = quebra(c, txt, f, 900)
    alt = len(linhas) * tam * 1.3 + 70
    x = 60 + (1 - k) * 1000
    c.rrect([x, y, x + 960, y + alt], 30, fill="#1a2234", outline="#2e3a52", width=3)
    for i, ln in enumerate(linhas):
        c.text((x + 40, y + 40 + i * tam * 1.3), ln, f, fill=cor)
    return y + alt


def legenda(c, fala, p):
    pal = fala.split()
    n = max(1, math.ceil(len(pal) / 4))
    i = min(n - 1, int(clamp(p) * n * 1.05))
    bloco = " ".join(pal[i * 4:(i + 1) * 4])
    tam = 56
    while c.tlen(bloco, F(tam)) > 940 and tam > 34:
        tam -= 2
    bw = c.tlen(bloco, F(tam))
    c.rrect([540 - bw / 2 - 28, 1680, 540 + bw / 2 + 28, 1776], 22, fill="#000000")
    c.text((540, 1728), bloco, F(tam), fill="#ffffff", anchor="mm")


def marca(c):
    c.text((1040, 60), "MYTICKETS.TOURS", F(30), fill="#8d97ab", anchor="ra")


# ---------- roteiro ----------

def frases_sem_venda(txt):
    frases = re.split(r"(?<=[.!?])\s+", txt.strip())
    return " ".join(f for f in frases if not VENDA.search(f)).strip()


