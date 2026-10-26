# Plano de marketing do mytickets.tours

Foco inicial: **estratégias sem custo**, copiadas do que SeatPick, StubHub, SeatGeek, TickPick e Sports Events 365 fazem para crescer. Mídia paga (Google Ads) só entra depois que as páginas orgânicas provarem conversão.

Ordem dos mercados: **1. Estados Unidos** (maior volume de esportes e de buscas por ingressos), **2. Brasil e Europa** em paralelo, **3. resto do mundo**.

Situação hoje (26/10/2026): 10 eventos em PT, EN e ES, quase todos europeus. Só 1 é americano (Knicks vs Nuggets). A prioridade EUA ainda não aparece no catálogo.

---

## 0. Parceiros e comissão

Cada página de evento já vende o pacote da viagem: ingresso, passeio, hotel e transporte.

| Parceiro | O que oferece | Onde aparece | Comissão |
| --- | --- | --- | --- |
| Sports Events 365 | ingressos | 10 eventos, nos 3 idiomas | sim, código `6821d72fcdbe3` |
| GetYourGuide | tours, visita a estádio, passeios | 10 eventos | sim, `partner_id=ROXVLTV` |
| Booking.com | hospedagem perto do estádio | 10 eventos | **não**, campo `id` vazio em `VIAGEM` |
| Omio | trens, ônibus e voos na Europa | 7 eventos | **não**, campo `id` vazio em `VIAGEM` |
| P1 Travel | ingresso e pacote ingresso + hotel (Europa, F1) | desligado | aguardando aprovação |
| SuperIngressos | NBA, NFL, MLB, NHL, MLS e shows nos EUA | desligado | aguardando aprovação |

**Ações gratuitas e imediatas:**
1. Cadastrar o site na Booking.com e na Omio, direto ou pela Travelpayouts (as duas numa conta só). Os links já aparecem em 10 e 7 eventos e hoje não geram comissão. Com o código aprovado, basta colar no campo `id` de `VIAGEM` em `scripts/conteudo.py` e rodar o gerador.
2. Acompanhar a aprovação da SuperIngressos: é a porta de entrada para as ligas americanas.

---

## 1. Estratégias gratuitas copiadas dos sites de referência

| Estratégia | De quem copiamos | No site hoje | O que falta |
| --- | --- | --- | --- |
| Páginas por evento, cidade e competição | StubHub, SeatGeek, SeatPick | ✅ geradas por `gerar_paginas.py` | Páginas por **time** e por **estádio**, e mais eventos por hub |
| Rich snippets `SportsEvent` com data, local e preço | StubHub, SeatGeek | ✅ JSON-LD em cada evento | — |
| Hreflang PT/EN/ES, sitemaps, IndexNow, Bing | Todos | ✅ | — |
| Calendário por time ("Arsenal 2026/27 schedule & tickets") | SeatGeek, Sports Events 365 | ❌ | Página por time com todos os jogos futuros e preço mínimo |
| Comparação de preços entre vendedores | SeatPick | Parcial: estrutura de vários parceiros pronta, 1 ativo | Ligar P1 Travel e SuperIngressos quando aprovarem |
| Transparência e confiança | TickPick | ✅ "Como funciona e garantias", alertas de golpe | — |
| Guias para o torcedor viajante | Sports Events 365 | ✅ 2 guias | Guias para os EUA e para brasileiros (ver seções 2 e 3) |
| Alerta de preço por e-mail | SeatPick, SeatGeek | ❌ | "Avise quando baixar": cria lista própria de e-mails, com consentimento (LGPD/GDPR) |
| Vídeos curtos (Shorts, Reels, TikTok) | SeatGeek, StubHub | ✅ YouTube automático e Pinterest | Mais vídeos em inglês para o público americano |

---

## 2. Estados Unidos (prioridade 1)

**Por quê:** é o maior mercado de ingressos esportivos do mundo, com temporada o ano todo.

**Esportes e calendário:**
- NFL (setembro a fevereiro, Super Bowl em fevereiro)
- NBA (outubro a junho)
- NHL (outubro a junho)
- MLB (março a outubro)
- MLS (fevereiro a dezembro)
- Turismo esportivo de americanos para a Europa (Premier League, Champions League, F1)

**Ações gratuitas:**
1. Colocar no `data/eventos.json` jogos americanos que a Sports Events 365 já vende (como o Knicks vs Nuggets), enquanto a SuperIngressos não aprova.
2. Conteúdo "best seats at [estádio]" e "cheapest [time] tickets": é a cauda longa que mais converte nos EUA.
3. Guia "Premier League / Champions League trip from the US": viagem + ingresso, público de alta renda, usa hotel, passeio e ingresso na mesma página.
4. Reddit e fóruns de torcedores: respostas úteis com link para o guia, nunca spam, respeitando as regras de cada comunidade.
5. Vídeos curtos em inglês, narrados, sobre preço e experiência de estádio.

**Conformidade:** divulgação de afiliado clara (FTC). Já existe a página de aviso legal.

---

## 3. Brasil e Europa (prioridade 2, em paralelo)

### Brasil
- Turismo esportivo para a Europa: o brasileiro quer ver Real Madrid, Barcelona, PSG, Premier League. Guias em português com preço em BRL.
- Conteúdo: "Quanto custa ver um jogo do Real Madrid no Bernabéu", "Como comprar ingresso da Champions sendo brasileiro".
- NBA e NFL para o brasileiro que viaja aos EUA (SuperIngressos vende em português).
- Canais gratuitos: Instagram, TikTok, YouTube Shorts, grupos de viagem e o atendimento por WhatsApp que já existe.
- **Conformidade:** LGPD para e-mails capturados e identificação de publicidade (CONAR).

### Europa
- Mercado principal da Sports Events 365: Premier League, LaLiga, Serie A, Bundesliga, Ligue 1, Champions League, F1.
- Conteúdo de cidade: "Sports events in London this weekend", "Partidos en Madrid este mes". Os hubs de cidade já existem; falta volume de eventos.
- **Conformidade:** GDPR; o banner de cookies (Consent Mode v2) já está no site.

---

## 4. Resto do mundo (prioridade 3)
- América Latina hispânica (México, Argentina, Colômbia) reaproveitando as páginas em espanhol.
- Oriente Médio e Ásia para F1 e turismo esportivo europeu.
- Novos idiomas só quando o Search Console mostrar demanda real de um país.

---

## 5. Cronograma sugerido

| Período | Foco |
| --- | --- |
| Semana 1 | Cadastro na Booking/Omio (ou Travelpayouts); primeiros jogos de NBA e NFL no catálogo |
| Mês 1 | Páginas por time com calendário; guia "trip from the US" |
| Mês 2 | Ligar SuperIngressos e P1 Travel se aprovados; guias para brasileiros; alerta de preço por e-mail |
| Mês 3+ | Medir por mercado no GA4; testar Google Ads só nos eventos com conversão orgânica provada |

## 6. Como medir
- Os eventos `affiliate_click`, `outbound_ticket_click` e `travel_click` já vão para o GA4.
- Criar no GA4 um relatório por país e idioma para comparar EUA, Brasil e Europa.
- Painel mensal: cliques, conversões e comissão por parceiro e por país.
