#!/usr/bin/env python3
"""Servidor MCP para a API de Marketing da Meta.

Fala o protocolo MCP por stdio, em JSON-RPC 2.0, sem dependencia nenhuma:
so a biblioteca padrao do Python. Escrito a mao de proposito — um token de
conta de anuncios nao deveria passar por codigo de terceiro nao auditado.

Variaveis de ambiente (ver .env.exemplo):
  META_ACCESS_TOKEN      token do System User, com ads_read (e ads_management
                         so se voce quiser escrita)
  META_AD_ACCOUNT_ID     act_1234567890
  META_API_VERSAO        v23.0 por padrao
  META_PERMITIR_ESCRITA  1 libera mudar status e orcamento; vazio = so leitura
  META_TETO_DIARIO_BRL   teto de seguranca para mudar_orcamento (100 por padrao)
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))


def _carregar_env():
    """Le o .env que fica ao lado deste arquivo, sem depender de biblioteca.

    O ambiente ja existente sempre ganha: num workflow do GitHub Actions os
    segredos chegam por variavel, e nenhum .env deve sobrescrever isso.
    """
    caminho = os.path.join(AQUI, ".env")
    if not os.path.exists(caminho):
        return
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            for linha in arquivo:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, _, valor = linha.partition("=")
                chave = chave.strip()
                valor = valor.strip().strip('"').strip("'")
                if chave and chave not in os.environ:
                    os.environ[chave] = valor
    except OSError as exc:
        sys.stderr.write("[meta-ads-mcp] nao consegui ler o .env: " + str(exc) + "\n")


_carregar_env()

VERSAO_API = os.environ.get("META_API_VERSAO", "v23.0").strip() or "v23.0"
BASE = "https://graph.facebook.com/" + VERSAO_API
TOKEN = os.environ.get("META_ACCESS_TOKEN", "").strip()
CONTA = os.environ.get("META_AD_ACCOUNT_ID", "").strip()
ESCRITA = os.environ.get("META_PERMITIR_ESCRITA", "").strip().lower() in ("1", "true", "sim", "yes")
try:
    TETO = float(os.environ.get("META_TETO_DIARIO_BRL", "100") or "100")
except ValueError:
    TETO = 100.0

if CONTA and not CONTA.startswith("act_"):
    CONTA = "act_" + CONTA


class Erro(Exception):
    pass


def limpar(texto):
    """Nunca devolver o token numa mensagem de erro."""
    if TOKEN and TOKEN in texto:
        texto = texto.replace(TOKEN, "***")
    return texto


def registrar(msg):
    sys.stderr.write("[meta-ads-mcp] " + limpar(str(msg)) + "\n")
    sys.stderr.flush()


def chamar(caminho, parametros=None, metodo="GET"):
    if not TOKEN:
        raise Erro("META_ACCESS_TOKEN nao esta definido no ambiente deste servidor.")
    parametros = dict(parametros or {})
    parametros["access_token"] = TOKEN
    url = BASE + "/" + str(caminho).lstrip("/")
    dados = None
    if metodo == "GET":
        url = url + "?" + urllib.parse.urlencode(parametros)
    else:
        dados = urllib.parse.urlencode(parametros).encode("utf-8")
    pedido = urllib.request.Request(url, data=dados, method=metodo)
    pedido.add_header("User-Agent", "mytickets-meta-ads-mcp/1.0")
    try:
        with urllib.request.urlopen(pedido, timeout=90) as resposta:
            return json.loads(resposta.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        bruto = exc.read().decode("utf-8", errors="replace")
        motivo = bruto[:600]
        try:
            erro = json.loads(bruto).get("error", {})
            motivo = erro.get("message", motivo)
            if erro.get("error_user_msg"):
                motivo = motivo + " — " + erro["error_user_msg"]
        except Exception:
            pass
        raise Erro("HTTP " + str(exc.code) + ": " + limpar(motivo))
    except urllib.error.URLError as exc:
        raise Erro("Sem conexao com graph.facebook.com: " + limpar(str(exc.reason)))


def conta_exigida():
    if not CONTA:
        raise Erro("META_AD_ACCOUNT_ID nao esta definido (formato act_1234567890).")
    return CONTA


def reais(valor_menor):
    """A Meta guarda orcamento em centavos; aqui vira reais."""
    try:
        return round(int(valor_menor) / 100.0, 2)
    except (TypeError, ValueError):
        return None


def centavos(valor_reais):
    return str(int(round(float(valor_reais) * 100)))


def paginar(caminho, parametros, limite):
    """Segue o cursor da Graph API ate juntar `limite` itens."""
    itens = []
    parametros = dict(parametros)
    parametros["limit"] = min(limite, 100)
    while True:
        bloco = chamar(caminho, parametros)
        itens.extend(bloco.get("data", []))
        proximo = (bloco.get("paging") or {}).get("cursors", {}).get("after")
        if not proximo or len(itens) >= limite or not bloco.get("data"):
            break
        parametros["after"] = proximo
    return itens[:limite]


# ---------------------------------------------------------------- ferramentas

def ferramenta_checar(_args):
    saida = {
        "versao_da_api": VERSAO_API,
        "escrita_liberada": ESCRITA,
        "teto_diario_brl": TETO,
        "conta_configurada": CONTA or None,
    }
    saida["token"] = "ausente" if not TOKEN else "presente"
    if TOKEN:
        try:
            eu = chamar("me", {"fields": "id,name"})
            saida["identidade"] = eu
        except Erro as exc:
            saida["identidade_erro"] = str(exc)
    if TOKEN and CONTA:
        try:
            saida["conta"] = chamar(CONTA, {
                "fields": "name,account_status,currency,timezone_name,amount_spent,balance,funding_source_details",
            })
        except Erro as exc:
            saida["conta_erro"] = str(exc)
    return saida


CAMPOS_CAMPANHA = "id,name,status,effective_status,objective,daily_budget,lifetime_budget,budget_remaining,start_time,stop_time"
CAMPOS_CONJUNTO = "id,name,status,effective_status,campaign_id,daily_budget,lifetime_budget,optimization_goal,billing_event,targeting"
CAMPOS_ANUNCIO = "id,name,status,effective_status,adset_id,campaign_id,creative{id,name,title,body,object_story_spec}"


def _enfeitar(itens):
    for item in itens:
        for chave in ("daily_budget", "lifetime_budget", "budget_remaining"):
            if chave in item:
                item[chave + "_brl"] = reais(item[chave])
    return itens


def ferramenta_listar_campanhas(args):
    parametros = {"fields": CAMPOS_CAMPANHA}
    estado = (args.get("status") or "TODAS").upper()
    if estado in ("ACTIVE", "PAUSED", "ARCHIVED"):
        parametros["effective_status"] = json.dumps([estado])
    itens = paginar(conta_exigida() + "/campaigns", parametros, int(args.get("limite", 50)))
    return {"total": len(itens), "campanhas": _enfeitar(itens)}


def ferramenta_listar_conjuntos(args):
    parametros = {"fields": CAMPOS_CONJUNTO}
    alvo = args.get("campanha_id")
    caminho = (alvo + "/adsets") if alvo else (conta_exigida() + "/adsets")
    itens = paginar(caminho, parametros, int(args.get("limite", 50)))
    for item in itens:
        alvos = item.pop("targeting", None)
        if alvos:
            item["publico"] = {
                "paises": (alvos.get("geo_locations") or {}).get("countries"),
                "idade": [alvos.get("age_min"), alvos.get("age_max")],
                "interesses": [i.get("name") for i in (alvos.get("flexible_spec") or [{}])[0].get("interests", [])] or None,
            }
    return {"total": len(itens), "conjuntos": _enfeitar(itens)}


def ferramenta_listar_anuncios(args):
    alvo = args.get("conjunto_id") or args.get("campanha_id")
    caminho = (alvo + "/ads") if alvo else (conta_exigida() + "/ads")
    itens = paginar(caminho, {"fields": CAMPOS_ANUNCIO}, int(args.get("limite", 50)))
    return {"total": len(itens), "anuncios": itens}


CAMPOS_INSIGHT = (
    "spend,impressions,reach,frequency,clicks,inline_link_clicks,ctr,"
    "cpc,cpm,cost_per_inline_link_click,actions,action_values,purchase_roas,"
    "campaign_name,adset_name,ad_name,date_start,date_stop"
)
PERIODOS = (
    "today", "yesterday", "last_3d", "last_7d", "last_14d", "last_28d",
    "last_30d", "this_week_mon_today", "this_month", "last_month", "maximum",
)


def ferramenta_insights(args):
    nivel = (args.get("nivel") or "campaign").lower()
    if nivel not in ("account", "campaign", "adset", "ad"):
        raise Erro("nivel deve ser account, campaign, adset ou ad.")
    alvo = args.get("id") or conta_exigida()
    parametros = {"fields": CAMPOS_INSIGHT, "level": nivel}
    desde, ate = args.get("desde"), args.get("ate")
    if desde and ate:
        parametros["time_range"] = json.dumps({"since": desde, "until": ate})
    else:
        periodo = (args.get("periodo") or "last_7d").lower()
        if periodo not in PERIODOS:
            raise Erro("periodo invalido. Use um de: " + ", ".join(PERIODOS))
        parametros["date_preset"] = periodo
    if args.get("por_dia"):
        parametros["time_increment"] = "1"
    linhas = paginar(alvo + "/insights", parametros, int(args.get("limite", 100)))
    for linha in linhas:
        acoes = {a.get("action_type"): a.get("value") for a in (linha.pop("actions", None) or [])}
        if acoes:
            linha["acoes"] = acoes
        valores = {a.get("action_type"): a.get("value") for a in (linha.pop("action_values", None) or [])}
        if valores:
            linha["valor_das_acoes"] = valores
    return {"nivel": nivel, "total": len(linhas), "linhas": linhas}


def _atual(identificador):
    return chamar(identificador, {"fields": "id,name,status,effective_status,daily_budget,lifetime_budget"})


def ferramenta_mudar_status(args):
    if not ESCRITA:
        raise Erro("Escrita bloqueada. Defina META_PERMITIR_ESCRITA=1 para liberar.")
    identificador = args.get("id")
    novo = (args.get("status") or "").upper()
    if not identificador:
        raise Erro("Informe o id da campanha, do conjunto ou do anuncio.")
    if novo not in ("ACTIVE", "PAUSED"):
        raise Erro("status deve ser ACTIVE ou PAUSED.")
    antes = _atual(identificador)
    if not args.get("confirmar"):
        return {
            "simulacao": True,
            "aviso": "Nada foi alterado. Reenvie com confirmar=true para aplicar.",
            "objeto": antes,
            "mudaria_para": novo,
        }
    chamar(identificador, {"status": novo}, metodo="POST")
    return {"aplicado": True, "antes": antes, "depois": _atual(identificador)}


def ferramenta_mudar_orcamento(args):
    if not ESCRITA:
        raise Erro("Escrita bloqueada. Defina META_PERMITIR_ESCRITA=1 para liberar.")
    identificador = args.get("id")
    if not identificador:
        raise Erro("Informe o id da campanha ou do conjunto.")
    diario = args.get("diario_brl")
    vitalicio = args.get("vitalicio_brl")
    if (diario is None) == (vitalicio is None):
        raise Erro("Informe diario_brl OU vitalicio_brl, nunca os dois.")
    if diario is not None and float(diario) > TETO:
        raise Erro(
            "R$ " + str(diario) + " passa do teto de seguranca de R$ " + str(TETO) +
            ". Suba META_TETO_DIARIO_BRL de proposito se for mesmo isso."
        )
    campo = "daily_budget" if diario is not None else "lifetime_budget"
    valor = centavos(diario if diario is not None else vitalicio)
    antes = _atual(identificador)
    if not args.get("confirmar"):
        return {
            "simulacao": True,
            "aviso": "Nada foi alterado. Reenvie com confirmar=true para aplicar.",
            "objeto": antes,
            "mudaria": {campo: valor, "em_reais": diario if diario is not None else vitalicio},
        }
    chamar(identificador, {campo: valor}, metodo="POST")
    return {"aplicado": True, "antes": antes, "depois": _atual(identificador)}


def ferramenta_biblioteca(args):
    termo = args.get("termo")
    if not termo:
        raise Erro("Informe o termo de busca.")
    paises = args.get("paises") or ["BR"]
    parametros = {
        "search_terms": termo,
        "ad_reached_countries": json.dumps(paises),
        "ad_active_status": args.get("situacao", "ACTIVE"),
        "ad_type": args.get("tipo", "ALL"),
        "fields": "id,page_name,ad_creation_time,ad_delivery_start_time,ad_creative_bodies,ad_creative_link_titles,ad_creative_link_descriptions,ad_snapshot_url,publisher_platforms",
    }
    itens = paginar("ads_archive", parametros, int(args.get("limite", 25)))
    return {
        "total": len(itens),
        "nota": (
            "Fora da Uniao Europeia a Ad Library API so devolve anuncios sobre politica e "
            "temas sociais. Para anuncio comercial, consulte paises da UE ou use a Biblioteca "
            "de Anuncios pelo navegador."
        ),
        "anuncios": itens,
    }


FERRAMENTAS = [
    {
        "name": "meta_checar",
        "description": "Confere token, conta, moeda, saldo, versao da API e se a escrita esta liberada. Rode isto primeiro.",
        "handler": ferramenta_checar,
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "meta_listar_campanhas",
        "description": "Lista campanhas da conta com status, objetivo e orcamento ja convertido para reais.",
        "handler": ferramenta_listar_campanhas,
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["TODAS", "ACTIVE", "PAUSED", "ARCHIVED"], "description": "Filtra pelo status efetivo."},
                "limite": {"type": "integer", "description": "Quantas trazer (padrao 50)."},
            },
        },
    },
    {
        "name": "meta_listar_conjuntos",
        "description": "Lista conjuntos de anuncios, com publico resumido (paises, idade, interesses).",
        "handler": ferramenta_listar_conjuntos,
        "inputSchema": {
            "type": "object",
            "properties": {
                "campanha_id": {"type": "string", "description": "So os conjuntos dessa campanha."},
                "limite": {"type": "integer"},
            },
        },
    },
    {
        "name": "meta_listar_anuncios",
        "description": "Lista anuncios com o criativo (titulo e texto), por conjunto ou por campanha.",
        "handler": ferramenta_listar_anuncios,
        "inputSchema": {
            "type": "object",
            "properties": {
                "conjunto_id": {"type": "string"},
                "campanha_id": {"type": "string"},
                "limite": {"type": "integer"},
            },
        },
    },
    {
        "name": "meta_insights",
        "description": "Metricas de gasto, impressoes, alcance, cliques, CTR, CPC, CPM, acoes e ROAS. Nivel account, campaign, adset ou ad.",
        "handler": ferramenta_insights,
        "inputSchema": {
            "type": "object",
            "properties": {
                "nivel": {"type": "string", "enum": ["account", "campaign", "adset", "ad"]},
                "id": {"type": "string", "description": "Id do objeto; vazio = a conta inteira."},
                "periodo": {"type": "string", "enum": list(PERIODOS), "description": "Atalho de periodo (padrao last_7d)."},
                "desde": {"type": "string", "description": "AAAA-MM-DD, usado com 'ate'."},
                "ate": {"type": "string", "description": "AAAA-MM-DD."},
                "por_dia": {"type": "boolean", "description": "Quebra o resultado dia a dia."},
                "limite": {"type": "integer"},
            },
        },
    },
    {
        "name": "meta_mudar_status",
        "description": "Pausa ou ativa campanha, conjunto ou anuncio. Simula por padrao: so aplica com confirmar=true, e so se META_PERMITIR_ESCRITA=1.",
        "handler": ferramenta_mudar_status,
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "status": {"type": "string", "enum": ["ACTIVE", "PAUSED"]},
                "confirmar": {"type": "boolean", "description": "false ou ausente devolve so a previa."},
            },
            "required": ["id", "status"],
        },
    },
    {
        "name": "meta_mudar_orcamento",
        "description": "Ajusta orcamento diario ou vitalicio, em reais. Simula por padrao e respeita META_TETO_DIARIO_BRL.",
        "handler": ferramenta_mudar_orcamento,
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "diario_brl": {"type": "number"},
                "vitalicio_brl": {"type": "number"},
                "confirmar": {"type": "boolean"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "meta_biblioteca_anuncios",
        "description": "Busca na Ad Library da Meta. Atencao: fora da UE so devolve anuncio politico e de tema social.",
        "handler": ferramenta_biblioteca,
        "inputSchema": {
            "type": "object",
            "properties": {
                "termo": {"type": "string"},
                "paises": {"type": "array", "items": {"type": "string"}, "description": "Codigos ISO, padrao ['BR']."},
                "situacao": {"type": "string", "enum": ["ACTIVE", "ALL", "INACTIVE"]},
                "limite": {"type": "integer"},
            },
            "required": ["termo"],
        },
    },
]

POR_NOME = {f["name"]: f for f in FERRAMENTAS}
PROTOCOLOS = ("2024-11-05", "2025-03-26", "2025-06-18")


def responder(identificador, resultado=None, erro=None):
    if identificador is None:
        return
    mensagem = {"jsonrpc": "2.0", "id": identificador}
    if erro is not None:
        mensagem["error"] = erro
    else:
        mensagem["result"] = resultado
    sys.stdout.write(json.dumps(mensagem, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def tratar(mensagem):
    metodo = mensagem.get("method")
    identificador = mensagem.get("id")
    parametros = mensagem.get("params") or {}

    if metodo == "initialize":
        pedido = parametros.get("protocolVersion")
        versao = pedido if pedido in PROTOCOLOS else PROTOCOLOS[0]
        return responder(identificador, {
            "protocolVersion": versao,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "meta-ads", "version": "1.0.0"},
        })

    if metodo in ("notifications/initialized", "notifications/cancelled"):
        return

    if metodo == "ping":
        return responder(identificador, {})

    if metodo == "tools/list":
        return responder(identificador, {
            "tools": [
                {"name": f["name"], "description": f["description"], "inputSchema": f["inputSchema"]}
                for f in FERRAMENTAS
            ]
        })

    if metodo == "tools/call":
        nome = parametros.get("name")
        ferramenta = POR_NOME.get(nome)
        if not ferramenta:
            return responder(identificador, erro={"code": -32602, "message": "ferramenta desconhecida: " + str(nome)})
        try:
            saida = ferramenta["handler"](parametros.get("arguments") or {})
            texto = json.dumps(saida, ensure_ascii=False, indent=2)
        except Erro as exc:
            return responder(identificador, {
                "content": [{"type": "text", "text": "Erro: " + str(exc)}],
                "isError": True,
            })
        except Exception as exc:  # noqa: BLE001 - o servidor nunca pode morrer
            registrar("falha inesperada em " + str(nome) + ": " + repr(exc))
            return responder(identificador, {
                "content": [{"type": "text", "text": "Falha inesperada: " + limpar(repr(exc))}],
                "isError": True,
            })
        return responder(identificador, {"content": [{"type": "text", "text": texto}]})

    if metodo in ("resources/list", "prompts/list"):
        chave = "resources" if metodo.startswith("resources") else "prompts"
        return responder(identificador, {chave: []})

    return responder(identificador, erro={"code": -32601, "message": "metodo desconhecido: " + str(metodo)})


def principal():
    registrar("de pe — api " + VERSAO_API + ", conta " + (CONTA or "nao definida") +
              ", escrita " + ("liberada" if ESCRITA else "bloqueada"))
    for linha in sys.stdin:
        linha = linha.strip()
        if not linha:
            continue
        try:
            mensagem = json.loads(linha)
        except json.JSONDecodeError:
            registrar("linha ignorada, nao era JSON")
            continue
        try:
            tratar(mensagem)
        except Exception as exc:  # noqa: BLE001
            registrar("erro ao tratar mensagem: " + repr(exc))


def checar_pela_linha_de_comando():
    """`python servidor.py --checar` imprime o diagnostico sem precisar de MCP."""
    saida = ferramenta_checar({})
    print(json.dumps(saida, ensure_ascii=False, indent=2))
    ok = saida.get("token") == "presente" and "identidade" in saida and "conta" in saida
    return 0 if ok else 1


if __name__ == "__main__":
    if "--checar" in sys.argv:
        sys.exit(checar_pela_linha_de_comando())
    principal()
