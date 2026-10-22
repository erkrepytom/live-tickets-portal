# MyTickets Tours

Affiliate portal for international sports and show tickets, in Portuguese, English and Spanish. Tickets are sold and delivered by SportsEvents365.

## Pages

| Path | What it is |
|---|---|
| `index.html`, `en/`, `es/` | Home pages: departures board, featured events, explore by sport, city and artist, the 3D "Universo MyTickets" banner, the scroll-driven video and sale alerts |
| `eventos/<slug>/`, `en/events/<slug>/`, `es/eventos/<slug>/` | One guide page per event and language |
| `futebol/`, `cidades/<city>/`, `competicoes/<competition>/` (and `en/`, `es/` equivalents) | Hub pages per sport, city and competition. Generated automatically when a group has at least `MIN_HUB` (2) events |
| `sitemap.xml` | Sitemap index pointing to `sitemap-paginas.xml`, `sitemap-esportes.xml`, `sitemap-shows.xml` and `sitemap-guias.xml` |
| `robots.txt`, `<key>.txt` | For search engines; the `.txt` file is the public IndexNow key |

All pages are generated. Do not edit them by hand.

## Updating events

1. Edit `data/eventos.json`. The `id` is the SportsEvents365 event number (`/event/<id>`).
2. Run `python scripts/gerar_paginas.py`.
3. Commit and push. Every push to `main` publishes to mytickets.tours (Azure) and to the GitHub Pages mirror.

Past events are dropped automatically the next time the script runs.

## SEO and measurement

- Every event page carries `SportsEvent`/`MusicEvent` JSON-LD (venue address and coordinates from `LOCAIS` in the generator, ISO country code, teams or artist, organizer, partner checkout as the offer) plus `BreadcrumbList`. Hubs carry `ItemList`; home pages carry `Organization` and `WebSite`. New venues need an entry in `LOCAIS`.
- `lastmod` in the sitemaps only changes when a page's content changes (hashes kept in `data/lastmod.json`).
- On every push to `main`, `scripts/indexnow.py` sends the changed URLs to IndexNow (Bing, Yandex and others). Google reads the sitemap submitted once in Search Console.
- Measurement: set `GTM_ID` (or `GA_MEASUREMENT_ID`) in the generator. A Consent Mode v2 cookie banner appears automatically. The site pushes `view_item`, `begin_checkout`, `affiliate_click` and `generate_lead` to the `dataLayer`. Mark `affiliate_click` as the key event.
- Search Console: verify the domain by DNS, or set `GSC_VERIFICATION` for the meta tag.

## Editorial content and E-E-A-T

- `scripts/conteudo.py` holds the editorial text in PT/EN/ES: what to bring, best sections for families vs loud support, "how to buy from abroad" steps, the event FAQ, the "How it works and guarantees" page and the linkable guide "Buying tickets in Europe safely". Partner facts (delivery, guarantee, cancellation, emergency line) come from the SportsEvents365 terms, checked 2026-10-15; update `PARCEIRO` there if the terms change.
- Each event in `data/eventos.json` can carry `hora`, `inicio` (ISO with timezone), `conferido` (date the date/time was checked at the partner) and `status`. The page shows "checked on …" and the Event JSON-LD uses the full start time.
- Event pages carry `FAQPage` JSON-LD. Google currently shows FAQ rich results only for government and health sites, so the gain is in content and long-tail matching, not in the rich result itself.
- "More events" on each event page favours the same city and competition first (internal silo), so authority reaching a big match flows to smaller ones on the same topic.

## Partners (aggregator model)

`PARCEIROS` in `scripts/conteudo.py` lists every sales partner. A partner shows on the site only when `"ativo": True` and it has a real affiliate link for the event. Today only Sports Events 365 is active; viagogo, StubHub and Tiqets are listed but switched off until their programs approve the account.

To switch on a new partner after approval:
1. In `data/eventos.json`, add the partner's deeplink to each event it sells: `"links": {"viagogo": "https://..."}` (Sports Events 365 links are built automatically).
2. In `PARCEIROS`, set `"ativo": True` and fill in `selo`, `fatos` (only facts taken from the partner's terms) and `termos`.
3. Run the generator. The event page gets a new card under "Where to buy", the footer and the legal page list the new name, and the button goes through `/go/<partner>/<lang>/<event>/`.

Outbound clicks send `outbound_ticket_click` to GA4 (`partner`, `event_name`, `target_lang`, `click_location`) as well as `affiliate_click`.

## Travel layer ("Plan the trip")

Every event page ends with three cards, in the page's language and already filled with the event's city and dates: hotels (Booking.com, check-in the day before and check-out the day after), transport within Europe (Omio; the card is skipped for events outside Europe) and tours/activities (GetYourGuide, stadium tour + city). `VIAGEM` in `scripts/conteudo.py` holds the texts and the affiliate field of each partner.

- With `"id": ""` (today) the links are plain external links (`rel="nofollow noopener"`) and the section says the site earns nothing on them. They are still useful to the reader, which is the point for SEO.
- After joining Travelpayouts (Booking, Omio, GetYourGuide in one account) or each program directly, paste the affiliate id (Booking `aid`, Travelpayouts `marker`, GetYourGuide `partner_id`) into `"id"`. The generator then routes the card through `/go/<partner>/<lang>/<event>/`, marks it `rel="sponsored"` and switches the disclosure line. Clicks are measured as `travel_click` in GA4 (`partner`, `click_location`).

## Ticket partners waiting for approval

`PARCEIROS` now also lists P1 Travel (Partnerize; single tickets and ticket + hotel packages for European football, F1, MotoGP, Roland-Garros and concerts) and SuperIngressos (CJ/Awin/Webgains; Portuguese-speaking seller for NBA, NFL, MLB, NHL, MLS and US concerts). Both are `"ativo": False`. The switch-on steps are the same as above: deeplink per event in `data/eventos.json` under `"links"`, then `ativo`, `fatos` and `termos`.

## YouTube videos (works like a blog)

`data/videos.json` lists the videos shown on the site. Each one carries `yt` (the 11-character YouTube id), `titulo`, `idioma`, `publicado`, an optional `evento` (slug) and an optional `cta`. Where they appear:

- Event page: the first video linked to the event replaces the "coming soon" short slot (vertical, with the "See tickets" button under it); further videos appear in an "On video" strip. The page gets `VideoObject` JSON-LD.
- `/videos/`, `/en/videos/`, `/es/videos/`: all videos, newest first, each with its button. The page and the footer link only exist when there is at least one video.
- Home: an "On video" strip with the last three.

The player is a facade: a static thumbnail from `i.ytimg.com` and a play button; the `youtube-nocookie.com` iframe is created only on click (`assets/site.js`), so pages load nothing from YouTube until the visitor asks. Plays are measured as `video_start`.

Buttons per `cta.tipo`: `evento` → tickets for the linked event (`/go/se365/…`); `viagem` + `parceiro` (`booking`, `omio`, `getyourguide`) → the travel link for the event; `url` → any link you give (`rotulo` per language; `afiliado: false` drops `rel="sponsored"`). Videos linked to an event also get a "See event guide" button.

`.github/workflows/videos.yml` runs every 6 hours: `scripts/videos.py` reads the channel's public RSS feed (channel id `UCIUejr6o9Rdvsg_07x6kziA`, override with the repository variable `YOUTUBE_CHANNEL_ID`), appends new videos with the language guessed from the title and the event matched by team/artist/city names, regenerates the site and publishes. It never rewrites entries already in the JSON, so edit `evento`, `cta` or `ativo` freely.

## Sale monitor (Scrapling) and sale alerts

`scripts/vendas.py` reads, every 3 hours (`.github/workflows/vendas.yml`), the official ticket page of each event (`VENDA_OFICIAL` in `scripts/conteudo.py`: FC Barcelona, AC Milan, FIGC, FFR, Yas Marina, Knicks, Australian Open, Celine Dion, UEFA) plus the partner's stock from `data/precos.json`, and writes `data/vendas.json`: per event, `oficial` (status `a_venda` / `em_breve` / `esgotado` / `desconhecido`, confidence, the snippet that decided it, HTTP code, engine) and `parceiro` (listings and lowest price), plus `mudancas`, the last status transitions. The event page shows a "Sales" fact line only when the official status has confidence ≥ 0.5 or the partner has stock.

Pages are fetched with Scrapling's `Fetcher` (browser-like headers and TLS, no browser). Set the repository variable `SCRAPLING_STEALTH=1` and add `scrapling install` to the workflow to use the `StealthyFetcher` (headless browser) for pages that block plain HTTP clients. Without Scrapling the script falls back to `urllib`. Classification looks for status words in several languages inside ~400-character windows around the event's keywords; without such a window it uses the whole page with low confidence, and without any signal it stays `desconhecido`.

The scheduled task "Alertas de venda" (Claude, daily) reads `mudancas`, and when an event turned `a_venda` it matches the sale-alert sign-ups that FormSubmit delivers to the site inbox (subject "Alerta de venda: …", fields `email`, `evento_slug`, `idioma_alertas`) and leaves one Gmail draft per subscriber, in their language, for the owner to approve. Nothing is sent automatically.

## Scam alerts and reports

`data/artigos.json` holds the articles of `/alertas-de-golpe/` (`/en/scam-alerts/`, `/es/alertas-de-estafas/`): one page per article and language with `Article` JSON-LD (author = `RESPONSAVEL`), the events it mentions and sources. Rules written in the file: facts only; a site or company named as a scam needs evidence (screenshot, URL, date) and factual wording; reader reports are published anonymised. Every article page and the hub carry the "Report a suspicious page" form, which posts to the same FormSubmit endpoint (subject "Denúncia de página suspeita: …", fields `url_suspeita`, `relato`, `evento_slug`, `email`) and lands in the site inbox; nothing is published automatically. Event pages link to the hub next to the guide links.

## Videos: autoplay in view

Video blocks (`.yt`) start muted when at least half of the block is visible, pause when it leaves, and one tap turns the sound on (other playing videos are muted). YouTube videos load through `youtube-nocookie.com` only at that moment; local shorts in `assets/videos/short-<event>[-en|-es].mp4` are used when the event has no YouTube video in that language. Users with `prefers-reduced-motion` or Data Saver get the thumbnail and play on tap.

## Affiliate links

- Deeplinks follow the panel's Deeplink generator format, on the partner's site in the page's language: `365tickets.com.br` (PT), `www.sportsevents365.com` (EN), `sportsevents365.es` (ES). The localized domains are the partner's own (hreflang) and the 365tickets.com.br click showed up in the panel's Raw Clicks report. Sending each visitor to a site already in their language stops Chrome's automatic translation, which breaks the partner's pages a few seconds after they load.
- SubID: `assets/site.js` adds `data1` (where on the page the click happened: board, event_cta_top, event_cta, explore, header, footer…) and `data2` (which page) at click time. See them in the panel's SubID / commissions report. The WhatsApp catalogue links carry `data1=whatsapp&data2=<lang>`.
- Link protector: ticket buttons point to `/ir/<event id>/`, a redirect page generated by the script (the equivalent of the panel's "Affiliate link protector / cloaker"). It forwards the SubID and is blocked in robots.txt and with `X-Robots-Tag`.
- The partner's sport pages (`/events/type/<code>`) wipe their own event list after loading (checked 2026-10-15), so sport buttons use our hub or a working competition page (`DOCK_ESPORTE` in the generator).

Every ticket link goes straight to the matching event, competition, team, city or artist page on sportsevents365.com, with `a_aid=6821d72fcdbe3`.

## Assets

- `assets/site.css`, `assets/site.js`: design, split-flap board, parallax, scroll video, liquid cursor and magnetic buttons.
- `assets/solar.js`, `assets/solar-banner.css`: the original 3D solar-system banner, unchanged.
- `assets/img/`: the banners from the previous portal version.
- To use a real vertical video in the scroll section, add `data-video="path/to/video.mp4"` to the home page `<body>` in the generator.

## News robot

`.github/workflows/noticias.yml` updates `dados.json` every hour and republishes the site. The home pages show one news block per country, ordered by GA4 visitors when configured.

## Headers and security

`staticwebapp.config.json` sets the security headers served by Azure (HSTS, Content-Security-Policy, Permissions-Policy, X-Frame-Options, COOP) and long caching for `/assets/*` (asset URLs are versioned with `?v=<hash>`, so a changed file is always re-fetched). When a new third-party script or host is added to the pages, add it to the CSP too, or the browser will block it.

## Hosting

The official site is https://mytickets.tours, served by the Azure Static Web App `app-mytickets-tours` (Free plan). Both workflows deploy there on every push and every hourly news update, using the `AZURE_STATIC_WEB_APPS_API_TOKEN` secret. `/tickets` redirects to the partner for old links (see `staticwebapp.config.json`). GitHub Pages keeps a mirror; canonical URLs point to mytickets.tours.

## Still to do

- Add the WhatsApp channel links. The alert form posts to FormSubmit and lands in email@mytickets.tours.
- Add the GA4 secrets (`GA4_PROPERTY_ID`: 559145785) for the news ranking. The site measures with GA4 `G-FCTZZX96NW` behind a Consent Mode v2 banner.

## Affiliate disclosure

Purchases through affiliate links may earn the operator a commission at no extra cost to the buyer. Availability, prices and purchase terms are set by the supplier.

## License

MIT. Third-party trademarks and linked supplier content keep their respective rights.

## Pinterest

- Páginas de evento e de guia têm o botão "Salvar no Pinterest" (`botoes_pinterest` em `scripts/gerar_paginas.py`).
  Sem o script do Pinterest ele é um link comum para `pinterest.com/pin/create/button/`.
- `assets/site.js` só carrega `pinit.js` (uma vez) quando a página tem botão do Pinterest **e** o visitante aceitou os cookies.
  A home e as páginas institucionais não carregam o script.
- Toda página tem `og:image` (imagem do evento ou `OG_PADRAO`), que o Pinterest usa ao salvar.
- Cliques no botão viram o evento `share` (method `pinterest`) no GA4.
- Para ligar o botão Seguir: preencha `PINTEREST_PERFIL` (o nome em pinterest.com/<perfil>/).
- Para reivindicar o site no Pinterest: preencha `PINTEREST_VERIFY` com o código da meta tag `p:domain_verify`.

### Pins automáticos (site → Pinterest)

- O gerador desenha a arte vertical (1000×1500) de cada evento e guia, nos 3 idiomas, em `assets/pins/` (`scripts/pins.py`).
- `.github/workflows/pinterest.yml` roda depois de cada publicação do site e uma vez por dia: cria até 3 pins novos
  por execução e atualiza o título, a descrição e o link dos pins que mudaram. `data/pins.json` guarda o que já foi publicado.
- O pin leva à página do evento no site (com `utm_source=pinterest`), não direto ao link de afiliado.
- Para ligar: crie os quadros, rode `python scripts/pins.py quadros` (com um token) para ver os IDs, preencha
  `data/pinterest.json` (`ativo: true` e o quadro de cada idioma) e cadastre os segredos `PINTEREST_APP_ID`,
  `PINTEREST_APP_SECRET`, `PINTEREST_REFRESH_TOKEN` e, de preferência, `GH_PAT` (grava o refresh token renovado).
- Enquanto o app estiver em "Trial access", o Pinterest cria os pins só como rascunho de teste, visíveis só para você.
  Pins públicos exigem "Standard access" (pedido no painel de apps, com um vídeo do fluxo de login).
