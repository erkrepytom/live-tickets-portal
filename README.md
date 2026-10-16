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
