# MyTickets Tours

Affiliate portal for international sports and show tickets, in Portuguese, English and Spanish. Tickets are sold and delivered by SportsEvents365.

## Pages

| Path | What it is |
|---|---|
| `index.html`, `en/`, `es/` | Home pages: departures board, featured events, explore by sport, city and artist, the 3D "Universo MyTickets" banner, the scroll-driven video and sale alerts |
| `eventos/<slug>/`, `en/events/<slug>/`, `es/eventos/<slug>/` | One guide page per event and language |
| `sitemap.xml`, `robots.txt` | For search engines |

All pages are generated. Do not edit them by hand.

## Updating events

1. Edit `data/eventos.json`. The `id` is the SportsEvents365 event number (`/event/<id>`).
2. Run `python scripts/gerar_paginas.py`.
3. Commit and push. Every push to `main` publishes to mytickets.tours (Azure) and to the GitHub Pages mirror.

Past events are dropped automatically the next time the script runs.

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
- Add `GA_MEASUREMENT_ID` and the GA4 secrets, with a cookie consent banner.

## Affiliate disclosure

Purchases through affiliate links may earn the operator a commission at no extra cost to the buyer. Availability, prices and purchase terms are set by the supplier.

## License

MIT. Third-party trademarks and linked supplier content keep their respective rights.
