#!/usr/bin/env python3
"""Rascunhos editoriais por IA para eventos novos (modelo AirOps do SeatPick: IA escreve, pessoa revisa).

Como usar:
  1. Em data/eventos-pendentes.json, cadastre só o mínimo de cada evento novo:
     {"id": 395343, "data": "2027-02-14", "tipo": "football", "local": "Camp Nou",
      "cidade": "Barcelona", "competicao": "La Liga", "times": ["FC Barcelona", "Real Madrid"]}
     (concertos: "artista" no lugar de "times"; "slug" é opcional).
  2. Rode python scripts/ia_rascunhos.py (ou o workflow "Rascunhos por IA").
  3. Leia radar/rascunhos-ia.md: cada evento vem com título, painel, introdução e "como chegar" em PT/EN/ES,
     horário local quando achado, e as fontes usadas. Cada fato marcado "conferir" precisa ser checado.
  4. Copie a entrada aprovada de data/rascunhos-ia.json para data/eventos.json (completando img/banner)
     e rode o gerador. Nada entra no site sem esse passo manual.

Segredo: ANTHROPIC_API_KEY. Custo: até 5 buscas por evento.
"""
import datetime as dt
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ia  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODIGO = {"football": 1000, "tennis": 1001, "nba": 1002, "f1": 1003, "rugby": 1020, "concert": 0}

SISTEMA = """Você é redator de um guia independente de ingressos (MyTickets Tours) em português do Brasil, inglês e espanhol.
Estilo da casa: frases curtas, fatos concretos, nada de adjetivo vazio, nada de "oficial" (o site não é bilheteria)
e nenhuma promessa sobre preço ou disponibilidade. Pesquise na web para confirmar horário e transporte até o local
e use só o que encontrar em fontes confiáveis (site do clube, da liga, do estádio, do transporte público)."""

PROMPT = """Evento a preparar:
{ev}

Pesquise e devolva SÓ um JSON com estas chaves:
{{
 "titulo": {{"pt": "...", "en": "...", "es": "..."}},          // ex.: "FC Barcelona x Real Madrid" / "FC Barcelona vs Real Madrid"
 "painel": {{"pt": "...", "en": "...", "es": "..."}},          // MAIÚSCULAS, até 24 caracteres, ex.: "BARCELONA X R. MADRID"
 "cidade": {{"pt": "...", "en": "...", "es": "..."}},
 "pais": {{"pt": "...", "en": "...", "es": "..."}},
 "intro": {{"pt": "...", "en": "...", "es": "..."}},           // 2 frases: o que é o jogo/show e por que é procurado
 "chegar": {{"pt": ["...", "..."], "en": [...], "es": [...]}}, // 2 dicas: linhas e estações reais; quanto tempo antes chegar
 "hora": "HH:MM ou vazio",                                      // horário local, só se confirmado em fonte
 "inicio": "ISO 8601 com fuso ou vazio",
 "fontes": ["url", ...],
 "conferir": ["fato que precisa ser checado por uma pessoa", ...]
}}"""


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def slug_de(p):
    if p.get("slug"):
        return p["slug"]
    base = p.get("artista") or "-vs-".join(p.get("times", [])) or p.get("competicao", "evento")
    return f"{slugify(base)}-{p['data']}"


def montar(p, r):
    """Junta o mínimo cadastrado com o rascunho, no formato de data/eventos.json."""
    ev = {"slug": slug_de(p), "id": p["id"], "data": p["data"], "tipo": p["tipo"], "esporte_tipo": CODIGO.get(p["tipo"], 0),
          "img": p.get("img", ""), "titulo": r["titulo"], "painel": r["painel"],
          "competicao": {"nome": p.get("competicao", "")}, "local": p["local"],
          "cidade": dict(r["cidade"]), "pais": r["pais"], "intro": r["intro"], "chegar": r["chegar"]}
    if p.get("times"):
        ev["times"] = [{"nome": t} for t in p["times"]]
    if p.get("artista"):
        ev["artista"] = {"nome": p["artista"], "dock": f"/dock/music/{slugify(p['artista'])}"}
    if r.get("hora"):
        ev["hora"] = r["hora"]
    if r.get("inicio"):
        ev["inicio"] = r["inicio"]
    ev["conferido"] = ""  # preencher com a data em que uma pessoa conferiu data e hora no parceiro
    ev["_ia"] = {"gerado": dt.date.today().isoformat(), "modelo": ia.MODELO, "fontes": r.get("fontes", []),
                 "conferir": r.get("conferir", [])}
    return ev


def main():
    arq_p = os.path.join(RAIZ, "data", "eventos-pendentes.json")
    try:
        pendentes = json.load(open(arq_p, encoding="utf-8")).get("eventos", [])
    except (OSError, ValueError):
        pendentes = []
    existentes = {e["slug"] for e in json.load(open(os.path.join(RAIZ, "data", "eventos.json"), encoding="utf-8"))["eventos"]}
    pendentes = [p for p in pendentes if slug_de(p) not in existentes]
    if not pendentes:
        print("Nenhum evento pendente em data/eventos-pendentes.json.")
        return
    if not ia.ativo():
        print("ANTHROPIC_API_KEY ausente: rascunhos não gerados.")
        return
    arq_r = os.path.join(RAIZ, "data", "rascunhos-ia.json")
    try:
        feitos = {e["slug"]: e for e in json.load(open(arq_r, encoding="utf-8"))}
    except (OSError, ValueError):
        feitos = {}
    for p in pendentes:
        if slug_de(p) in feitos and "--refazer" not in sys.argv:
            continue
        try:
            r = ia.perguntar(PROMPT.format(ev=json.dumps(p, ensure_ascii=False)), sistema=SISTEMA, buscas=5, max_tokens=3000)
            dados = ia.json_da_resposta(r["texto"])
            dados["fontes"] = list(dict.fromkeys(dados.get("fontes", []) + [c["url"] for c in r["citacoes"] if not c.get("so_resultado")]))
            feitos[slug_de(p)] = montar(p, dados)
            print(f"Rascunho pronto: {slug_de(p)}")
        except (RuntimeError, ValueError, KeyError) as erro:
            print(f"Falhou em {slug_de(p)}: {erro}")
    json.dump(list(feitos.values()), open(arq_r, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    out = [f"# Rascunhos por IA — {dt.date.today().isoformat()}", "",
           "Revise cada evento, confira os itens marcados e só então copie a entrada de data/rascunhos-ia.json para "
           "data/eventos.json (sem a chave _ia, completando img, banner e conferido).", ""]
    for ev in feitos.values():
        out += [f"## {ev['titulo']['pt']} — {ev['data']}", "",
                f"- Painel: {ev['painel']['pt']} / {ev['painel']['en']} / {ev['painel']['es']}",
                f"- Horário: {ev.get('hora') or 'não confirmado'}", "", f"**PT:** {ev['intro']['pt']}", "",
                "Como chegar: " + " ".join(ev["chegar"]["pt"]), "", f"**EN:** {ev['intro']['en']}", "", f"**ES:** {ev['intro']['es']}", ""]
        if ev["_ia"]["conferir"]:
            out += ["Conferir:"] + [f"- [ ] {x}" for x in ev["_ia"]["conferir"]] + [""]
        out += ["Fontes:"] + [f"- {u}" for u in ev["_ia"]["fontes"]] + [""]
    open(os.path.join(RAIZ, "radar", "rascunhos-ia.md"), "w", encoding="utf-8").write("\n".join(out))
    print("Revisão em radar/rascunhos-ia.md")


if __name__ == "__main__":
    main()
