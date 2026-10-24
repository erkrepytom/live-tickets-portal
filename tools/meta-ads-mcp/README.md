# Servidor MCP — Meta Ads

Ponte entre o Claude Code e a API de Marketing da Meta. Em Python puro, **sem nenhuma
dependência**: só a biblioteca padrão. Um arquivo, `servidor.py`.

## Por que escrito à mão, e não um servidor da comunidade

Um token de conta de anúncios com `ads_management` pode pausar campanha, trocar orçamento e
ler o histórico de gastos. Instalar para isso um pacote de terceiro não auditado — por npm,
pip ou contêiner — é entregar essa chave a código que ninguém leu. Este servidor tem umas
poucas centenas de linhas, chama só `graph.facebook.com`, não escreve em disco e não manda
telemetria para lugar nenhum. Dá para ler inteiro em dez minutos.

## O que ele faz

| Ferramenta | O que faz |
| --- | --- |
| `meta_checar` | Confere token, conta, moeda, saldo e versão da API. **Rode primeiro.** |
| `meta_listar_campanhas` | Campanhas com status, objetivo e orçamento já em reais |
| `meta_listar_conjuntos` | Conjuntos com o público resumido (países, idade, interesses) |
| `meta_listar_anuncios` | Anúncios com título e texto do criativo |
| `meta_insights` | Gasto, impressões, alcance, cliques, CTR, CPC, CPM, ações e ROAS |
| `meta_mudar_status` | Pausa ou ativa — **simula por padrão** |
| `meta_mudar_orcamento` | Orçamento diário ou vitalício, em reais — **simula por padrão** |
| `meta_biblioteca_anuncios` | Busca na Ad Library (leia a ressalva mais abaixo) |

## As duas travas de segurança

1. **Escrita bloqueada por padrão.** `meta_mudar_status` e `meta_mudar_orcamento` recusam
   enquanto `META_PERMITIR_ESCRITA` não for `1` no `.env`. Com leitura apenas, o pior que um
   erro do agente faz é mostrar um número errado.
2. **Simulação antes de aplicar.** Mesmo com escrita liberada, as duas devolvem só a prévia
   — o estado atual e o que mudaria — até receberem `confirmar: true`. E `meta_mudar_orcamento`
   recusa qualquer valor acima de `META_TETO_DIARIO_BRL` (R$ 100 por padrão), para que um
   engano de casa decimal não vire R$ 5.000 por dia.

## Instalação

### 1. Gerar o token (você, não eu)

Credencial é sua e digitada por você. No Meta:

1. `business.facebook.com` → **Configurações do negócio** → **Usuários** → **Usuários do sistema**
2. **Adicionar** → nome (ex.: `mytickets-agente`) → função **Funcionário**
3. **Adicionar ativos** → **Contas de anúncios** → marque a conta → permissão **Gerenciar campanhas**
4. **Gerar novo token** → escolha o app → marque:
   - `ads_read` — obrigatório
   - `ads_management` — **só** se quiser liberar escrita depois
   - `business_management` — opcional, ajuda o `meta_checar`
5. Copie o token. Ele não aparece de novo.

Token de usuário do sistema não expira sozinho, mas morre se a senha do dono mudar, se o app
for reconfigurado ou se a permissão for revogada. Quando o `meta_checar` acusar `HTTP 190`,
é isso: gere outro pelos mesmos passos.

### 2. Instalar

**Windows (PowerShell, dentro desta pasta):**

```powershell
.\instalar.ps1
```

Ele acha o Python, cria o `.env`, abre o Bloco de Notas para você colar o token, confere o
acesso na Graph API e registra o servidor no Claude Code.

**Linux, macOS ou WSL:**

```bash
bash instalar.sh
```

**Na mão, se preferir:**

```bash
cp .env.exemplo .env     # preencha META_ACCESS_TOKEN e META_AD_ACCOUNT_ID
python servidor.py --checar
claude mcp add meta-ads --scope user -- python /caminho/completo/servidor.py
```

O `.mcp.json` na raiz do repositório já declara este servidor para o escopo do projeto: abrindo
o projeto no Claude Code, ele pede sua aprovação na primeira vez e aparece em `/mcp`.

### 3. Conferir

```bash
python servidor.py --checar
```

Saindo com `token: presente`, `identidade` e `conta` preenchidos, está pronto. Se não:

| Sintoma | Causa provável |
| --- | --- |
| `HTTP 190` | token inválido ou revogado — gere outro |
| `HTTP 100` com `(#100)` | `META_AD_ACCOUNT_ID` sem o prefixo `act_` |
| `HTTP 200` com `(#200)` | falta `ads_read` no token |
| `Unsupported get request` | o usuário do sistema não tem acesso a essa conta |
| `Unknown version` | `META_API_VERSAO` descontinuada — suba no `.env` |

## O `.env`

Fica nesta pasta, está no `.gitignore` e **nunca** vai para o repositório. O servidor lê sozinho,
sem biblioteca de dotenv, e variáveis já presentes no ambiente sempre ganham dele — para que
no GitHub Actions os segredos do repositório prevaleçam.

## Ressalvas honestas

- **Ad Library API.** Fora da União Europeia ela devolve apenas anúncios sobre política e temas
  sociais. Para espiar criativo comercial de concorrente no Brasil ela não serve: use a
  Biblioteca de Anúncios pelo navegador, ou consulte países da UE. A ferramenta está aqui
  porque funciona onde funciona, não porque resolve a inteligência competitiva.
- **Versão da Graph API.** Cada versão é descontinuada cerca de dois anos depois do lançamento.
  O padrão é `v23.0`; confira o changelog da Meta e suba `META_API_VERSAO` quando o
  `meta_checar` reclamar. É a única manutenção que este servidor pede.
- **Atribuição.** Os números daqui são os da Meta, com a janela de atribuição da conta. Eles não
  batem com os do GA4 nem com os do painel do parceiro de afiliado, e não deveriam bater.

## O que não está aqui, e por quê

- **Composio, n8n, Activepieces, Pipeshub.** Fazem sentido quando há muitas contas, muitos
  clientes ou OAuth de vários usuários para administrar. Para uma conta de anúncios, cada um
  deles significa confiar o token de longa duração a um serviço a mais, com assinatura e
  dependência próprias, em troca de nada que este arquivo já não faça.
- **Contêiner Docker.** Existe para empacotar dependência. Este servidor não tem nenhuma.
- **`facebook-business` e `facebook-nodejs-business-sdk`.** Valem a pena no dia em que você for
  criar anúncio em massa ou montar público personalizado por código — operações com dezenas de
  campos aninhados. Para ler métrica e pausar campanha, os SDKs só acrescentam superfície.
  `pip install facebook-business` na hora que precisar.
- **CAPI (Conversions API).** É o passo seguinte, e é de telemetria, não de gestão: mandar
  `AffiliateClick` e `Lead` pelo servidor em vez de pelo navegador. Entra quando o consentimento
  e o pixel estiverem no ar.
- **Google Ads.** Precisa de OAuth mais um *developer token* aprovado pelo Google, e a aprovação
  demora. É uma segunda frente, não uma variação desta.

## Relatório diário

`scripts/meta_relatorio.py` lê as métricas, aplica a regra de corte do plano de campanha
(anúncio com 2.000 impressões e CTR abaixo de 0,8%; conjunto com 100 cliques e nenhuma saída;
canal com R$ 1.000 gastos e nenhuma venda) e escreve em `relatorios/`, que está no `.gitignore`.

**Este repositório é público.** No GitHub, de um repositório público tanto os arquivos quanto o
log de execução das Actions são visíveis por qualquer pessoa — inclusive por concorrente. Por isso
o relatório não é commitado e, dentro do Actions, o script não imprime número nenhum: ou sai por
Telegram, ou não sai. O workflow `meta-relatorio.yml` fica inerte enquanto `TELEGRAM_BOT_TOKEN`
e `TELEGRAM_CHAT_ID` não existirem nos segredos.
