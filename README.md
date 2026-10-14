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
3. Commit and push. GitHub Pages publishes on every push to `main`.

Past events are dropped automatically the next time the script runs.

## Affiliate links

Every ticket link goes straight to the matching event, competition, team, city or artist page at the partner, with `a_aid=6821d72fcdbe3`. Each language uses the partner's own site: `365tickets.com.br` (PT), `sportsevents365.com` (EN) and `sportsevents365.es` (ES).

## Assets

- `assets/site.css`, `assets/site.js`: design, split-flap board, parallax, scroll video, liquid cursor and magnetic buttons.
- `assets/solar.js`, `assets/solar-banner.css`: the original 3D solar-system banner, unchanged.
- `assets/img/`: the banners from the previous portal version.
- To use a real vertical video in the scroll section, add `data-video="path/to/video.mp4"` to the home page `<body>` in the generator.

## News robot

`.github/workflows/noticias.yml` updates `dados.json` every hour. The Portuguese home page shows those headlines.

## Before going live on mytickets.tours

- Point the domain at GitHub Pages and change `BASE_URL` in `scripts/gerar_paginas.py`.
- Connect the alert form to an email provider and add the WhatsApp channel links.

## Affiliate disclosure

Purchases through affiliate links may earn the operator a commission at no extra cost to the buyer. Availability, prices and purchase terms are set by the supplier.

## License

MIT. Third-party trademarks and linked supplier content keep their respective rights.
