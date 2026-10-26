# Prospecção nos EUA: onde falam de ingressos e como entrar na conversa

Três partes: **onde** estão os comentários, **como varrer** todo dia e **como prospectar** sem virar spam.

---

## 1. Onde estão os comentários

| Lugar | Quem está lá | O que procurar |
| --- | --- | --- |
| Reddit, comunidade do time (r/cowboys, r/lakers, r/NYKnicks…) | torcedor indo ao jogo | "first game", "where to sit", "tickets for [jogo]" |
| Reddit, liga (r/nfl, r/nba) | torcedor de fora da cidade | threads de viagem e de jogo fora de casa |
| Reddit, cidade (r/Dallas, r/LosAngeles, r/nyc) | visitante perguntando o que fazer | "visiting", "this weekend", "game day" |
| Reddit, viagem (r/travel, r/solotravel, r/TravelNoPics, r/AskAnAmerican) | turista estrangeiro | "first time in the US", "is it worth it", "from Brazil/UK" |
| r/tickets | quem já está comprando | "is [site] legit", "best site", "fees" |
| Comentários do YouTube (vídeos de jogo, de estádio, "how to buy tickets") | quem pesquisa antes de ir | "how much", "where did you buy" |
| Facebook: grupos de brasileiros nos EUA, de intercambistas e de viagem para os EUA | brasileiro e latino viajando | "alguém já foi num jogo da NBA?" |
| Quora e TripAdvisor (fórum de cada cidade) | turista planejando | perguntas sobre jogo, estádio e preço |

Facebook, Quora e TripAdvisor não têm busca aberta para robô: são para ronda manual, 15 minutos por semana.

---

## 2. Varredura automática (já no repositório)

- **Script:** `scripts/escuta_eua.py`. Lê os eventos dos EUA em `data/eventos.json`, monta as buscas por time, liga e cidade, e varre o Reddit pela busca pública em RSS. Com o secret `YOUTUBE_API_KEY` (cota gratuita do Google Cloud), também lê comentários de vídeos recentes de cada jogo.
- **Quando:** todo dia às 9h17 de Nova York pelo workflow `Escuta EUA`, ou à mão em Actions → "Escuta EUA" → Run workflow.
- **Onde ver:** na própria execução do Actions, a aba Summary mostra a tabela. O arquivo completo fica em Artifacts por 30 dias.
- **Nota de 0 a 100:** sinais de intenção (onde comprar, é confiável, preço, primeira vez/turista, setor), evento do site citado e quanto a conversa é recente. Vendedores anunciando ingresso são descartados.
- **Não publica nada:** sem commit, sem deploy, sem post. Responder é sempre manual.
- **Evento novo entra sozinho:** basta estar em `data/eventos.json` com país EUA. Para um time novo, acrescente a comunidade em `SUBREDDITS` no script.
- **Limite conhecido:** o Reddit às vezes bloqueia buscas vindas de servidores de nuvem. Quando isso acontecer, o relatório conta as buscas "sem resultado ou bloqueadas". Se for frequente, a saída é criar um app gratuito no Reddit e usar a API oficial.

---

## 3. Como prospectar

### Regras que não se quebram
1. **Leia as regras da comunidade antes.** Muitas proíbem link de afiliado ou de venda. Nessas, ajude sem link.
2. **Ajude primeiro.** A resposta tem que valer sozinha, mesmo que a pessoa nunca clique.
3. **Diga quem você é.** "I run mytickets.tours, a ticket guide site" na mesma resposta. Exigência da FTC e das comunidades.
4. **Link para o guia, nunca direto para o checkout.** O guia do evento já tem os botões de compra.
5. **Nada automático.** Sem bot postando e sem DM para quem não pediu. Isso derruba a conta e o domínio.
6. **Proporção 9 para 1:** nove participações sem link para cada uma com link.

### Rastreamento
Use sempre `?utm_source=reddit&utm_medium=community&utm_campaign=<slug-do-evento>` (ou `youtube`, `facebook`) no link do guia. No GA4 dá para ver quais comunidades geram `affiliate_click`.

### Modelos de resposta (adapte, nunca cole igual)
A coluna "Resposta sugerida" do relatório aponta qual usar.

**onde_comprar**
> For [game], the official team sale usually sells out fast, so most people end up on resale. Whatever site you use, check the final price with fees before paying and make sure they have a delivery guarantee. I run mytickets.tours and wrote a guide for this game with dates, sections and how to get there: [link]

**confianca**
> Good instinct to check. What I look for: a registered company with published terms, a written delivery guarantee, and card payment (never bank transfer or Zelle to a person). Screenshots of tickets as "proof" are a red flag, since the same QR code can be sold many times. We keep a scam checklist here (disclosure: it's my site): [link]

**preco**
> Prices for [game] move with demand. Upper levels and end zones/behind the baskets are usually the cheapest and still show the whole game. Regular-season prices can drop close to the date, while rivalry and holiday games usually stay high. Current lowest prices are on the guide I keep for this game: [link]

**turista**
> Welcome! A few things foreign visitors trip over: tell your bank before buying so the card isn't blocked, tickets are almost always on your phone, and NFL stadiums only allow clear bags. I made a guide for visitors with how to get to [stadium] and which sections to pick (my site, full disclosure): [link]

**setor / chegar / ingresso**
> Responda à pergunta concreta (setor, estacionamento, transporte) com a informação do guia do evento. Link só se a comunidade permitir.

### Rotina semanal (30 a 45 minutos)
1. Abrir o relatório do dia no Actions e responder as 5 conversas de nota mais alta.
2. Ronda manual nos grupos de Facebook e no TripAdvisor da cidade de cada jogo.
3. Anotar numa planilha: comunidade, link, data, se teve link e cliques vistos no GA4.
4. Depois de 4 semanas, cortar as comunidades que não geram clique e reforçar as que geram.

### Prospecção de parcerias (além das conversas)
- **Blogs e canais de viagem para os EUA** (em português e espanhol): propor guia em conjunto ou link para os guias de evento. Rende backlink e tráfego.
- **Agências de intercâmbio e de viagem** que levam brasileiros aos EUA: oferecer os guias de jogo como material para clientes.
- **Grupos de torcedores estrangeiros** (ex.: fã-clubes brasileiros de times da NFL e NBA): conteúdo útil para o grupo, com autorização do administrador.
