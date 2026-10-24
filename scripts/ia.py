#!/usr/bin/env python3
"""Chamada mínima à API da Anthropic (Claude), só com a biblioteca padrão, para os robôs de IA do site.

Usado por geo.py (presença em respostas de IA), ia_ctr.py (títulos e descrições) e ia_rascunhos.py
(rascunhos editoriais). Nenhum desses robôs publica nada: eles escrevem relatórios em radar/ para
uma pessoa revisar e decidir.

Chave: variável de ambiente ANTHROPIC_API_KEY (no GitHub, um segredo do repositório).
Modelo: ANTHROPIC_MODEL (padrão claude-sonnet-5-5: rápido e barato o bastante para rodar toda semana).
"""
import json
import os
import time
import urllib.error
import urllib.request

API = "https://api.anthropic.com/v1/messages"
MODELO = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
# Busca na web feita pela própria API (cobrada à parte: US$ 10 por 1.000 buscas, mais os tokens).
BUSCA = {"type": "web_search_20250305", "name": "web_search"}


def chave():
    return os.environ.get("ANTHROPIC_API_KEY", "").strip()


def ativo():
    """Sem chave, cada robô avisa e sai sem erro (o workflow não fica vermelho)."""
    return bool(chave())


def perguntar(prompt, sistema=None, buscas=0, max_tokens=2000, local=None, tentativas=3):
    """Envia uma pergunta e devolve {"texto", "citacoes": [{url, titulo}], "buscas", "uso"}.
    buscas > 0 liga a busca na web com esse limite por pergunta; local = {"country": "BR", ...}."""
    corpo = {"model": MODELO, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
    if sistema:
        corpo["system"] = sistema
    if buscas:
        ferramenta = dict(BUSCA, max_uses=buscas)
        if local:
            ferramenta["user_location"] = dict({"type": "approximate"}, **local)
        corpo["tools"] = [ferramenta]
    dados = json.dumps(corpo).encode("utf-8")
    for n in range(tentativas):
        req = urllib.request.Request(API, data=dados, method="POST", headers={
            "x-api-key": chave(), "anthropic-version": "2023-06-01", "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                resp = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as erro:
            corpo_erro = erro.read().decode("utf-8", "replace")[:300]
            if erro.code in (429, 500, 502, 503, 529) and n < tentativas - 1:
                time.sleep(10 * (n + 1))
                continue
            raise RuntimeError(f"API da Anthropic respondeu {erro.code}: {corpo_erro}") from erro
    textos, citacoes, vistos = [], [], set()
    for bloco in resp.get("content", []):
        if bloco.get("type") == "text":
            textos.append(bloco.get("text", ""))
            for c in bloco.get("citations") or []:
                if c.get("url") and c["url"] not in vistos:
                    vistos.add(c["url"])
                    citacoes.append({"url": c["url"], "titulo": c.get("title", "")})
        elif bloco.get("type") == "web_search_tool_result" and isinstance(bloco.get("content"), list):
            for r in bloco["content"]:
                if r.get("url") and r["url"] not in vistos:
                    vistos.add(r["url"])
                    citacoes.append({"url": r["url"], "titulo": r.get("title", ""), "so_resultado": True})
    uso = resp.get("usage", {})
    return {"texto": "".join(textos).strip(), "citacoes": citacoes,
            "buscas": uso.get("server_tool_use", {}).get("web_search_requests", 0), "uso": uso}


def json_da_resposta(texto):
    """Extrai o primeiro objeto JSON de uma resposta (o modelo às vezes cerca o JSON com ```)."""
    ini, fim = texto.find("{"), texto.rfind("}")
    if ini < 0 or fim <= ini:
        raise ValueError("a resposta não trouxe JSON")
    return json.loads(texto[ini:fim + 1])
