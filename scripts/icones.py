"""Gera os ícones do site (favicon, Apple touch icon, ícones do manifest e logo da Organization).

Desenho: ingresso amarelo (cor de sinalização do site) com as iniciais MT em azul-noite.
Uso: python scripts/icones.py   (também é chamado pelo gerar_paginas.py)
Saída: favicon.ico, favicon.svg, apple-touch-icon.png, assets/icons/icon-192.png,
       assets/icons/icon-512.png, assets/icons/maskable-512.png, assets/img/logo-512.png
"""
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
AMARELO = (255, 196, 0)
NOITE = (11, 23, 38)
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="14" fill="#FFC400"/>
<path d="M10 20a4 4 0 0 1 4-4h36a4 4 0 0 1 4 4v7a5 5 0 0 0 0 10v7a4 4 0 0 1-4 4H14a4 4 0 0 1-4-4v-7a5 5 0 0 0 0-10z" fill="#0B1726"/>
<text x="32" y="40" text-anchor="middle" font-family="Arial Narrow, Impact, Helvetica, Arial, sans-serif" font-weight="900" font-size="22" fill="#FFC400" letter-spacing="1">MT</text>
</svg>
"""


def desenhar(tam, margem_fracao=0.0, maskable=False):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    raio = tam * 0.22
    if maskable:  # área segura do Android: o fundo preenche tudo, o desenho fica no centro
        d.rectangle([0, 0, tam, tam], fill=AMARELO)
    else:
        d.rounded_rectangle([0, 0, tam - 1, tam - 1], radius=raio, fill=AMARELO)
    m = tam * (0.16 + margem_fracao)
    x0, y0, x1, y1 = m, tam * 0.27 + margem_fracao * tam, tam - m, tam * 0.73 - margem_fracao * tam
    d.rounded_rectangle([x0, y0, x1, y1], radius=tam * 0.06, fill=NOITE)
    r = tam * 0.075
    cy = (y0 + y1) / 2
    d.ellipse([x0 - r, cy - r, x0 + r, cy + r], fill=AMARELO)
    d.ellipse([x1 - r, cy - r, x1 + r, cy + r], fill=AMARELO)
    fonte = ImageFont.truetype(FONTE, int(tam * 0.30))
    d.text((tam / 2, cy), "MT", font=fonte, fill=AMARELO, anchor="mm")
    return im


def gerar():
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("Pillow não instalado: ícones não gerados (pip install pillow).")
        return
    (RAIZ / "assets" / "icons").mkdir(parents=True, exist_ok=True)
    (RAIZ / "favicon.svg").write_text(SVG, encoding="utf-8")
    desenhar(180).save(RAIZ / "apple-touch-icon.png", optimize=True)
    desenhar(192).save(RAIZ / "assets" / "icons" / "icon-192.png", optimize=True)
    desenhar(512).save(RAIZ / "assets" / "icons" / "icon-512.png", optimize=True)
    desenhar(512, margem_fracao=0.08, maskable=True).save(RAIZ / "assets" / "icons" / "maskable-512.png", optimize=True)
    desenhar(512).convert("RGB").save(RAIZ / "assets" / "img" / "logo-512.png", optimize=True)
    base = desenhar(64)
    base.save(RAIZ / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    desenhar(32).save(RAIZ / "assets" / "icons" / "favicon-32.png", optimize=True)


if __name__ == "__main__":
    gerar()
    print("Ícones gerados.")
