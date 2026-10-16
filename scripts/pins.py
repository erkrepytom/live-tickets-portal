"""Liga o site ao Pinterest.

Dois papéis:
1. gerar_imagens(): cria a arte vertical (1000x1500, proporção 2:3) de cada evento e guia, em PT/EN/ES,
   em assets/pins/. Roda junto com o gerador (gerar_paginas.py), então a arte já sobe com o site.
2. publicar (python scripts/pins.py publicar): roda no GitHub Actions depois de cada publicação do site.
   Cria um pin para cada evento ou guia novo e atualiza o pin quando o título, a data ou o texto mudam.
   Sem as credenciais do Pinterest, só mostra o que faria (modo de ensaio) e não chama a API.

Configuração em data/pinterest.json ("ativo", quadro de cada idioma, limite de pins novos por execução).
Credenciais, nos segredos do GitHub: PINTEREST_APP_ID, PINTEREST_APP_SECRET e PINTEREST_REFRESH_TOKEN.
O Pinterest troca o refresh token a cada renovação (validade de 60 dias). Com o segredo GH_PAT
(token do GitHub com permissão de escrever segredos neste repositório), o robô grava o token novo sozinho.
"""
import base64
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conteudo as C  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
FONTES = Path(__file__).resolve().parent / "fontes"
ESTADO = RAIZ / "data" / "pins.json"
CONFIG = RAIZ / "data" / "pinterest.json"
API = "https://api.pinterest.com/v5"
# O pin leva à página do evento no site (com os botões de afiliado), nunca direto ao /go/: o Pinterest trata
# páginas de redirecionamento como spam. A marca utm mostra no GA4 as visitas e cliques vindos do Pinterest.
UTM = "?utm_source=pinterest&utm_medium=social&utm_campaign=pins"
W, H = 1000, 1500
CORES = {"fundo": (15, 34, 54), "sinal": (255, 194, 14), "texto": (241, 244, 247), "mut": (151, 167, 185)}

TXT = {
 "pt": {"cta": "INGRESSOS + GUIA DE VIAGEM", "guia": "GUIA DE VIAGEM",
        "desc": "{t}: {d}, {loc}, {c}. Guia com como chegar, melhor setor, o que levar e onde comprar ingressos com garantia de entrega. Link de afiliado: o MyTickets Tours pode receber comissão.",
        "desc_guia": "{t}. {desc} Link de afiliado: o MyTickets Tours pode receber comissão.",
        "alt": "Arte do MyTickets Tours: {t}, {d}, {c}."},
 "en": {"cta": "TICKETS + TRAVEL GUIDE", "guia": "TRAVEL GUIDE",
        "desc": "{t}: {d}, {loc}, {c}. Guide to getting there, the best sections, what to bring and where to buy tickets with a delivery guarantee. Affiliate link: MyTickets Tours may earn a commission.",
        "desc_guia": "{t}. {desc} Affiliate link: MyTickets Tours may earn a commission.",
        "alt": "MyTickets Tours graphic: {t}, {d}, {c}."},
 "es": {"cta": "ENTRADAS + GUÍA DE VIAJE", "guia": "GUÍA DE VIAJE",
        "desc": "{t}: {d}, {loc}, {c}. Guía para llegar, el mejor sector, qué llevar y dónde comprar entradas con garantía de entrega. Enlace de afiliado: MyTickets Tours puede recibir una comisión.",
        "desc_guia": "{t}. {desc} Enlace de afiliado: MyTickets Tours puede recibir una comisión.",
        "alt": "Imagen de MyTickets Tours: {t}, {d}, {c}."},
}


def _g():
    import gerar_paginas as G  # import tardio: gerar_paginas também importa este módulo
    return G


def foto_local(ev):
    """Imagem local para a arte (as fotos do Unsplash não são baixadas aqui)."""
    for img in (ev.get("banner"), ev.get("img")):
        if img and not img.startswith("photo-") and (RAIZ / "assets" / "img" / img).exists():
            return img
    return None  # sem foto própria: a arte usa só tipografia (nunca a foto de outro esporte)


def candidatos(eventos):
    """Um pin por evento e por guia, em cada idioma."""
    G = _g()
    itens = []
    for ev in eventos:
        for lang in G.IDIOMAS:
            titulo, cidade = G.L(ev["titulo"], lang), G.L(ev["cidade"], lang)
            d = G.data_longa(ev["data"], lang)
            v = {"t": titulo, "d": d, "loc": C.local_curto(ev["local"]), "c": cidade}
            itens.append({"chave": f"{lang}/{ev['slug']}", "lang": lang, "data": ev["data"],
                          "titulo": C.titulo_evento(lang, titulo, ev["data"][:4], ev["local"])[:100],
                          "descricao": TXT[lang]["desc"].format(**v)[:800], "alt": TXT[lang]["alt"].format(**v)[:500],
                          "link": f"{G.BASE_URL}/{G.caminho_evento(lang, ev['slug'])}{UTM}",
                          "imagem": f"assets/pins/{lang}/{ev['slug']}.jpg", "foto": foto_local(ev), "selo": G.L(ev["competicao"]["nome"], lang),
                          "arte": (titulo, f"{G.data_num(ev['data'], lang).upper()} · {cidade.upper()}", TXT[lang]["cta"])})
    for nome, guia, foto in (("guia-europa", C.GUIA, "06-champions.jpg"), ("guia-barca", C.GUIA_BARCA, "04-la-liga.jpg")):
        for lang in G.IDIOMAS:
            pg = guia[lang]
            itens.append({"chave": f"{lang}/{nome}", "lang": lang, "data": "9999-12-31",
                          "titulo": pg["title"][:100], "descricao": TXT[lang]["desc_guia"].format(t=pg["h1"], desc=pg["desc"])[:800],
                          "alt": pg["title"][:500], "link": f"{G.BASE_URL}/{pg['path']}{UTM}",
                          "imagem": f"assets/pins/{lang}/{nome}.jpg", "foto": foto,
                          "arte": (pg["h1"], "", TXT[lang]["guia"])})
    return itens


# ---------------------------------------------------------------- arte

def _quebrar(draw, texto, fonte, largura):
    linhas, atual = [], ""
    for p in texto.split():
        teste = f"{atual} {p}".strip()
        if draw.textlength(teste, font=fonte) <= largura:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    return linhas + [atual]


def desenhar(item, destino):
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    altura_foto = 900
    negrito = str(FONTES / "DejaVuSansCondensed-Bold.ttf")
    img = Image.new("RGB", (W, H), CORES["fundo"])
    if item.get("foto"):
        foto = Image.open(RAIZ / "assets" / "img" / item["foto"]).convert("RGB")
        # Os banners antigos têm um degradê à esquerda: o recorte fica do lado direito.
        centro = (0.8, 0.5) if item["foto"][:2].isdigit() else (0.5, 0.5)
        img.paste(ImageOps.fit(foto, (W, altura_foto), method=Image.LANCZOS, centering=centro), (0, 0))
    else:
        # Sem foto: faixas diagonais na cor de destaque e o nome da competição em letras grandes.
        d0 = ImageDraw.Draw(img)
        for i in range(-H, W + H, 120):
            d0.polygon([(i, 0), (i + 46, 0), (i + 46 - altura_foto, altura_foto), (i - altura_foto, altura_foto)], fill=(22, 46, 72))
        selo = (item.get("selo") or "").upper()
        tam = 150
        while tam > 60 and d0.textlength(selo, font=ImageFont.truetype(negrito, tam)) > W - 120:
            tam -= 6
        f_s = ImageFont.truetype(negrito, tam)
        for k, ln in enumerate(_quebrar(d0, selo, f_s, W - 120)[:3]):
            d0.text((60, 200 + k * int(tam * 1.05)), ln, font=f_s, fill=CORES["sinal"])
    # transição suave da foto para o painel
    sombra = Image.new("L", (1, 260))
    for y in range(260):
        sombra.putpixel((0, y), int(255 * (y / 259) ** 1.6))
    img.paste(Image.new("RGB", (W, 260), CORES["fundo"]), (0, altura_foto - 260), sombra.resize((W, 260)))
    d = ImageDraw.Draw(img)
    titulo, linha2, cta = item["arte"]
    tam = 96
    while tam > 54:
        f_t = ImageFont.truetype(negrito, tam)
        linhas = _quebrar(d, titulo.upper(), f_t, W - 120)
        if len(linhas) <= 3:
            break
        tam -= 6
    y = 860
    for ln in linhas:
        d.text((60, y), ln, font=f_t, fill=CORES["texto"])
        y += int(tam * 1.08)
    tam2 = 44
    while tam2 > 26 and d.textlength(linha2, font=ImageFont.truetype(negrito, tam2)) > W - 120:
        tam2 -= 2
    if linha2:
        d.text((60, y + 22), linha2, font=ImageFont.truetype(negrito, tam2), fill=CORES["sinal"])
    f_c = ImageFont.truetype(negrito, 38)
    larg = d.textlength(cta, font=f_c) + 64
    yc = H - 230
    d.rounded_rectangle((60, yc, 60 + larg, yc + 84), radius=42, fill=CORES["sinal"])
    d.text((92, yc + 20), cta, font=f_c, fill=CORES["fundo"])
    f_m = ImageFont.truetype(negrito, 34)
    d.text((60, H - 100), "MYTICKETS", font=f_m, fill=CORES["texto"])
    d.text((60 + d.textlength("MYTICKETS", font=f_m), H - 100), ".TOURS", font=f_m, fill=CORES["sinal"])
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino, "JPEG", quality=80, optimize=True, progressive=True)


def gerar_imagens(eventos):
    """Chamado pelo gerador. Só redesenha a arte quando o texto ou a foto mudam."""
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("Pillow não instalado: arte do Pinterest não gerada (pip install pillow).")
        return 0
    marca = RAIZ / "assets" / "pins" / "_hash.json"
    try:
        antigo = json.loads(marca.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        antigo = {}
    novo, feitos = {}, 0
    for it in candidatos(eventos):
        h = hashlib.sha1(json.dumps([it["arte"], it["foto"], it.get("selo"), 4], ensure_ascii=False).encode()).hexdigest()[:12]
        novo[it["imagem"]] = h
        alvo = RAIZ / it["imagem"]
        if antigo.get(it["imagem"]) != h or not alvo.exists():
            desenhar(it, alvo)
            feitos += 1
    for velho in set(antigo) - set(novo):  # evento que saiu do site: a arte sai junto
        (RAIZ / velho).unlink(missing_ok=True)
    marca.parent.mkdir(parents=True, exist_ok=True)
    marca.write_text(json.dumps(novo, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return feitos


# ---------------------------------------------------------------- API

def _req(metodo, url, token=None, dados=None, form=None, basic=None):
    cab = {"Accept": "application/json"}
    corpo = None
    if dados is not None:
        corpo = json.dumps(dados).encode()
        cab["Content-Type"] = "application/json"
    if form is not None:
        corpo = urllib.parse.urlencode(form).encode()
        cab["Content-Type"] = "application/x-www-form-urlencoded"
    if token:
        cab["Authorization"] = f"Bearer {token}"
    if basic:
        cab["Authorization"] = "Basic " + base64.b64encode(basic.encode()).decode()
    r = urllib.request.Request(url, data=corpo, headers=cab, method=metodo)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}


def token_de_acesso():
    """Usa PINTEREST_ACCESS_TOKEN se existir; senão renova com o refresh token."""
    if os.environ.get("PINTEREST_ACCESS_TOKEN"):
        return os.environ["PINTEREST_ACCESS_TOKEN"]
    app, segredo, refresh = (os.environ.get(k, "") for k in ("PINTEREST_APP_ID", "PINTEREST_APP_SECRET", "PINTEREST_REFRESH_TOKEN"))
    if not (app and segredo and refresh):
        return None
    st, r = _req("POST", f"{API}/oauth/token", form={"grant_type": "refresh_token", "refresh_token": refresh}, basic=f"{app}:{segredo}")
    if st != 200 or "access_token" not in r:
        raise SystemExit(f"Pinterest recusou a renovação do token (HTTP {st}): {r.get('message', r)}")
    print(f"::add-mask::{r['access_token']}")
    novo = r.get("refresh_token")
    if novo and novo != refresh:
        print(f"::add-mask::{novo}")
        if os.environ.get("GH_PAT") and os.environ.get("GITHUB_REPOSITORY"):
            subprocess.run(["gh", "secret", "set", "PINTEREST_REFRESH_TOKEN", "--repo", os.environ["GITHUB_REPOSITORY"], "--body", novo],
                           env={**os.environ, "GH_TOKEN": os.environ["GH_PAT"]}, check=True, capture_output=True)
            print("Refresh token novo gravado no segredo PINTEREST_REFRESH_TOKEN.")
        else:
            print("::warning::O Pinterest emitiu um refresh token novo, mas não há GH_PAT para gravá-lo. "
                  "Gere outro token e atualize o segredo PINTEREST_REFRESH_TOKEN em até 60 dias.")
    return r["access_token"]


def _imagem_no_ar(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20) as r:
            return r.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def publicar():
    G = _g()
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    try:
        estado = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        estado = {}
    hoje = time.strftime("%Y-%m-%d")
    dados = json.loads((RAIZ / "data" / "eventos.json").read_text(encoding="utf-8"))
    eventos = sorted([x for x in dados["eventos"] if x["data"] >= hoje], key=lambda x: x["data"])
    quadros = cfg.get("quadros", {})
    token = token_de_acesso() if cfg.get("ativo") else None
    ensaio = token is None
    if ensaio:
        print("Modo de ensaio: Pinterest desligado em data/pinterest.json ou sem credenciais. Nada será publicado.")
    limite, novos, mudou = int(cfg.get("max_novos_por_execucao", 3)), 0, False
    for it in candidatos(eventos):
        quadro = quadros.get(it["lang"], "")
        imagem = f"{G.BASE_URL}/{it['imagem']}"
        corpo = {"title": it["titulo"], "description": it["descricao"], "link": it["link"], "alt_text": it["alt"]}
        h = hashlib.sha1(json.dumps([corpo, (RAIZ / it["imagem"]).stat().st_size if (RAIZ / it["imagem"]).exists() else 0],
                                    ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
        atual = estado.get(it["chave"])
        if atual and atual.get("hash") == h:
            continue
        if not quadro:
            print(f"- {it['chave']}: sem quadro configurado para '{it['lang']}', pulado.")
            continue
        if atual:  # pin já existe: atualiza título, descrição e link
            print(f"- atualizar {it['chave']} (pin {atual['id']})")
            if not ensaio:
                st, r = _req("PATCH", f"{API}/pins/{atual['id']}", token, {**corpo, "board_id": quadro})
                if st != 200:
                    print(f"  ::warning::falhou (HTTP {st}): {r.get('message', r)}")
                    continue
                estado[it["chave"]] = {**atual, "hash": h, "atualizado": hoje}
                mudou = True
            continue
        if novos >= limite:
            print(f"- {it['chave']}: fica para a próxima execução (limite de {limite} pins novos).")
            continue
        print(f"- criar {it['chave']} → {it['link']}")
        novos += 1
        if ensaio:
            continue
        if not _imagem_no_ar(imagem):
            print(f"  ::warning::imagem ainda não está no ar ({imagem}); tento na próxima execução.")
            continue
        st, r = _req("POST", f"{API}/pins", token, {**corpo, "board_id": quadro, "media_source": {"source_type": "image_url", "url": imagem}})
        if st not in (200, 201) or "id" not in r:
            print(f"  ::warning::falhou (HTTP {st}): {r.get('message', r)}")
            continue
        estado[it["chave"]] = {"id": r["id"], "hash": h, "criado": hoje}
        mudou = True
        time.sleep(2)
    if mudou:
        ESTADO.write_text(json.dumps(estado, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Pronto: {novos} pin(s) novo(s){' (ensaio)' if ensaio else ''}.")


def listar_quadros():
    """Mostra o ID de cada quadro do perfil, para preencher data/pinterest.json."""
    token = token_de_acesso()
    if not token:
        raise SystemExit("Defina PINTEREST_ACCESS_TOKEN (ou APP_ID, APP_SECRET e REFRESH_TOKEN) para listar os quadros.")
    st, r = _req("GET", f"{API}/boards?page_size=100", token)
    if st != 200:
        raise SystemExit(f"HTTP {st}: {r.get('message', r)}")
    for b in r.get("items", []):
        print(f"{b['id']}  {b.get('name', '')}  ({b.get('privacy', '')})")


if __name__ == "__main__":
    if sys.argv[1:] == ["publicar"]:
        publicar()
    elif sys.argv[1:] == ["quadros"]:
        listar_quadros()
    elif sys.argv[1:] == ["imagens"]:
        G = _g()
        d = json.loads((RAIZ / "data" / "eventos.json").read_text(encoding="utf-8"))
        print(gerar_imagens([x for x in d["eventos"] if x["data"] >= time.strftime("%Y-%m-%d")]), "arte(s) gerada(s).")
    else:
        print(__doc__)
