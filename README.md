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
- Add `GTM_ID` or `GA_MEASUREMENT_ID` (the consent banner is already built in) and the GA4 secrets.

## Affiliate disclosure

Purchases through affiliate links may earn the operator a commission at no extra cost to the buyer. Availability, prices and purchase terms are set by the supplier.

## License

MIT. Third-party trademarks and linked supplier content keep their respective rights.
