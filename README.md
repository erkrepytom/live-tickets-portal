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

## Affiliate links

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
