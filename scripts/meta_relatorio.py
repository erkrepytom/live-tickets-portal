#!/usr/bin/env python3
"""Relatorio diario das campanhas no Meta Ads, com a regra de corte aplicada.

Escreve em relatorios/, que esta no .gitignore. Nunca muda campanha nenhuma:
so le, compara com os limites do plano e avisa.

ATENCAO: este repositorio e publico, e no GitHub tanto os arquivos quanto o log
de execucao de um repositorio publico sao visiveis por qualquer pessoa. Por isso
nada de gasto, CPC ou nome de campanha e commitado, e dentro do Actions o script
nao imprime numero nenhum: ou ele envia por Telegram, ou nao diz nada.

Modos:
  python scripts/meta_relatorio.py              relatorio local em relatorios/
  python scripts/meta_relatorio.py --telegram   envia para o grupo e nao grava nada

Limites que ele cobra, iguais aos da simulacao de campanha:
  - anuncio com 2.000 impressoes e CTR abaixo de 0,8%  -> cortar
  - conjunto com 100 cliques e nenhuma saida medida    -> cortar
  - canal com R$ 1.000 gastos e nenhuma venda          -> decidir
  - nada e julgado antes de 100 cliques

Variaveis: META_ACCESS_TOKEN, META_AD_ACCOUNT_ID (e as do servidor MCP).
"""

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "meta-ads-mcp"))

import servidor  # noqa: E402  (precisa do sys.path acima)

CTR_MINIMO = 0.8
IMPRESSOES_PARA_JULGAR = 2000
CLIQUES_PARA_JULGAR = 100
GASTO_PARA_DECIDIR = 1000.0
RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PASTA = os.path.normpath(os.path.join(RAIZ, "relatorios"))
EM_ACTIONS = bool(os.environ.get("GITHUB_ACTIONS"))
falhas = []


def aviso(texto, erro=False):
    """Fora do Actions imprime. Dentro dele, cala: o log de repositório público é público."""
    if EM_ACTIONS:
        return
    print(texto)


def anotar(texto, erro=False):
    """Anotação sem número nenhum, essa sim pode aparecer no resumo da execução."""
    print(texto)
    if EM_ACTIONS:
        print(f"::{'error' if erro else 'notice'}::{texto}")


def numero(linha, chave, padrao=0.0):
    try:
        return float(linha.get(chave) or 0)
    except (TypeError, ValueError):
        return padrao


def saidas_de(linha):
    """Quantos cliques de saida o pixel registrou nesta linha."""
    acoes = linha.get("acoes") or {}
    total = 0.0
    for chave, valor in acoes.items():
        if "link_click" in chave or chave in ("offsite_conversion.AffiliateClick", "AffiliateClick"):
            try:
                total = max(total, float(valor))
            except (TypeError, ValueError):
                pass
    return total


def membros_de(linha):
    acoes = linha.get("acoes") or {}
    for chave in ("lead", "onsite_conversion.lead_grouped", "offsite_conversion.fb_pixel_lead", "group_join"):
        if chave in acoes:
            try:
                return float(acoes[chave])
            except (TypeError, ValueError):
                pass
    return 0.0


def puxar(nivel, periodo):
    try:
        return servidor.ferramenta_insights({"nivel": nivel, "periodo": periodo, "limite": 200})["linhas"]
    except servidor.Erro as exc:
        falhas.append(f"{nivel}/{periodo}: {exc}")
        aviso(f"Não consegui os insights de {nivel}/{periodo}: {exc}", erro=True)
        return []


def cortes(anuncios, conjuntos, conta):
    recados = []
    for linha in anuncios:
        impressoes, ctr = numero(linha, "impressions"), numero(linha, "ctr")
        if impressoes >= IMPRESSOES_PARA_JULGAR and ctr < CTR_MINIMO:
            recados.append(
                f"CORTAR anúncio «{linha.get('ad_name', '?')}»: {int(impressoes)} impressões e CTR de "
                f"{ctr:.2f}%, abaixo do mínimo de {CTR_MINIMO}%."
            )
    for linha in conjuntos:
        cliques = numero(linha, "inline_link_clicks") or numero(linha, "clicks")
        if cliques >= CLIQUES_PARA_JULGAR and saidas_de(linha) == 0:
            recados.append(
                f"CORTAR conjunto «{linha.get('adset_name', '?')}»: {int(cliques)} cliques e nenhuma "
                f"saída medida. Ou o público não serve, ou o pixel não está marcando a saída."
            )
    gasto = sum(numero(l, "spend") for l in conta)
    membros = sum(membros_de(l) for l in conta)
    if gasto >= GASTO_PARA_DECIDIR:
        custo = (gasto / membros) if membros else None
        if custo is None or custo > 30:
            recados.append(
                f"DECIDIR: R$ {gasto:,.2f} gastos e custo por membro de "
                + (f"R$ {custo:,.2f}" if custo else "—, nenhum membro registrado")
                + ". A regra do plano manda desligar o canal nessa situação."
            )
    return recados


def tabela(linhas, rotulo):
    if not linhas:
        return f"_Sem dados de {rotulo} no período._\n"
    cabecalho = (
        f"| {rotulo} | Gasto | Impressões | Cliques | CTR | CPC | Saídas | Membros |\n"
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n"
    )
    corpo = ""
    for linha in sorted(linhas, key=lambda l: -numero(l, "spend")):
        nome = linha.get("campaign_name") or linha.get("adset_name") or linha.get("ad_name") or "conta"
        corpo += (
            f"| {nome} | R$ {numero(linha, 'spend'):,.2f} | {int(numero(linha, 'impressions')):,} | "
            f"{int(numero(linha, 'inline_link_clicks') or numero(linha, 'clicks')):,} | "
            f"{numero(linha, 'ctr'):.2f}% | R$ {numero(linha, 'cpc'):,.2f} | "
            f"{int(saidas_de(linha)):,} | {int(membros_de(linha)):,} |\n"
        )
    return cabecalho + corpo


def principal():
    if not servidor.TOKEN:
        aviso("META_ACCESS_TOKEN não está definido; nada a relatar.", erro=True)
        return 1
    if not servidor.CONTA:
        aviso("META_AD_ACCOUNT_ID não está definido; nada a relatar.", erro=True)
        return 1

    ontem_campanhas = puxar("campaign", "yesterday")
    semana_campanhas = puxar("campaign", "last_7d")
    semana_conjuntos = puxar("adset", "last_7d")
    semana_anuncios = puxar("ad", "last_7d")
    semana_conta = puxar("account", "last_7d")

    recados = cortes(semana_anuncios, semana_conjuntos, semana_conta)
    gasto_ontem = sum(numero(l, "spend") for l in ontem_campanhas)
    gasto_semana = sum(numero(l, "spend") for l in semana_conta)
    membros_semana = sum(membros_de(l) for l in semana_conta)
    saidas_semana = sum(saidas_de(l) for l in semana_conta)
    custo_membro = (gasto_semana / membros_semana) if membros_semana else None

    agora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    texto = f"""# Meta Ads — relatório do dia

_Gerado em {agora}. Este arquivo é escrito por `scripts/meta_relatorio.py` e não muda campanha nenhuma._

**Ontem:** R$ {gasto_ontem:,.2f} gastos. **Últimos 7 dias:** R$ {gasto_semana:,.2f}, {int(saidas_semana):,} saídas, {int(membros_semana):,} membros, custo por membro de """ + (f"R$ {custo_membro:,.2f}" if custo_membro else "—") + f""".

O ponto de equilíbrio da simulação é R$ 15 por membro. Acima de R$ 30 a regra manda desligar.

## O que a regra de corte apontou

"""
    if recados:
        for recado in recados:
            texto += f"- {recado}\n"
            aviso(recado, erro=recado.startswith("DECIDIR"))
    else:
        texto += "_Nada a cortar: ou está dentro dos limites, ou ainda não há volume para julgar._\n"

    texto += "\n## Ontem, por campanha\n\n" + tabela(ontem_campanhas, "Campanha")
    texto += "\n## Últimos 7 dias, por campanha\n\n" + tabela(semana_campanhas, "Campanha")
    texto += "\n## Últimos 7 dias, por conjunto\n\n" + tabela(semana_conjuntos, "Conjunto")
    texto += "\n## Últimos 7 dias, por anúncio\n\n" + tabela(semana_anuncios, "Anúncio")

    if "--telegram" in sys.argv:
        enviado = mandar_no_telegram(texto)
        anotar("Relatório do Meta Ads enviado ao grupo." if enviado
               else "Não consegui enviar o relatório ao grupo; confira TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID.",
               erro=not enviado)
        return 0 if enviado else 1

    if EM_ACTIONS:
        anotar("Relatório gerado, mas não impresso nem gravado: repositório público. "
               "Use --telegram, ou rode na sua máquina.", erro=False)
        return 1 if len(falhas) == 5 else 0

    os.makedirs(PASTA, exist_ok=True)
    dia = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    caminho_md = os.path.join(PASTA, f"meta-{dia}.md")
    with open(caminho_md, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto)
    with open(os.path.join(PASTA, "meta.json"), "w", encoding="utf-8") as arquivo:
        json.dump({
            "gerado_em": agora,
            "gasto_ontem": round(gasto_ontem, 2),
            "gasto_7d": round(gasto_semana, 2),
            "saidas_7d": int(saidas_semana),
            "membros_7d": int(membros_semana),
            "custo_por_membro_7d": round(custo_membro, 2) if custo_membro else None,
            "cortes": recados,
            "falhas": falhas,
            "campanhas_7d": semana_campanhas,
        }, arquivo, ensure_ascii=False, indent=2)

    print(f"\nEscrito em {caminho_md}")
    if len(falhas) == 5:
        aviso("Todas as consultas falharam — o relatório saiu vazio.", erro=True)
        return 1
    return 0


def mandar_no_telegram(texto):
    """Manda o relatório para um chat do Telegram por bot. Nada vai para o repositório."""
    ficha = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not ficha or not chat:
        return False
    import urllib.parse
    import urllib.request
    corpo = urllib.parse.urlencode({
        "chat_id": chat,
        "text": texto[:4000],
        "parse_mode": "Markdown",
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    pedido = urllib.request.Request(
        f"https://api.telegram.org/bot{ficha}/sendMessage", data=corpo, method="POST")
    try:
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            return json.loads(resposta.read().decode("utf-8")).get("ok", False)
    except Exception:
        return False


if __name__ == "__main__":
    sys.exit(principal())
