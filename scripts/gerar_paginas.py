"""Gera o site MyTickets Tours em PT, EN e ES a partir de data/eventos.json.

Uso: python scripts/gerar_paginas.py
Saída: index.html, en/index.html, es/index.html, uma página por evento e idioma,
sitemap.xml e robots.txt. Os links de ingresso apontam direto para o evento ou a
categoria no site do parceiro, sempre com o código de afiliado.
"""
import datetime as dt
import hashlib
import html
import json
import urllib.parse
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import conteudo as C  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# Troque para https://mytickets.tours quando o domínio apontar para o GitHub Pages.
BASE_URL = "https://mytickets.tours"
AFILIADO = "6821d72fcdbe3"
# Todos os idiomas usam o site principal do parceiro, onde o a_aid é contabilizado.
# Site do parceiro no idioma de cada página. São os domínios oficiais que o próprio parceiro indica
# (hreflang) e que repassam o a_aid; o clique pelo 365tickets.com.br apareceu no relatório "Raw Clicks"
# do painel em 15/10/2026. Usar o idioma certo evita a tradução automática do Chrome, que quebra o
# site do parceiro ("não conseguimos encontrar esse evento" alguns segundos depois de abrir).
PARCEIRO = {"pt": "https://365tickets.com.br", "en": "https://www.sportsevents365.com", "es": "https://sportsevents365.es"}
IDIOMAS = ["pt", "en", "es"]
# Formulário de alertas: o FormSubmit entrega cada cadastro como e-mail na caixa do Titan.
# Coloque aqui https://formsubmit.co/ajax/<seu-email-titan> (ou o código aleatório que o
# FormSubmit envia depois da ativação). Vazio = formulário mostra "em breve".
FORM_ENDPOINT = "https://formsubmit.co/ajax/email@mytickets.tours"
# ID de medição do Google Analytics 4 (G-XXXXXXX). Vazio = sem Analytics no site.
GA_MEASUREMENT_ID = "G-FCTZZX96NW"
# Contêiner do Google Tag Manager (GTM-XXXXXXX). Se preenchido, substitui o gtag direto:
# o GA4 e o Google Ads passam a ser configurados dentro do GTM. Os eventos do site
# (view_item, begin_checkout, affiliate_click, generate_lead) vão para o dataLayer nos dois casos.
GTM_ID = ""
# Código da meta tag de verificação do Google Search Console (só o valor de content="...").
# Vazio = verificação feita por DNS (recomendado para a propriedade de domínio).
GSC_VERIFICATION = ""
# Pinterest. PINTEREST_PERFIL = nome do perfil (pinterest.com/<perfil>/) liga o botão Seguir.
# PINTEREST_VERIFY = código da meta tag p:domain_verify, para reivindicar o site no Pinterest.
PINTEREST_PERFIL = "Sportseventstickets"
PINTEREST_VERIFY = ""
OG_PADRAO = "06-champions.jpg"
PIN_TXT = {"pt": ("Salvar no Pinterest", "Seguir no Pinterest"), "en": ("Save to Pinterest", "Follow on Pinterest"),
           "es": ("Guardar en Pinterest", "Seguir en Pinterest")}
# Chave pública do IndexNow (Bing, Yandex, Seznam, Naver). O arquivo <chave>.txt fica na raiz.
INDEXNOW_KEY = "3fd2b7b8fea97fff39010e15706a1aff"
# Uma página-hub (esporte, cidade, competição) só é gerada com pelo menos este número de eventos,
# para não criar páginas finas. Quando o catálogo crescer, os hubs aparecem sozinhos.
MIN_HUB = 2
HREFLANG = {"pt": "pt-BR", "en": "en", "es": "es"}
# Ordem em que os idiomas aparecem para o visitante (seletor do topo, rodapé e formulário de alertas).
ORDEM_MENU = ["en", "es", "pt"]

# Endereço e coordenadas de cada local, para o JSON-LD de Event (Google Eventos).
# A chave é o campo "local" de data/eventos.json. Local sem cadastro aqui usa só cidade e país.
LOCAIS = {
 "Camp Nou": {"rua": "C. d'Arístides Maillol, 12", "cep": "08028", "cidade": "Barcelona", "regiao": "Catalunya", "geo": (41.3809, 2.1228)},
 "San Siro (Giuseppe Meazza)": {"rua": "Piazzale Angelo Moratti", "cep": "20151", "cidade": "Milano", "regiao": "Lombardia", "geo": (45.4781, 9.1240)},
 "Stade de France": {"rua": "ZAC du Cornillon Nord", "cep": "93200", "cidade": "Saint-Denis", "regiao": "Île-de-France", "geo": (48.9245, 2.3602)},
 "Yas Marina Circuit": {"rua": "Yas Island", "cep": "", "cidade": "Abu Dhabi", "regiao": "Abu Dhabi", "geo": (24.4672, 54.6031)},
 "Madison Square Garden": {"rua": "4 Pennsylvania Plaza", "cep": "10001", "cidade": "New York", "regiao": "NY", "geo": (40.7505, -73.9934)},
 "Rod Laver Arena": {"rua": "Olympic Blvd, Melbourne Park", "cep": "3001", "cidade": "Melbourne", "regiao": "VIC", "geo": (-37.8216, 144.9785)},
 "Paris La Défense Arena": {"rua": "99 Jardin de l'Arche", "cep": "92000", "cidade": "Nanterre", "regiao": "Île-de-France", "geo": (48.8957, 2.2297)},
 "Estadio Metropolitano": {"rua": "Av. de Luis Aragonés, 4", "cep": "28022", "cidade": "Madrid", "regiao": "Comunidad de Madrid", "geo": (40.4362, -3.5995)},
}
# País (nome em inglês do campo "pais") → código ISO 3166-1, o formato que o Google prefere.
PAIS_ISO = {"Spain": "ES", "Italy": "IT", "France": "FR", "United Arab Emirates": "AE", "USA": "US", "United States": "US",
            "Australia": "AU", "United Kingdom": "GB", "Germany": "DE", "Netherlands": "NL", "Portugal": "PT", "Brazil": "BR"}
FOTO_TOPO = "hero.jpg"  # imagens locais ficam em assets/img (banners do portal anterior)

T = {
 "pt": {
  "brand_title": "MyTickets Tours | Ingressos para esporte e shows no mundo todo",
  "home_desc": "Ingressos para La Liga, Serie A, Champions League, NBA, Fórmula 1, tênis e shows internacionais, com o guia de cada evento. Venda e entrega pela SportsEvents365.",
  "nav": ["Partidas", "Explorar", "Como funciona", "Alertas"], "cta": "Ver ingressos",
  "hero_kicker": "Ingressos para esporte e shows no mundo todo", "hero_l1": "PARTIDAS PARA", "hero_l2": "O JOGO", "hero_h1": "Partidas para o jogo",
  "hero_sub": "Escolha o evento, entenda a viagem e compre num parceiro com garantia de entrega. Em português, inglês e espanhol.",
  "hero_cta2": "Receber alertas", "hero_note": "Guia independente de ingressos. Você compra no site do parceiro: {parceiros}.", "gate": "PORTÃO",
  "board_kicker": "Painel de partidas", "board_h": "Próximas partidas",
  "board_sub": "Toque no nome para ver o guia do evento, ou em embarque para ir direto aos ingressos.",
  "cols": ["QUANDO", "EVENTO", "CIDADE", "STATUS"], "go": "EMBARQUE",
  "board_foot": "Datas do catálogo do parceiro. Confira data, horário, setor e preço final antes de pagar.", "local_time": "Hora local",
  "feat_kicker": "Em destaque", "feat_h": "Os próximos embarques", "feat_sub": "As três datas mais próximas, com guia completo.",
  "exp_kicker": "Explorar", "exp_h": "Por esporte, cidade e artista", "exp_sub": "Cada nome abre a página certa no catálogo do parceiro.",
  "g_sports": "Esportes", "g_comp": "Ligas e campeonatos", "g_teams": "Times", "g_cities": "Cidades", "g_music": "Shows e artistas",
  "solar_k": "Universo MyTickets", "solar_h": "Todo esporte gira em torno de um <span>grande evento</span>",
  "how_kicker": "Como funciona", "how_h": "Do vídeo à arquibancada",
  "steps": [("Assista", "Vídeos curtos sobre um evento específico, no Shorts, Reels e TikTok, em português, inglês e espanhol."),
            ("Entenda", "Cada vídeo leva à página do evento: data, estádio, como chegar e dicas de setor."),
            ("Garanta", "O ingresso é vendido e entregue pela SportsEvents365. Você vê setor e preço antes de pagar.")],
  "reel_cap": "Barça x Real Madrid no Camp Nou: como conseguir ingresso", "reel_link": "LINK NA BIO → PÁGINA DO EVENTO", "admit": "ENTRADA · 1",
  "news_kicker": "Notícias pelo mundo", "news_h": "O que está em alta", "news_sub": "Manchetes de veículos de cada país sobre os esportes e eventos do site, priorizando os assuntos mais buscados. Atualizado a cada hora.", "hot": "EM ALTA",
  "alerts_kicker": "Alertas de venda", "alerts_h": "Avise-me quando abrir",
  "alerts_sub": "Um e-mail quando a venda do seu evento abrir. Sem spam, e você cancela com um clique.",
  "f_email": "Seu e-mail", "f_event": "Evento", "f_lang": "Idioma dos alertas", "ph_email": "voce@email.com",
  "f_consent": "Aceito receber e-mails do MyTickets sobre este evento. Posso cancelar quando quiser.", "f_submit": "Quero o alerta",
  "f_soon": "O cadastro de alertas abre em breve. Nada foi enviado ainda.", "f_err": "Digite um e-mail válido e marque o consentimento.",
  "f_done": "Pronto. Você vai receber um e-mail quando a venda abrir.", "f_fail": "Não deu para enviar agora. Tente de novo em alguns minutos.",
  "f_sending": "Enviando…", "f_privacy": "Usamos o FormSubmit só para entregar seu cadastro na caixa de e-mail do MyTickets. Seu e-mail serve apenas para este alerta.",
  "wa_kicker": "WhatsApp", "wa_h": "Canais oficiais", "wa_sub": "Novidades de venda num canal só nosso, no seu idioma. Nunca pedimos pagamento ou dados por mensagem.", "soon": "Em breve",
  "foot_disc": "Divulgação: o MyTickets Tours é um site afiliado. Quando você compra pelos nossos links, podemos receber comissão da SportsEvents365, sem custo extra para você. Ingressos, preços e entrega são de responsabilidade do parceiro.",
  "aff_note": "Link de afiliado: o MyTickets pode receber comissão, sem custo extra para você.",
  "home": "Início", "events": "Partidas", "f_date": "Data", "f_venue": "Local", "f_city": "Cidade", "f_comp": "Competição", "f_artist": "Artista",
  "ev_cta": "Ver ingressos no parceiro", "ev_alert": "Avisar quando abrir a venda", "get_h": "Como chegar", "tips_h": "Dicas de setor",
  "also": "Veja também no parceiro", "more_k": "Mais partidas", "more_h": "Outros embarques",
  "short_tag": "SHORT · PT · EM BREVE", "short_t": "Como ver {t} saindo do Brasil",
  "ev_title": "{t}: ingressos e guia | MyTickets Tours", "ev_desc": "Ingressos para {t} em {d}, {v}, {c}. Como chegar, dicas de setor e compra em parceiro com garantia de entrega.",
  "date_note": "Data do catálogo do parceiro. O horário é confirmado pelo organizador.",
 },
 "en": {
  "brand_title": "MyTickets Tours | Tickets for sports and shows worldwide",
  "home_desc": "Tickets for La Liga, Serie A, the Champions League, NBA, Formula 1, tennis and concerts worldwide, with a guide to every event. Sold and delivered by SportsEvents365.",
  "nav": ["Departures", "Explore", "How it works", "Alerts"], "cta": "See tickets",
  "hero_kicker": "Tickets for sports and shows worldwide", "hero_l1": "DEPARTURES TO", "hero_l2": "THE GAME", "hero_h1": "Departures to the game",
  "hero_sub": "Pick the event, plan the trip and buy from a partner with a delivery guarantee. In Portuguese, English and Spanish.",
  "hero_cta2": "Get alerts", "hero_note": "Independent ticket guide. You buy on the partner's site: {parceiros}.", "gate": "GATE",
  "board_kicker": "Departures board", "board_h": "Next departures",
  "board_sub": "Tap a name for the event guide, or tap boarding to go straight to tickets.",
  "cols": ["WHEN", "EVENT", "CITY", "STATUS"], "go": "BOARDING",
  "board_foot": "Dates from the partner's catalogue. Check the date, time, section and final price before paying.", "local_time": "Local time",
  "feat_kicker": "Featured", "feat_h": "Boarding soon", "feat_sub": "The three nearest dates, each with a full guide.",
  "exp_kicker": "Explore", "exp_h": "By sport, city and artist", "exp_sub": "Every name opens the right page in the partner's catalogue.",
  "g_sports": "Sports", "g_comp": "Leagues and competitions", "g_teams": "Teams", "g_cities": "Cities", "g_music": "Concerts and artists",
  "solar_k": "MyTickets Universe", "solar_h": "Every sport revolves around a <span>big event</span>",
  "how_kicker": "How it works", "how_h": "From the video to the stands",
  "steps": [("Watch", "Short videos about one specific event, on Shorts, Reels and TikTok, in Portuguese, English and Spanish."),
            ("Plan", "Every video leads to the event page: date, stadium, getting there and seating tips."),
            ("Book", "Tickets are sold and delivered by SportsEvents365. You see the section and price before you pay.")],
  "reel_cap": "Barça vs Real Madrid at Camp Nou: how to get tickets", "reel_link": "LINK IN BIO → EVENT PAGE", "admit": "ADMIT · 1",
  "news_kicker": "News around the world", "news_h": "What's trending", "news_sub": "Headlines from each country's own outlets about the sports and events on this site, led by the most searched topics. Updated hourly.", "hot": "TRENDING",
  "alerts_kicker": "Sale alerts", "alerts_h": "Tell me when it opens",
  "alerts_sub": "One email when sales for your event open. No spam, and you can unsubscribe in one click.",
  "f_email": "Your email", "f_event": "Event", "f_lang": "Alert language", "ph_email": "you@email.com",
  "f_consent": "I agree to receive MyTickets emails about this event. I can unsubscribe at any time.", "f_submit": "Get the alert",
  "f_soon": "Alert sign-up opens soon. Nothing was sent yet.", "f_err": "Enter a valid email and tick the consent box.",
  "f_done": "Done. You will get an email when sales open.", "f_fail": "We couldn't send it right now. Try again in a few minutes.",
  "f_sending": "Sending…", "f_privacy": "We use FormSubmit only to deliver your sign-up to the MyTickets inbox. Your email is used for this alert only.",
  "wa_kicker": "WhatsApp", "wa_h": "Official channels", "wa_sub": "Sale news in a channel that is ours alone, in your language. We never ask for payment or personal data by message.", "soon": "Coming soon",
  "foot_disc": "Disclosure: MyTickets Tours is an affiliate site. When you buy through our links we may earn a commission from SportsEvents365 at no extra cost to you. Tickets, prices and delivery are the partner's responsibility.",
  "aff_note": "Affiliate link: MyTickets may earn a commission at no extra cost to you.",
  "home": "Home", "events": "Departures", "f_date": "Date", "f_venue": "Venue", "f_city": "City", "f_comp": "Competition", "f_artist": "Artist",
  "ev_cta": "See tickets at the partner", "ev_alert": "Tell me when sales open", "get_h": "Getting there", "tips_h": "Seating tips",
  "also": "Also at the partner", "more_k": "More departures", "more_h": "Other events",
  "short_tag": "SHORT · EN · COMING SOON", "short_t": "How to see {t} from abroad",
  "ev_title": "{t}: tickets and guide | MyTickets Tours", "ev_desc": "Tickets for {t} on {d} at {v}, {c}. Getting there, seating tips and booking with a partner that guarantees delivery.",
  "date_note": "Date from the partner's catalogue. Start time is confirmed by the organizer.",
 },
 "es": {
  "brand_title": "MyTickets Tours | Entradas para deportes y shows en todo el mundo",
  "home_desc": "Entradas para La Liga, Serie A, Champions League, NBA, Fórmula 1, tenis y conciertos internacionales, con la guía de cada evento. Venta y entrega por SportsEvents365.",
  "nav": ["Salidas", "Explorar", "Cómo funciona", "Alertas"], "cta": "Ver entradas",
  "hero_kicker": "Entradas para deportes y shows en todo el mundo", "hero_l1": "SALIDAS HACIA", "hero_l2": "EL PARTIDO", "hero_h1": "Salidas hacia el partido",
  "hero_sub": "Elige el evento, planea el viaje y compra en un socio con garantía de entrega. En portugués, inglés y español.",
  "hero_cta2": "Recibir alertas", "hero_note": "Guía independiente de entradas. Compras en el sitio del socio: {parceiros}.", "gate": "PUERTA",
  "board_kicker": "Panel de salidas", "board_h": "Próximas salidas",
  "board_sub": "Toca el nombre para ver la guía del evento, o embarque para ir directo a las entradas.",
  "cols": ["CUÁNDO", "EVENTO", "CIUDAD", "ESTADO"], "go": "EMBARQUE",
  "board_foot": "Fechas del catálogo del socio. Confirma fecha, hora, sector y precio final antes de pagar.", "local_time": "Hora local",
  "feat_kicker": "Destacados", "feat_h": "Próximos embarques", "feat_sub": "Las tres fechas más cercanas, con guía completa.",
  "exp_kicker": "Explorar", "exp_h": "Por deporte, ciudad y artista", "exp_sub": "Cada nombre abre la página correcta en el catálogo del socio.",
  "g_sports": "Deportes", "g_comp": "Ligas y competiciones", "g_teams": "Equipos", "g_cities": "Ciudades", "g_music": "Conciertos y artistas",
  "solar_k": "Universo MyTickets", "solar_h": "Todo deporte gira en torno a un <span>gran evento</span>",
  "how_kicker": "Cómo funciona", "how_h": "Del video a la grada",
  "steps": [("Mira", "Videos cortos sobre un evento concreto, en Shorts, Reels y TikTok, en portugués, inglés y español."),
            ("Entiende", "Cada video lleva a la página del evento: fecha, estadio, cómo llegar y consejos de sector."),
            ("Asegura", "La entrada la vende y entrega SportsEvents365. Ves sector y precio antes de pagar.")],
  "reel_cap": "Barça vs Real Madrid en el Camp Nou: cómo conseguir entradas", "reel_link": "LINK EN LA BIO → PÁGINA DEL EVENTO", "admit": "ENTRADA · 1",
  "news_kicker": "Noticias por el mundo", "news_h": "Lo más buscado", "news_sub": "Titulares de medios de cada país sobre los deportes y eventos del sitio, empezando por los temas más buscados. Se actualiza cada hora.", "hot": "EN ALZA",
  "alerts_kicker": "Alertas de venta", "alerts_h": "Avísame cuando abra",
  "alerts_sub": "Un correo cuando abra la venta de tu evento. Sin spam, y te das de baja con un clic.",
  "f_email": "Tu correo", "f_event": "Evento", "f_lang": "Idioma de las alertas", "ph_email": "tu@correo.com",
  "f_consent": "Acepto recibir correos de MyTickets sobre este evento. Puedo darme de baja cuando quiera.", "f_submit": "Quiero la alerta",
  "f_soon": "El registro de alertas abre pronto. Todavía no se envió nada.", "f_err": "Escribe un correo válido y marca el consentimiento.",
  "f_done": "Listo. Recibirás un correo cuando abra la venta.", "f_fail": "No se pudo enviar ahora. Inténtalo de nuevo en unos minutos.",
  "f_sending": "Enviando…", "f_privacy": "Usamos FormSubmit solo para entregar tu registro en el correo de MyTickets. Tu correo se usa solo para esta alerta.",
  "wa_kicker": "WhatsApp", "wa_h": "Canales oficiales", "wa_sub": "Novedades de venta en un canal solo nuestro, en tu idioma. Nunca pedimos pagos ni datos por mensaje.", "soon": "Próximamente",
  "foot_disc": "Aviso: MyTickets Tours es un sitio afiliado. Cuando compras con nuestros enlaces podemos recibir una comisión de SportsEvents365 sin costo extra para ti. Entradas, precios y entrega son responsabilidad del socio.",
  "aff_note": "Enlace de afiliado: MyTickets puede recibir una comisión sin costo extra para ti.",
  "home": "Inicio", "events": "Salidas", "f_date": "Fecha", "f_venue": "Recinto", "f_city": "Ciudad", "f_comp": "Competición", "f_artist": "Artista",
  "ev_cta": "Ver entradas en el socio", "ev_alert": "Avisarme cuando abra la venta", "get_h": "Cómo llegar", "tips_h": "Consejos de sector",
  "also": "También en el socio", "more_k": "Más salidas", "more_h": "Otros eventos",
  "short_tag": "SHORT · ES · PRÓXIMAMENTE", "short_t": "Cómo ver {t} desde otro país",
  "ev_title": "{t}: entradas y guía | MyTickets Tours", "ev_desc": "Entradas para {t} el {d} en {v}, {c}. Cómo llegar, consejos de sector y compra en un socio con garantía de entrega.",
  "date_note": "Fecha del catálogo del socio. La hora la confirma el organizador.",
 },
}

DICAS = {
 "football": {"pt": ["Setores laterais dão a melhor visão do campo inteiro.", "Setores altos costumam ter o menor preço.", "Em grupo, compre os lugares no mesmo pedido para sentarem juntos."],
              "en": ["Side sections give the best view of the whole pitch.", "Upper tiers are usually the cheapest.", "For a group, buy all seats in one order so you sit together."],
              "es": ["Los laterales dan la mejor vista de todo el campo.", "Los sectores altos suelen ser los más baratos.", "En grupo, compra todos los asientos en el mismo pedido para sentarse juntos."]},
 "rugby": {"pt": ["Lugares nas laterais, perto do meio-campo, mostram melhor as jogadas.", "Leve casaco: as noites de novembro em Paris são frias.", "Em grupo, compre os lugares no mesmo pedido."],
           "en": ["Side seats near halfway show the play best.", "Bring a coat: November nights in Paris are cold.", "For a group, buy all seats in one order."],
           "es": ["Los asientos laterales cerca de la mitad muestran mejor el juego.", "Lleva abrigo: las noches de noviembre en París son frías.", "En grupo, compra todos los asientos en el mismo pedido."]},
 "f1": {"pt": ["Arquibancadas perto de curvas lentas mostram mais ultrapassagens.", "Confira se o ingresso vale para um dia ou para o fim de semana inteiro.", "Leve protetor auricular."],
        "en": ["Grandstands near slow corners show more overtakes.", "Check whether the ticket covers one day or the whole weekend.", "Bring ear protection."],
        "es": ["Las tribunas cerca de curvas lentas muestran más adelantamientos.", "Comprueba si la entrada vale para un día o para todo el fin de semana.", "Lleva protección para los oídos."]},
 "nba": {"pt": ["Lugares no nível inferior, nas laterais, ficam mais perto da quadra.", "Lugares atrás das cestas costumam ser mais baratos.", "Chegue cedo para ver o aquecimento dos jogadores."],
         "en": ["Lower-level sideline seats are closest to the court.", "Seats behind the baskets are usually cheaper.", "Arrive early to watch warm-ups."],
         "es": ["Los asientos laterales del nivel inferior están más cerca de la pista.", "Los asientos detrás de las canastas suelen ser más baratos.", "Llega temprano para ver el calentamiento."]},
 "tennis": {"pt": ["Confira a sessão no ingresso: a final masculina tem sessão própria.", "Lugares nas laterais da quadra mostram os dois jogadores.", "Leve protetor solar: janeiro é verão em Melbourne."],
            "en": ["Check the session on the ticket: the men's final has its own session.", "Seats along the sides show both players.", "Bring sunscreen: January is summer in Melbourne."],
            "es": ["Revisa la sesión en la entrada: la final masculina tiene sesión propia.", "Los asientos laterales muestran a los dos jugadores.", "Lleva protector solar: enero es verano en Melbourne."]},
 "concert": {"pt": ["Pista fica mais perto do palco; cadeiras mostram o show inteiro.", "Lugares de frente para o palco têm o melhor som.", "Em grupo, compre os lugares no mesmo pedido."],
             "en": ["Floor is closest to the stage; seats show the whole show.", "Seats facing the stage have the best sound.", "For a group, buy all seats in one order."],
             "es": ["La pista está más cerca del escenario; las gradas muestran todo el show.", "Los asientos frente al escenario tienen el mejor sonido.", "En grupo, compra todos los asientos en el mismo pedido."]},
}

TIPO_NOME = {"football": {"pt": "Futebol", "en": "Football", "es": "Fútbol"}, "rugby": {"pt": "Rúgbi", "en": "Rugby", "es": "Rugby"},
             "f1": {"pt": "Automobilismo", "en": "Motor racing", "es": "Automovilismo"}, "nba": {"pt": "Basquete", "en": "Basketball", "es": "Baloncesto"},
             "tennis": {"pt": "Tênis", "en": "Tennis", "es": "Tenis"}, "concert": {"pt": "Show", "en": "Concert", "es": "Concierto"}}

# ---------- Páginas-hub (esporte, cidade, competição) ----------
HUB_PASTA = {"esporte": {"pt": "", "en": "", "es": ""},
             "cidade": {"pt": "cidades/", "en": "cities/", "es": "ciudades/"},
             "competicao": {"pt": "competicoes/", "en": "competitions/", "es": "competiciones/"}}
# Nome do esporte como aparece no título do hub e no slug da URL.
HUB_ESPORTE = {
 "football": {"pt": ("futebol", "futebol"), "en": ("football", "football"), "es": ("fútbol", "futbol")},
 "rugby": {"pt": ("rúgbi", "rugbi"), "en": ("rugby", "rugby"), "es": ("rugby", "rugby")},
 "f1": {"pt": ("Fórmula 1", "formula-1"), "en": ("Formula 1", "formula-1"), "es": ("Fórmula 1", "formula-1")},
 "nba": {"pt": ("NBA e basquete", "basquete"), "en": ("NBA and basketball", "basketball"), "es": ("NBA y baloncesto", "baloncesto")},
 "tennis": {"pt": ("tênis", "tenis"), "en": ("tennis", "tennis"), "es": ("tenis", "tenis")},
 "concert": {"pt": ("shows internacionais", "shows"), "en": ("international concerts", "concerts"), "es": ("conciertos internacionales", "conciertos")},
}
HT = {
 "pt": {"h_esporte": "Ingressos de {x}", "h_cidade": "Ingressos em {x}", "h_competicao": "Ingressos {x}",
        "desc": "{n} eventos com guia completo, como {lista}. Datas, locais, como chegar e compra em parceiro com garantia de entrega.",
        "lead": "{n} eventos com página própria no MyTickets: data, local, como chegar e dicas de setor. A compra acontece na SportsEvents365, com setor e preço visíveis antes do pagamento.",
        "list_h": "Próximas datas", "partner": "Ver todo o catálogo no parceiro", "guides": "Guias no site", "kicker": "Guia de ingressos",
        "c_text": "Usamos cookies do Google Analytics para medir visitas e cliques, só com a sua permissão.", "c_yes": "Aceitar", "c_no": "Recusar", "c_more": "Privacidade"},
 "en": {"h_esporte": "{X} tickets", "h_cidade": "Tickets in {x}", "h_competicao": "{x} tickets",
        "desc": "{n} events with a full guide, including {lista}. Dates, venues, getting there and booking with a partner that guarantees delivery.",
        "lead": "{n} events with their own page on MyTickets: date, venue, getting there and seating tips. Booking happens at SportsEvents365, where you see the section and price before paying.",
        "list_h": "Upcoming dates", "partner": "See the full partner catalogue", "guides": "Guides on the site", "kicker": "Ticket guide",
        "c_text": "We use Google Analytics cookies to measure visits and clicks, only with your permission.", "c_yes": "Accept", "c_no": "Decline", "c_more": "Privacy"},
 "es": {"h_esporte": "Entradas de {x}", "h_cidade": "Entradas en {x}", "h_competicao": "Entradas {x}",
        "desc": "{n} eventos con guía completa, como {lista}. Fechas, recintos, cómo llegar y compra en un socio con garantía de entrega.",
        "lead": "{n} eventos con página propia en MyTickets: fecha, recinto, cómo llegar y consejos de sector. La compra se hace en SportsEvents365, con sector y precio visibles antes de pagar.",
        "list_h": "Próximas fechas", "partner": "Ver todo el catálogo del socio", "guides": "Guías en el sitio", "kicker": "Guía de entradas",
        "c_text": "Usamos cookies de Google Analytics para medir visitas y clics, solo con tu permiso.", "c_yes": "Aceptar", "c_no": "Rechazar", "c_more": "Privacidad"},
}


def slugify(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def montar_hubs(eventos):
    """Agrupa os eventos por esporte, cidade e competição e devolve só os grupos com MIN_HUB eventos ou mais.
    Cada hub: {tipo, chave, nome{lang}, slug{lang}, dock (página do parceiro), eventos}."""
    grupos = {}
    for ev in eventos:
        chaves = [("esporte", ev["tipo"])]
        chaves.append(("cidade", L(ev["cidade"], "en")))
        if ev["tipo"] != "concert":
            chaves.append(("competicao", L(ev["competicao"]["nome"], "en")))
        for tipo, chave in chaves:
            g = grupos.setdefault((tipo, chave), {"tipo": tipo, "chave": chave, "eventos": [], "nome": {}, "slug": {}, "dock": None})
            g["eventos"].append(ev)
            for lang in IDIOMAS:
                if tipo == "esporte":
                    g["nome"][lang], g["slug"][lang] = HUB_ESPORTE[ev["tipo"]][lang]
                    g["dock"] = dock_esporte(ev["esporte_tipo"])
                elif tipo == "cidade":
                    g["nome"][lang] = L(ev["cidade"], lang)
                    g["slug"][lang] = slugify(L(ev["cidade"], lang))
                    g["dock"] = g["dock"] or ev["cidade"].get("dock")
                else:
                    g["nome"][lang] = L(ev["competicao"]["nome"], lang)
                    g["slug"][lang] = slugify(L(ev["competicao"]["nome"], "en"))
                    g["dock"] = g["dock"] or ev["competicao"].get("dock")
    return {k: g for k, g in grupos.items() if len(g["eventos"]) >= MIN_HUB}


def caminho_hub(lang, hub):
    return caminho_home(lang) + HUB_PASTA[hub["tipo"]][lang] + hub["slug"][lang] + "/"


def titulo_hub(lang, hub):
    nome = hub["nome"][lang]
    return HT[lang]["h_" + hub["tipo"]].format(x=nome, X=nome[:1].upper() + nome[1:])


def hub_de(hubs, tipo, chave):
    return hubs.get((tipo, chave))


# As páginas de esporte do parceiro (/events/type/<código>) carregam a lista e logo a apagam
# ("We couldn't find any matching events"), conferido em 15/10/2026 inclusive no menu do próprio parceiro.
# Por isso cada esporte aponta para a página de competição que funciona. Shows (/concerts) funciona.
DOCK_ESPORTE = {1000: "/dock/competition/premier-league", 1001: "/dock/competition/australian-open", 1002: "/dock/competition/nba",
                1003: "/dock/competition/formula-1", 1020: "/dock/competition/world-rugby-nations-championship",
                1005: "/dock/competition/major-league-baseball", 1010: "/dock/competition/nhl", 0: "/concerts"}
# Esporte do botão da home -> tipo dos eventos do site, para usar o guia próprio quando ele existir.
TIPO_DO_CODIGO = {1000: "football", 1001: "tennis", 1002: "nba", 1003: "f1", 1020: "rugby", 0: "concert"}


def dock_esporte(codigo):
    return DOCK_ESPORTE.get(codigo or 0, "/")


ESPORTES = [  # (nome por idioma, código do esporte no parceiro, foto do site anterior)
 ({"pt": "Futebol", "en": "Football", "es": "Fútbol"}, 1000, "10-brazil.jpg"),
 ({"pt": "Tênis", "en": "Tennis", "es": "Tenis"}, 1001, "photo-1554068865-24cecd4e34b8"),
 ({"pt": "Basquete", "en": "Basketball", "es": "Baloncesto"}, 1002, "photo-1546519638-68e109498ffc"),
 ({"pt": "Automobilismo", "en": "Motor racing", "es": "Automovilismo"}, 1003, "01-formula-1.jpg"),
 ({"pt": "Rúgbi", "en": "Rugby", "es": "Rugby"}, 1020, "08-six-nations.jpg"),
 ({"pt": "Beisebol", "en": "Baseball", "es": "Béisbol"}, 1005, "photo-1508344928928-7165b67de128"),
 ({"pt": "Hóquei no gelo", "en": "Ice hockey", "es": "Hockey sobre hielo"}, 1010, "photo-1515703407324-5f753afd8be8"),
 ({"pt": "Shows", "en": "Concerts", "es": "Conciertos"}, 0, "11-concerts.jpg"),
]
COMPETICOES = [("Premier League", "premier-league"), ("La Liga", "la-liga"), ("Serie A", "serie-a"), ("NBA", "nba"),
               ("NHL", "nhl"), ("MLB", "major-league-baseball"), ("Fórmula 1|Formula 1|Fórmula 1", "formula-1")]
TIMES = [("FC Barcelona", "barcelona-fc"), ("AC Milan", "ac-milan"), ("Inter", "inter"), ("AS Roma", "as-roma")]
CIDADES = [("Barcelona|Barcelona|Barcelona", "barcelona"), ("Madri|Madrid|Madrid", "madrid"), ("Roma|Rome|Roma", "rome"),
           ("Milão|Milan|Milán", "milano"), ("Londres|London|Londres", "london"), ("Paris|Paris|París", "paris"),
           ("Amsterdã|Amsterdam|Ámsterdam", "amsterdam"), ("Berlim|Berlin|Berlín", "berlin")]
ARTISTAS = [("Oasis", "oasis"), ("Stevie Wonder", "steviewonder"), ("Andrea Bocelli", "andrea-bocelli"), ("Shakira", "shakira"),
            ("BTS", "bts"), ("Celine Dion", "celine-dion"), ("Backstreet Boys", "backstreet-boys")]  # Dua Lipa saiu: sem shows à venda no parceiro (15/10/2026)

MESES = {"pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"],
         "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
         "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}
MES_CURTO = {"pt": "JAN FEV MAR ABR MAI JUN JUL AGO SET OUT NOV DEZ".split(), "en": "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(),
             "es": "ENE FEB MAR ABR MAY JUN JUL AGO SEP OCT NOV DIC".split()}
DIAS = {"pt": ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"],
        "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "es": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]}

e = html.escape


def L(v, lang):
    """Texto que pode ser único ou por idioma ({'pt':..} ou 'pt|en|es')."""
    if isinstance(v, dict):
        return v[lang]
    if "|" in v:
        return v.split("|")[IDIOMAS.index(lang)]
    return v


def data_longa(iso, lang):
    d = dt.date.fromisoformat(iso)
    dia, mes = DIAS[lang][d.weekday()], MESES[lang][d.month - 1]
    if lang == "en":
        return f"{dia}, {mes} {d.day}, {d.year}"
    return f"{dia}, {d.day} de {mes} de {d.year}"


def data_curta(iso, lang):
    d = dt.date.fromisoformat(iso)
    return f"{d.day:02d} {MES_CURTO[lang][d.month - 1]}"


def parceiro(lang, caminho, data1=None, data2=None):
    """Deeplink de afiliado. data1/data2 são o SubID do painel: aparecem no relatório de comissões.
    No site, o assets/site.js preenche data1 (onde foi o clique) e data2 (qual página) na hora do clique."""
    url = f"{PARCEIRO[lang]}{caminho}?a_aid={AFILIADO}"
    if data1:
        url += f"&data1={data1}"
    if data2:
        url += f"&data2={data2}"
    return url


def caminho_go(pk, lang, ev):
    """Gateway de saída: /go/<parceiro>/<idioma>/<evento>/ (trocar o link do parceiro não mexe nas páginas)."""
    return f"go/{pk}/{lang}/{ev['slug']}/"


def destino_parceiro(pk, lang, ev):
    """URL de afiliado do parceiro para o evento, ou None se o parceiro não vende esse evento."""
    if pk == "se365":
        return parceiro(lang, f"/event/{ev['id']}")
    return (ev.get("links") or {}).get(pk) or None


def opcoes_compra(lang, ev):
    return [(pk, p, destino_parceiro(pk, lang, ev)) for pk, p in C.parceiros_ativos("evento") if destino_parceiro(pk, lang, ev)]


def pagina_go(pk, lang, ev, destino):
    """Redireciona ao parceiro repassando o SubID (?d1=&d2=). Sem JavaScript, o meta refresh resolve."""
    sub = "data" if pk == "se365" else ""
    return f"""<!DOCTYPE html>
<html lang="{HREFLANG[lang]}"><head><meta charset="UTF-8"><meta name="robots" content="noindex, nofollow">
<meta name="referrer" content="no-referrer-when-downgrade">
<title>{e(L(ev['titulo'], lang))} · {e(C.PARCEIROS[pk]['nome'])} | MyTickets Tours</title>
<meta http-equiv="refresh" content="1;url={e(destino)}">
<script>(function(){{var q=new URLSearchParams(location.search),u={json.dumps(destino)},s={json.dumps(sub)};
if(s){{["d1","d2"].forEach(function(k,i){{var v=q.get(k);if(v)u+=(u.indexOf("?")<0?"?":"&")+s+(i+1)+"="+encodeURIComponent(v.slice(0,100))}})}}location.replace(u)}})();</script>
</head><body style="font-family:system-ui,sans-serif;padding:24px"><p><a href="{e(destino)}" rel="sponsored nofollow">{e(C.PARCEIROS[pk]['nome'])} →</a></p></body></html>
"""


def caminho_ir(ev, lang="en"):
    return f"ir/{lang}/{ev['id']}/"


def link_ingresso(pagina, ev):
    """Link protegido (cloaker) do botão de ingresso: /ir/<id>/ redireciona ao parceiro com o código de afiliado."""
    lang = "en" if pagina.startswith("en/") else "es" if pagina.startswith("es/") else "pt"
    return rel(pagina, caminho_go("se365", lang, ev))


def pagina_ir(ev, lang="en"):
    """Página de redirecionamento, no lugar do arquivo que o 'Affiliate link protector' do painel gera.
    Repassa o SubID (?d1=&d2=) que o site.js coloca no link; sem JavaScript, o meta refresh leva ao parceiro."""
    destino = parceiro(lang, f"/event/{ev['id']}")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="robots" content="noindex, nofollow">
<meta name="referrer" content="no-referrer-when-downgrade">
<title>{e(L(ev['titulo'], 'en'))} | MyTickets Tours</title>
<meta http-equiv="refresh" content="1;url={e(destino)}">
<script>(function(){{var q=new URLSearchParams(location.search),u={json.dumps(destino)};
["d1","d2"].forEach(function(k,i){{var v=q.get(k);if(v)u+="&data"+(i+1)+"="+encodeURIComponent(v.slice(0,100))}});location.replace(u)}})();</script>
</head><body style="font-family:system-ui,sans-serif;padding:24px"><p><a href="{e(destino)}" rel="sponsored nofollow">SportsEvents365 →</a></p></body></html>
"""


def botoes_pinterest(lang, pagina, imagem, descricao):
    """Botão Salvar (e Seguir, quando há perfil). Sem o script do Pinterest é um link comum; o site.js só carrega
    pinit.js depois que o visitante aceita os cookies, e só em páginas que têm estes botões."""
    q = urllib.parse.quote
    alvo = (f"https://www.pinterest.com/pin/create/button/?url={q(f'{BASE_URL}/{pagina}', safe='')}"
            f"&media={q(foto_abs(imagem), safe='')}&description={q(descricao[:500], safe='')}")
    salvar, seguir = PIN_TXT[lang]
    html = (f'<a class="btn-pin" data-pin-do="buttonPin" data-pin-custom="true" href="{e(alvo)}" target="_blank" rel="noopener">'
            f'<svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M6 3h12a1 1 0 0 1 1 1v17l-7-4-7 4V4a1 1 0 0 1 1-1z"/></svg>{e(salvar)}</a>')
    if PINTEREST_PERFIL:
        html += (f'<a class="btn-pin btn-pin-follow" data-pin-do="buttonFollow" href="https://www.pinterest.com/{e(PINTEREST_PERFIL)}/" '
                 f'target="_blank" rel="noopener">{e(seguir)}</a>')
    return f'<p class="pin-row">{html}</p>'


def foto(img, w=1200, pagina=""):
    """Foto do Unsplash (id photo-...) ou imagem local do portal anterior em assets/img."""
    if img.startswith("photo-"):
        return f"https://images.unsplash.com/{img}?w={w}&q=70&auto=format&fit=crop"
    webp = re.sub(r"\.jpe?g$", ".webp", img)  # versão WebP (bem menor) gerada ao lado do JPEG
    if webp != img and (RAIZ / "assets" / "img" / webp).exists():
        img = webp
    return rel(pagina, f"assets/img/{img}") + versao(f"assets/img/{img}")


def preload(img, w, pagina):
    """Pré-carrega a imagem de topo (normalmente o maior elemento visível, o LCP)."""
    return f'<link rel="preload" as="image" href="{foto(img, w, pagina)}" fetchpriority="high">'


def foto_abs(img):
    return foto(img, 1200) if img.startswith("photo-") else f"{BASE_URL}/assets/img/{img}"


def bg(img, w, pagina, extra=""):
    """style de fundo; os banners antigos têm o degradê à esquerda, então mostramos o lado direito."""
    pos = "background-position:right center;" if re.match(r"\d\d-", img) else ""
    return f"background-image:url('{foto(img, w, pagina)}');{pos}{extra}"


def caminho_home(lang):
    return "" if lang == "pt" else f"{lang}/"


def caminho_evento(lang, slug):
    return {"pt": f"eventos/{slug}/", "en": f"en/events/{slug}/", "es": f"es/eventos/{slug}/"}[lang]


def versao(arquivo):
    """Sufixo ?v=<hash> para o navegador baixar de novo só quando o arquivo mudar."""
    try:
        return "?v=" + hashlib.md5((RAIZ / arquivo).read_bytes()).hexdigest()[:8]
    except OSError:
        return ""


def rel(de, para):
    """Link relativo entre duas páginas (funciona no GitHub Pages e no domínio próprio)."""
    return "../" * de.count("/") + para


def mag(href, texto, cls="btn btn-signal", ext=True, seta=True):
    alvo = ' target="_blank" rel="sponsored nofollow noopener"' if ext else ""
    m = re.search(r"(?:^|/)go/([a-z0-9]+)/[a-z]{2}/[a-z0-9-]+/$", href)
    if m:
        alvo = f' target="_blank" rel="sponsored nofollow noopener" data-partner="{m.group(1)}"'
    s = ' <span class="arrow" aria-hidden="true">→</span>' if seta else ""
    return f'<a class="{cls}" data-magnetic href="{e(href)}"{alvo}><span class="mag-inner">{texto}{s}</span></a>'


def rastreio_ativo():
    return bool(GTM_ID or GA_MEASUREMENT_ID)


def ga_tag():
    """Consent Mode v2: tudo começa negado; o banner de cookies libera. Depois carrega o GTM ou o gtag."""
    base = "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
    if not rastreio_ativo():
        return base + "</script>"  # o dataLayer existe mesmo sem Analytics, para os eventos não darem erro
    base += ("gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied',wait_for_update:500});"
             "try{if(localStorage.getItem('mt_consent')==='granted')gtag('consent','update',{ad_storage:'granted',ad_user_data:'granted',ad_personalization:'granted',analytics_storage:'granted'});}catch(e){}")
    if GTM_ID:
        return base + ("(function(w,d,s,l,i){w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],"
                       "j=d.createElement(s);j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i;f.parentNode.insertBefore(j,f);"
                       f"}})(window,document,'script','dataLayer','{GTM_ID}');</script>")
    g = GA_MEASUREMENT_ID
    return base + f"gtag('js',new Date());gtag('config','{g}');</script><script async src=\"https://www.googletagmanager.com/gtag/js?id={g}\"></script>"


def banner_cookies(lang, pagina):
    if not rastreio_ativo():
        return ""
    h = HT[lang]
    return (f'<div class="cookie-bar" id="cookie-bar" role="region" aria-label="Cookies" hidden><div class="wrap">'
            f'<p>{e(h["c_text"])} <a href="{rel(pagina, PRIV[lang]["path"])}">{e(h["c_more"])}</a></p>'
            f'<div class="cookie-btns"><button class="btn btn-sm btn-ghost" type="button" data-consent="denied">{e(h["c_no"])}</button>'
            f'<button class="btn btn-sm btn-signal" type="button" data-consent="granted">{e(h["c_yes"])}</button></div></div></div>')


def ld_script(*objs):
    return "".join(f'<script type="application/ld+json">{json.dumps(o, ensure_ascii=False)}</script>' for o in objs)


def ld_breadcrumb(itens):
    """itens: [(nome, caminho relativo à raiz do site)]."""
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": f"{BASE_URL}/{p}"} for i, (n, p) in enumerate(itens)]}


def cabeca(lang, pagina, titulo, desc, alternos, extra="", imagem=None):
    alt = "\n".join(f'<link rel="alternate" hreflang="{HREFLANG[l]}" href="{BASE_URL}/{p}">' for l, p in alternos.items())
    return f"""<!DOCTYPE html>
<html lang="{HREFLANG[lang]}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{e(titulo)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{BASE_URL}/{pagina}">
{alt}
<link rel="alternate" hreflang="x-default" href="{BASE_URL}/{alternos['en']}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{BASE_URL}/{pagina}">
<meta property="og:locale" content="{HREFLANG[lang].replace('-', '_')}">
<meta property="og:site_name" content="MyTickets Tours">
<meta property="og:image" content="{e(foto_abs(imagem or OG_PADRAO))}">
<meta name="twitter:card" content="summary_large_image">
{f'<meta name="p:domain_verify" content="{e(PINTEREST_VERIFY)}">' if PINTEREST_VERIFY else ''}
{f'<meta name="google-site-verification" content="{e(GSC_VERIFICATION)}">' if GSC_VERIFICATION else ''}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Big+Shoulders+Display:wght@700;800;900&family=JetBrains+Mono:wght@500;700&family=Chakra+Petch:wght@600&family=IBM+Plex+Mono:wght@400&display=swap">
<link rel="stylesheet" href="{rel(pagina, 'assets/site.css')}{versao('assets/site.css')}">
{ga_tag()}
{extra}
</head>"""


def topo(lang, pagina, alternos):
    t = T[lang]
    home = rel(pagina, caminho_home(lang))
    ancoras = ["partidas", "explorar", "video", "alertas"]
    nav = "".join(f'<a href="{home}#{a}">{e(n)}</a>' for n, a in zip(t["nav"], ancoras))
    langs = "".join(f'<a href="{rel(pagina, alternos[l])}" hreflang="{HREFLANG[l]}" aria-current="{str(l == lang).lower()}">{l.upper()}</a>' for l in ORDEM_MENU)
    return f"""<header class="top">
  <div class="wrap">
    <a class="brand" href="{home}" aria-label="MyTickets Tours">MY<b>TICKETS</b>.TOURS</a>
    <nav class="nav" aria-label="Menu">{nav}</nav>
    <div class="top-r">
      <nav class="langs" aria-label="Idioma / Language">{langs}</nav>
      {mag(parceiro(lang, '/'), e(t['cta']), 'btn btn-signal btn-sm', seta=False)}
    </div>
  </div>
  {barra_voltar(lang, pagina)}
</header>"""


DESLIZE = {"pt": "Deslize para ver mais", "en": "Swipe to see more", "es": "Desliza para ver más"}
VOLTAR = {"pt": ("Voltar", "Página inicial"), "en": ("Back", "Home"), "es": ("Volver", "Inicio")}


def barra_voltar(lang, pagina):
    """Nas páginas internas: voltar à página anterior (ou ao início, se o visitante chegou de fora) e ir à página inicial."""
    if pagina == caminho_home(lang):
        return ""
    voltar, inicio = VOLTAR[lang]
    home = rel(pagina, caminho_home(lang))
    return (f'<nav class="backbar" aria-label="{e(voltar)} / {e(inicio)}"><div class="wrap">'
            f'<a class="back-btn" href="{home}" data-back><span aria-hidden="true">←</span> {e(voltar)}</a>'
            f'<a class="home-btn" href="{home}"><span aria-hidden="true">⌂</span> {e(inicio)}</a></div></nav>')


def alertas(lang, eventos, escolhido=None):
    t = T[lang]
    ops = "".join(f'<option value="{ev["slug"]}"{" selected" if ev["slug"] == escolhido else ""}>{e(L(ev["titulo"], lang))}</option>' for ev in eventos)
    lops = "".join(f'<option value="{l}"{" selected" if l == lang else ""}>{n}</option>' for l, n in [("en", "English"), ("es", "Español"), ("pt", "Português")])
    canais = "".join(f'<div class="channel"><div><strong>MyTickets · {n}</strong><span>{p}</span></div><span class="btn btn-sm btn-soon" aria-disabled="true">{e(t["soon"])}</span></div>'
                     for n, p in [("Português", "BR · PT · US"), ("English", "US · UK · CA · AU"), ("Español", "MX · AR · ES · CO")])
    return f"""<section class="band alerts" id="alertas" aria-labelledby="alerts-h">
  <div class="wrap alerts-grid">
    <div>
      <p class="kicker">{e(t['alerts_kicker'])}</p>
      <h2 id="alerts-h" data-scramble>{e(t['alerts_h'])}</h2>
      <p style="color:var(--mut);margin-top:14px;max-width:48ch">{e(t['alerts_sub'])}</p>
      <form class="form" id="alert-form" novalidate data-endpoint="{e(FORM_ENDPOINT)}" data-done="{e(t['f_done'])}" data-soon="{e(t['f_soon'])}" data-fail="{e(t['f_fail'])}" data-sending="{e(t['f_sending'])}" data-err="{e(t['f_err'])}">
        <input type="text" name="_honey" id="a-honey" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px">
        <div class="field"><label for="a-email">{e(t['f_email'])}</label><input id="a-email" type="email" autocomplete="email" inputmode="email" placeholder="{e(t['ph_email'])}"></div>
        <div class="row2">
          <div class="field"><label for="a-event">{e(t['f_event'])}</label><select id="a-event">{ops}</select></div>
          <div class="field"><label for="a-lang">{e(t['f_lang'])}</label><select id="a-lang">{lops}</select></div>
        </div>
        <label class="consent" for="a-consent"><input id="a-consent" type="checkbox"><span>{e(t['f_consent'])}</span></label>
        <div><button class="btn btn-signal" data-magnetic type="submit"><span class="mag-inner">{e(t['f_submit'])}</span></button></div>
        <p class="form-msg" id="form-msg" role="status" aria-live="polite"></p>
        {'<p class="disclose">' + e(t['f_privacy']) + '</p>' if FORM_ENDPOINT else ''}
      </form>
    </div>
    <div>
      <p class="kicker">{e(t['wa_kicker'])}</p>
      <h2 data-scramble>{e(t['wa_h'])}</h2>
      <p style="color:var(--mut);margin-top:14px;max-width:44ch">{e(t['wa_sub'])}</p>
      <div class="channels">{canais}</div>
    </div>
  </div>
</section>"""


# Link de indicação de subafiliados (painel de afiliado → Advanced tools → Signup Subaffiliates).
SUBAFILIADO = f"https://aff.sportsevents365.com/affiliates/signup.php?a_aid={AFILIADO}"
SUB_TXT = {"pt": ("Tem um site ou canal de viagem? Seja afiliado da SportsEvents365", "link de indicação"),
           "en": ("Run a travel site or channel? Become a SportsEvents365 affiliate", "referral link"),
           "es": ("¿Tienes una web o canal de viajes? Hazte afiliado de SportsEvents365", "enlace de referido")}


def rodape(lang, pagina, alternos):
    t = T[lang]
    langs = "".join(f'<a href="{rel(pagina, alternos[l])}" hreflang="{HREFLANG[l]}">{n}</a>' for l, n in [("en", "ENGLISH"), ("es", "ESPAÑOL"), ("pt", "PORTUGUÊS")])
    return f"""<footer class="foot">
  <div class="wrap">
    <a class="brand" href="{rel(pagina, caminho_home(lang))}">MY<b>TICKETS</b>.TOURS</a>
    <p class="foot-disc">{e(C.LEGAL[lang]['foot'].format(parceiros=C.nomes_parceiros()))}</p>
    <div class="foot-links">{langs}<a href="{rel(pagina, C.DIVULGACAO[lang]['path'])}">{e(C.LEGAL[lang]['pagina_link'])}</a><a href="{rel(pagina, C.COMO_FUNCIONA[lang]['path'])}">{e(C.ROT[lang]['como_h'].upper())}</a><a href="{rel(pagina, C.GUIA[lang]['path'])}">{e(C.ROT[lang]['guia_h'].upper())}</a><a href="{rel(pagina, PRIV[lang]['path'])}">{PRIV[lang]['link']}</a><a href="{e(parceiro(lang, '/'))}" target="_blank" rel="sponsored nofollow noopener">SPORTSEVENTS365</a></div>
    <p class="foot-aff"><a href="{SUBAFILIADO}" target="_blank" rel="sponsored nofollow noopener">{e(SUB_TXT[lang][0])}</a> <span>({e(SUB_TXT[lang][1])})</span></p>
    <p>{e(RESPONSAVEL)} · {CONTATO_EMAIL}</p>
    <p>© {dt.date.today().year} MyTickets Tours</p>
  </div>
</footer>
<div class="cur off" id="cur-blob" aria-hidden="true"><em>{'VER' if lang != 'en' else 'VIEW'}</em></div>
<div class="cur off" id="cur-dot" aria-hidden="true"></div>
{banner_cookies(lang, pagina)}
<script src="{rel(pagina, 'assets/site.js')}{versao('assets/site.js')}" defer></script>
</body>
</html>
"""


def cartao(lang, pagina, ev):
    t = T[lang]
    return f"""<a class="card" href="{rel(pagina, caminho_evento(lang, ev['slug']))}">
  <div class="card-img photo" style="{bg(ev['img'], 800, pagina)}"><span class="card-date">{e(data_curta(ev['data'], lang))} {ev['data'][:4]}</span></div>
  <div class="card-body"><h3>{e(L(ev['titulo'], lang))}</h3><p>{e(ev['local'])} · {e(L(ev['cidade'], lang))}</p></div>
</a>"""


def home(lang, eventos, noticias, hubs):
    t = T[lang]
    pagina = caminho_home(lang)
    alternos = {l: caminho_home(l) for l in IDIOMAS}
    solar_css = (RAIZ / "assets" / "solar-banner.css").read_text(encoding="utf-8")
    org = {"@context": "https://schema.org", "@type": "Organization", "@id": f"{BASE_URL}/#org", "name": "MyTickets Tours",
           "url": f"{BASE_URL}/", "email": CONTATO_EMAIL}
    if PINTEREST_PERFIL:
        org["sameAs"] = [f"https://www.pinterest.com/{PINTEREST_PERFIL}/"]
    site = {"@context": "https://schema.org", "@type": "WebSite", "@id": f"{BASE_URL}/#site", "name": "MyTickets Tours",
            "url": f"{BASE_URL}/{pagina}", "inLanguage": HREFLANG[lang], "publisher": {"@id": f"{BASE_URL}/#org"}}
    h = cabeca(lang, pagina, t["brand_title"], t["home_desc"], alternos, preload(FOTO_TOPO, 1800, pagina) + f"<style>\n{solar_css}</style>" + ld_script(org, site))
    clas = eventos[0]
    passes = [("GRU → BCN", eventos[0], 0.9, -6, "left:0;top:2%"), ("MEX → JFK", next(x for x in eventos if x["tipo"] == "nba"), 1.4, 5, "left:44%;top:40%"),
              ("EZE → MEL", next(x for x in eventos if x["tipo"] == "tennis"), 0.6, 3, "left:4%;top:60%"), ("LIS → MAD", eventos[-1], 1.1, -3, "left:50%;top:-4%")]
    passes_html = "".join(
        f'<a class="pass" data-i="{i+1}" data-depth="{d}" data-rot="{r}" style="{pos}" href="{rel(pagina, caminho_evento(lang, ev["slug"]))}" tabindex="-1">'
        f'<span class="pass-top"><span>{rota[:3]}</span><span>{t["gate"]} {7 + i * 3}</span></span>'
        f'<span class="pass-body"><span class="pass-route">{rota}</span><span class="pass-venue">{e(ev["local"])} · {e(L(ev["cidade"], lang))}</span></span>'
        f'<span class="pass-stub"><span>{e(data_curta(ev["data"], lang))}</span><span class="bars"></span></span></a>'
        for i, (rota, ev, d, r, pos) in enumerate(passes))
    linhas = "".join(
        f'<div class="b-row" role="listitem">'
        f'<span class="flapline" data-flap="{e(data_curta(ev["data"], lang))}" data-w="6" aria-label="{e(data_longa(ev["data"], lang))}">{e(data_curta(ev["data"], lang))}</span>'
        f'<a class="flapline b-event" href="{rel(pagina, caminho_evento(lang, ev["slug"]))}" data-flap="{e(L(ev["painel"], lang))}" data-w="22" aria-label="{e(L(ev["titulo"], lang))}">{e(L(ev["painel"], lang))}</a>'
        f'<span class="flapline b-city" data-flap="{e(L(ev["cidade"], lang).upper())}" data-w="10">{e(L(ev["cidade"], lang).upper())}</span>'
        f'<a class="flapline b-status blink" href="{e(link_ingresso(pagina, ev))}" data-partner="se365" target="_blank" rel="sponsored nofollow noopener" data-magnetic data-flap="{t["go"]}" data-w="8" aria-label="{e(t["go"])}: {e(L(ev["titulo"], lang))}">{t["go"]}</a>'
        f'</div>' for ev in eventos)
    atributos = ["", "", ' class="b-city"', ' style="justify-self:end"']
    head_row = "".join(f"<span{a}>{c}</span>" for a, c in zip(atributos, t["cols"]))
    cards = "".join(cartao(lang, pagina, ev) for ev in eventos[:3])
    def tile(n, cod, img):
        g = hubs.get(("esporte", TIPO_DO_CODIGO.get(cod)))
        if g:  # guia próprio: mostra os jogos do site antes de mandar ao parceiro
            alvo = f'href="{rel(pagina, caminho_hub(lang, g))}"'
        else:
            alvo = f'href="{e(parceiro(lang, dock_esporte(cod)))}" target="_blank" rel="sponsored nofollow noopener"'
        return f'<a class="ptile" {alvo}><span class="photo" style="{bg(img, 600, pagina)}"></span><span>{e(L(n, lang))}</span></a>'
    tiles = "".join(tile(n, cod, img) for n, cod, img in ESPORTES)
    def chips(itens, base):
        return "".join(f'<a class="chip" href="{e(parceiro(lang, base + s))}" target="_blank" rel="sponsored nofollow noopener">{e(L(n, lang))}</a>' for n, s in itens)
    lista_hubs = sorted(hubs.values(), key=lambda g: (["esporte", "competicao", "cidade"].index(g["tipo"]), -len(g["eventos"])))
    guias = ""
    if lista_hubs:
        links_guias = "".join(f'<a class="chip chip-own" href="{rel(pagina, caminho_hub(lang, g))}">{e(titulo_hub(lang, g))}</a>' for g in lista_hubs)
        guias = f'<div class="chips-group"><h3>{e(HT[lang]["guides"])}</h3><div class="chips">{links_guias}</div></div>'
    passos = "".join(f'<li class="step{" on" if i == 0 else ""}"><span class="step-n">{i + 1}</span><div><h3>{e(a)}</h3><p>{e(b)}</p></div></li>' for i, (a, b) in enumerate(t["steps"]))
    def bloco_pais(p):
        itens = "".join(f'<li><a href="{e(n["u"])}" target="_blank" rel="noopener">{e(n["t"])}<small>{e(n["f"])}{" · " + t["hot"] if n.get("alta") else ""}</small></a></li>' for n in p["noticias"])
        return f'<article class="country"><h3><span class="cc">{e(p["pais"])}</span> {e(p["nome"][lang])}</h3><ul>{itens}</ul></article>'
    noticias_html = ""
    if noticias:
        blocos = "".join(bloco_pais(p) for p in noticias)
        noticias_html = f"""<section class="band" id="noticias" aria-labelledby="news-h" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head"><div><p class="kicker">{e(t['news_kicker'])}</p><h2 id="news-h" data-scramble>{e(t['news_h'])}</h2></div><p>{e(t['news_sub'])}</p></div>
    <div class="countries" id="news" data-src="{rel(pagina, 'dados.json')}" data-lang="{lang}" data-hot="{e(t['hot'])}">{blocos}</div>
  </div>
</section>"""
    corpo = f"""
<body data-gate="{t['gate']}" data-admit="{t['admit']}" data-ticket="FC BARCELONA X REAL MADRID" data-venue="CAMP NOU · BARCELONA">
{topo(lang, pagina, alternos)}
<main id="inicio">
<section class="hero" data-parallax aria-labelledby="hero-h">
  <div class="layer l-photo photo" data-depth="0.12" style="{bg(FOTO_TOPO, 1800, pagina)}"></div>
  <div class="layer l-shade"></div>
  <div class="layer l-glow" data-depth="0.15"></div>
  <div class="layer l-grid" data-depth="0.3" aria-hidden="true"><svg viewBox="0 0 1200 700" preserveAspectRatio="none"><g stroke="rgba(160,190,230,.18)" stroke-width="1" fill="none"><path d="M600 330 L-200 700 M600 330 L100 700 M600 330 L400 700 M600 330 L800 700 M600 330 L1100 700 M600 330 L1400 700"/><path d="M0 420 H1200 M0 480 H1200 M0 560 H1200 M0 660 H1200"/></g></svg></div>
  <div class="layer l-bowl" data-depth="0.5" aria-hidden="true"><svg viewBox="0 0 1200 700" preserveAspectRatio="xMidYMid slice"><g fill="none" stroke="rgba(255,196,0,.22)" stroke-width="1.5"><ellipse cx="900" cy="330" rx="420" ry="120"/><ellipse cx="900" cy="330" rx="330" ry="88"/><ellipse cx="900" cy="330" rx="240" ry="58" stroke="rgba(255,196,0,.35)"/></g><g stroke="rgba(238,242,246,.35)" stroke-width="3"><path d="M520 330 V170 M1280 330 V170 M640 300 V150 M1160 300 V150"/></g></svg></div>
  <div class="wrap">
    <div class="hero-copy on-night">
      <p class="kicker">{e(t['hero_kicker'])}</p>
      <h1 id="hero-h"><span class="sr">{e(t['hero_h1'])}</span>
        <span class="flapline" data-flap="{t['hero_l1']}" data-w="13" aria-hidden="true">{t['hero_l1']}</span>
        <span class="flapline" data-flap="{t['hero_l2']}" data-w="13" aria-hidden="true">{t['hero_l2']}</span></h1>
      <p class="hero-sub">{e(t['hero_sub'])}</p>
      <div class="hero-ctas">
        {mag(parceiro(lang, '/'), e(t['cta']))}
        {mag('#alertas', e(t['hero_cta2']), 'btn btn-ghost', ext=False, seta=False)}
      </div>
      <p class="hero-note">{e(t['hero_note'].format(parceiros=C.nomes_parceiros()))} {e(C.LEGAL[lang]['face'].split('.')[0])}.</p>
    </div>
    <div class="passes" aria-hidden="true">{passes_html}</div>
  </div>
</section>

<section class="band" id="partidas" aria-labelledby="board-h">
  <div class="wrap">
    <div class="sec-head"><div><p class="kicker">{e(t['board_kicker'])}</p><h2 id="board-h" data-scramble>{e(t['board_h'])}</h2></div><p>{e(t['board_sub'])}</p></div>
    <div class="board">
      <div class="board-scroll"><div class="board-grid" id="board" role="list">
        <div class="b-row b-head" aria-hidden="true">{head_row}</div>
        {linhas}
      </div></div>
      <div class="board-foot"><span>{e(t['board_foot'])}</span><span>{e(t['local_time'])} <span class="clock" id="clock">--:--</span></span></div>
    </div>
  </div>
</section>

<section class="band" id="destaques" aria-labelledby="feat-h" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head"><div><p class="kicker">{e(t['feat_kicker'])}</p><h2 id="feat-h" data-scramble>{e(t['feat_h'])}</h2></div><p>{e(t['feat_sub'])}</p></div>
    <p class="swipe-hint">{e(DESLIZE[lang])}</p>
    <div class="cards cards-swipe">{cards}</div>
  </div>
</section>

<section class="band" id="explorar" aria-labelledby="exp-h" style="padding-top:0">
  <div class="wrap explore">
    <div class="sec-head" style="margin:0"><div><p class="kicker">{e(t['exp_kicker'])}</p><h2 id="exp-h" data-scramble>{e(t['exp_h'])}</h2></div><p>{e(t['exp_sub'])}</p></div>
    <div class="tiles-photo">{tiles}</div>
    {guias}
    <div class="chips-group"><h3>{e(t['g_comp'])}</h3><div class="chips">{chips(COMPETICOES, '/dock/competition/')}</div></div>
    <div class="chips-group"><h3>{e(t['g_teams'])}</h3><div class="chips">{chips(TIMES, '/dock/team/')}</div></div>
    <div class="chips-group"><h3>{e(t['g_cities'])}</h3><div class="chips">{chips(CIDADES, '/dock/cities/')}</div></div>
    <div class="chips-group"><h3>{e(t['g_music'])}</h3><div class="chips">{chips(ARTISTAS, '/dock/music/')}</div></div>
  </div>
</section>

<!-- ============ BANNER 3D (sistema solar esportivo, original do portal) ============ -->
<section id="banner3d" aria-label="Banner: sistema solar em 3D com bolas de esportes no lugar dos planetas">
  <canvas id="cena3d"></canvas>
  <div id="rotulos3d"></div>
  <div class="solar-card">
    <div class="solar-box">
      <p>{e(t['solar_k'])}</p>
      <h2>{t['solar_h']}</h2>
      <a href="{e(parceiro(lang, '/'))}" target="_blank" rel="sponsored nofollow noopener" data-magnetic><span class="mag-inner">{e(t['cta'])} →</span></a>
    </div>
  </div>
</section>
<!-- O three.js (~600 KB) só baixa quando o banner 3D chega perto da tela: o celular abre a página sem esperar por ele. -->
<script>(function(){{var b=document.getElementById("banner3d"),s=["https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js","https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js","{rel(pagina, 'assets/solar.js')}{versao('assets/solar.js')}"];
function go(i){{if(i>=s.length)return;var x=document.createElement("script");x.src=s[i];x.onload=function(){{go(i+1)}};document.body.appendChild(x)}}
if(!b||!("IntersectionObserver" in window)){{go(0);return}}var io=new IntersectionObserver(function(es){{for(var k=0;k<es.length;k++)if(es[k].isIntersecting){{io.disconnect();go(0);return}}}},{{rootMargin:"1500px 0px"}});io.observe(b)}})();</script>

<section class="sv" id="video" aria-labelledby="sv-h">
  <div class="sv-stick">
    <div class="wrap">
      <div class="sv-copy on-night">
        <p class="kicker">{e(t['how_kicker'])}</p>
        <h2 id="sv-h" data-scramble>{e(t['how_h'])}</h2>
        <ol class="steps">{passos}</ol>
      </div>
      <div class="phone" role="img" aria-label="{e(t['reel_cap'])}">
        <div class="screen" id="screen">
          <canvas id="sv-canvas"></canvas>
          <div class="reel-bar"><i id="reel-prog"></i></div>
          <div class="reel-ui"><span class="reel-handle">@mytickets.tours</span><span class="reel-cap">{e(t['reel_cap'])}</span><a class="reel-link" href="{rel(pagina, caminho_evento(lang, clas['slug']))}">{e(t['reel_link'])}</a></div>
        </div>
      </div>
    </div>
  </div>
</section>
{noticias_html}
{alertas(lang, eventos)}
</main>
"""
    return h + corpo + rodape(lang, pagina, alternos)


def ld_evento(lang, ev, pagina):
    """JSON-LD de Event no formato que o Google Eventos lê: local com endereço e geo, país ISO,
    participantes, organizador e oferta apontando para o checkout do parceiro (sem preço inventado)."""
    titulo, cidade = L(ev["titulo"], lang), L(ev["cidade"], lang)
    loc = LOCAIS.get(ev["local"], {})
    endereco = {"@type": "PostalAddress", "addressLocality": loc.get("cidade", cidade),
                "addressCountry": PAIS_ISO.get(L(ev["pais"], "en"), L(ev["pais"], lang))}
    if loc.get("rua"):
        endereco["streetAddress"] = loc["rua"]
    if loc.get("cep"):
        endereco["postalCode"] = loc["cep"]
    if loc.get("regiao"):
        endereco["addressRegion"] = loc["regiao"]
    lugar = {"@type": "Place", "name": ev["local"], "address": endereco}
    if loc.get("geo"):
        lugar["geo"] = {"@type": "GeoCoordinates", "latitude": loc["geo"][0], "longitude": loc["geo"][1]}
    ld = {"@context": "https://schema.org", "@type": "MusicEvent" if ev["tipo"] == "concert" else "SportsEvent",
          "name": titulo, "url": f"{BASE_URL}/{pagina}", "startDate": ev.get("inicio", ev["data"]), "inLanguage": HREFLANG[lang],
          "eventStatus": "https://schema.org/" + ev.get("status", "EventScheduled"),
          "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
          "location": lugar, "image": [foto_abs(ev.get("banner", ev["img"]))], "description": L(ev["intro"], lang),
          "offers": {"@type": "Offer", "url": parceiro(lang, f"/event/{ev['id']}"), "availability": "https://schema.org/InStock",
                     "seller": {"@type": "Organization", "name": "SportsEvents365", "url": "https://sportsevents365.com/"}}}
    if ev.get("artista"):
        ld["performer"] = {"@type": "MusicGroup", "name": ev["artista"]["nome"]}
    elif ev.get("times"):
        times = [{"@type": "SportsTeam", "name": L(tm["nome"], lang)} for tm in ev["times"]]
        ld["performer"] = times
        ld["competitor"] = times
        if len(times) == 2:
            ld["homeTeam"], ld["awayTeam"] = times
    if ev["tipo"] != "concert":
        ld["organizer"] = {"@type": "SportsOrganization", "name": L(ev["competicao"]["nome"], lang)}
    return ld


def data_num(iso, lang):
    d = dt.date.fromisoformat(iso)
    return f"{MESES['en'][d.month - 1]} {d.day}, {d.year}" if lang == "en" else f"{d.day:02d}/{d.month:02d}/{d.year}"


def relacionados(ev, eventos, n=3):
    """Silo interno: primeiro jogos da mesma cidade e competição, depois do mesmo esporte, depois por data.
    Assim a autoridade que chega a um clássico escorre para os jogos menores do mesmo tema."""
    def nota(x):
        return ((L(x["cidade"], "en") == L(ev["cidade"], "en")) * 2 + (L(x["competicao"]["nome"], "en") == L(ev["competicao"]["nome"], "en")) * 2
                + (x["tipo"] == ev["tipo"]) * 1)
    outros = [x for x in eventos if x["slug"] != ev["slug"]]
    return sorted(outros, key=lambda x: (-nota(x), x["data"]))[:n]


def faq_link(lang, ev, pagina, chave):
    """Link que acompanha cada resposta do FAQ (C.FAQ_LINK): canal oficial, mapa, guia, parceiro ou garantias."""
    rot = C.FAQ_LINK[lang]
    of = C.OFICIAL.get(C.chave_evento(ev["slug"]))
    if chave == "oficial":
        return f'<a href="{e(of[1])}" target="_blank" rel="noopener">{e(rot["oficial"].format(of=of[0]))}</a>' if of else ""
    if chave == "mapa":
        geo = LOCAIS.get(ev["local"], {}).get("geo")
        dest = f"{geo[0]},{geo[1]}" if geo else ev["local"].replace(" ", "+")
        return f'<a href="https://www.google.com/maps/dir/?api=1&amp;destination={e(dest)}" target="_blank" rel="noopener">{e(rot["mapa"])}</a>'
    if chave in C.FAQ_GUIA_SECAO:
        return f'<a href="{rel(pagina, C.GUIA[lang]["path"])}#s{C.FAQ_GUIA_SECAO[chave]}">{e(rot[chave])}</a>'
    if chave == "como":
        return f'<a href="{rel(pagina, C.COMO_FUNCIONA[lang]["path"])}">{e(rot["como"])}</a>'
    if chave in ("parceiro_faq", "termos"):
        url = C.PARCEIRO["faq" if chave == "parceiro_faq" else "termos"]
        return f'<a href="{e(url)}" target="_blank" rel="nofollow noopener">{e(rot[chave])}</a>'
    if chave == "comprar":
        return f'<a href="{link_ingresso(pagina, ev)}" target="_blank" rel="sponsored nofollow noopener">{e(rot["comprar"])}</a>'
    return ""


def faq_evento(lang, ev, pagina=None):
    """Perguntas do evento: lista de (pergunta, resposta, html do link)."""
    pagina = pagina or caminho_evento(lang, ev["slug"])
    titulo, cidade = L(ev["titulo"], lang), L(ev["cidade"], lang)
    of = C.OFICIAL.get(C.chave_evento(ev["slug"]))
    v = {"t": titulo, "d": data_longa(ev["data"], lang), "h": ev.get("hora", ""), "c": cidade, "empresa": C.PARCEIRO["empresa"],
         "of": of[0] if of else "", "conf": data_num(ev.get("conferido", C.PARCEIRO["conferido"]), lang), "tel": C.PARCEIRO["emergencia"]}
    itens = [(q.format(**v), a.format(**v), faq_link(lang, ev, pagina, k)) for q, a, k in C.FAQ[lang]
             if not ("{of}" in a and not of)]
    if not ev.get("hora"):
        itens = itens[1:]
    chegar = " ".join(ev["chegar"][lang])
    perg = {"pt": f"Como chegar {C.artigo(ev['local'], 'pt').replace('do', 'ao').replace('da', 'à')} {C.local_curto(ev['local'])}?",
            "en": f"How do I get to {C.local_curto(ev['local'])}?", "es": f"¿Cómo llegar {'al' if C.artigo(ev['local'], 'es') == 'del' else 'a la'} {C.local_curto(ev['local'])}?"}[lang]
    itens.insert(1, (perg, chegar, faq_link(lang, ev, pagina, "mapa")))
    return itens


def aviso_evento(lang, ev, pagina):
    """Caixa 'Antes de comprar' com o fato (e a fonte) que muda a decisão de compra deste evento."""
    av = C.AVISO.get(C.chave_evento(ev["slug"]))
    if not av:
        return ""
    fonte = f'{e(C.AVISO_FONTE[lang])}: <a href="{e(av["fonte"][1])}" target="_blank" rel="noopener">{e(av["fonte"][0])}</a>'
    barca = (f' · <a href="{rel(pagina, C.GUIA_BARCA[lang]["path"])}">{e(C.GUIA_BARCA[lang]["h1"])}</a>' if av.get("barca") else "")
    return (f'<aside class="notice" aria-labelledby="notice-h"><h2 id="notice-h">{e(C.AVISO_H[lang])}</h2>'
            f'<p>{e(av[lang])}</p><p class="disclose">{fonte}{barca}</p></aside>')


def evento(lang, ev, eventos, hubs):
    t = T[lang]
    pagina = caminho_evento(lang, ev["slug"])
    alternos = {l: caminho_evento(l, ev["slug"]) for l in IDIOMAS}
    titulo = L(ev["titulo"], lang)
    cidade = L(ev["cidade"], lang)
    dlonga = data_longa(ev["data"], lang)
    hub_esp = hub_de(hubs, "esporte", ev["tipo"])
    hub_cid = hub_de(hubs, "cidade", L(ev["cidade"], "en"))
    hub_comp = hub_de(hubs, "competicao", L(ev["competicao"]["nome"], "en")) if ev["tipo"] != "concert" else None
    trilha = [(t["home"], caminho_home(lang))]
    if hub_esp:
        trilha.append((titulo_hub(lang, hub_esp), caminho_hub(lang, hub_esp)))
    if hub_comp:
        trilha.append((titulo_hub(lang, hub_comp), caminho_hub(lang, hub_comp)))
    trilha.append((titulo, pagina))
    faq = faq_evento(lang, ev, pagina)
    ld_faq = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a, _l in faq]}
    # Funil de e-commerce do GA4: a página do evento é o "produto"; o clique no parceiro vira begin_checkout (assets/site.js).
    item = {"item_id": str(ev["id"]), "item_name": L(ev["titulo"], "en"), "item_brand": "SportsEvents365",
            "item_category": ev["tipo"], "item_category2": L(ev["competicao"]["nome"], "en"), "item_variant": L(ev["cidade"], "en"),
            "location_id": ev["local"]}
    view = ("<script>window.MT_ITEM=" + json.dumps(item, ensure_ascii=False) + ";dataLayer.push({ecommerce:null});dataLayer.push(" +
            json.dumps({"event": "view_item", "page_type": "event", "ecommerce": {"items": [item]}}, ensure_ascii=False) + ");</script>")
    extra = ld_script(ld_evento(lang, ev, pagina), ld_breadcrumb(trilha), ld_faq) + view
    rt = C.ROT[lang]
    hora_txt = ev.get("hora") or "--:--"
    titulo_pg = C.titulo_evento(lang, titulo, ev["data"][:4], ev["local"])
    desc_pg = rt["desc"].format(t=titulo, d=dlonga, h=hora_txt, loc=f'{C.local_curto(ev["local"])}, {cidade}')
    h = cabeca(lang, pagina, titulo_pg, desc_pg, alternos, preload(ev.get("banner", ev["img"]), 1800, pagina) + extra, imagem=ev.get("banner", ev["img"]))

    def link_parceiro(nome, dock):
        return f'<a href="{e(parceiro(lang, dock))}" target="_blank" rel="sponsored nofollow noopener">{e(nome)}</a>' if dock else e(nome)

    def link_hub(nome, hub, dock):
        """Prefere o guia no próprio site (link interno conta para o SEO); sem hub, vai ao parceiro."""
        return f'<a href="{rel(pagina, caminho_hub(lang, hub))}">{e(nome)}</a>' if hub else link_parceiro(nome, dock)
    comp = ev["competicao"]
    comp_nome = L(comp["nome"], lang)
    cidade_html = link_hub(cidade, hub_cid, ev["cidade"].get("dock"))
    if ev.get("artista"):
        quarto = (t["f_artist"], link_parceiro(ev["artista"]["nome"], ev["artista"]["dock"]))
    else:
        quarto = (t["f_comp"], link_hub(comp_nome, hub_comp, comp.get("dock")))
    tipo_nome = TIPO_NOME[ev["tipo"]][lang]
    kicker_tipo = link_hub(tipo_nome, hub_esp, dock_esporte(ev["esporte_tipo"]))
    tambem = []
    for tm in ev.get("times", []):
        if tm.get("dock"):
            tambem.append(link_parceiro(L(tm["nome"], lang), tm["dock"]))
    if ev.get("artista"):
        tambem.append(link_parceiro(ev["artista"]["nome"], ev["artista"]["dock"]))
    if comp.get("dock"):
        tambem.append(link_parceiro(comp_nome, comp["dock"]))
    if ev["cidade"].get("dock"):
        tambem.append(link_parceiro(cidade, ev["cidade"]["dock"]))
    tambem.append(link_parceiro(tipo_nome, dock_esporte(ev["esporte_tipo"])))
    chegar = "".join(f"<li>{e(x)}</li>" for x in ev["chegar"][lang])
    dicas = "".join(f"<li>{e(x)}</li>" for x in DICAS[ev["tipo"]][lang])
    tambem_html = "".join(f"<li>{x}</li>" for x in tambem)
    mais = "".join(cartao(lang, pagina, x) for x in relacionados(ev, eventos))
    lg = C.LEGAL[lang]
    cards_compra = "".join(
        f'<article class="buy-opt"><div class="buy-head"><span class="buy-seller">{e(lg["vendedor"])}</span><h3>{e(pp["nome"])}</h3>'
        f'<p class="buy-badge">{e(pp["selo"][lang])}</p></div>'
        + (f'<ul>' + "".join(f"<li>{e(x)}</li>" for x in pp["fatos"].get(lang, [])) + '</ul>' if pp["fatos"].get(lang) else "")
        + f'<div class="buy-actions">{mag(rel(pagina, caminho_go(pk, lang, ev)), e(lg["cta"].format(nome=pp["nome"])), "btn btn-signal")}'
        + (f'<a class="buy-terms" href="{e(pp["termos"])}" target="_blank" rel="nofollow noopener">{e(lg["ver_termos"])}</a>' if pp.get("termos") else "")
        + '</div></article>' for pk, pp, _d in opcoes_compra(lang, ev))
    onde_comprar = (f'<section class="buy" aria-labelledby="buy-h"><h2 id="buy-h">{e(lg["onde_h"])}</h2><p class="buy-sub">{e(lg["onde_sub"])}</p>'
                    f'<div class="buy-list">{cards_compra}</div><p class="disclose buy-face">{e(lg["face"])}</p></section>') if cards_compra else ""
    entrada = "".join(f"<li>{e(x)}</li>" for x in C.ENTRADA[ev["tipo"]][lang])
    perfis = list(C.PUBLICO[ev["tipo"]][lang]) + ([C.LOCAL_PUBLICO[ev["local"]][lang]] if ev["local"] in C.LOCAL_PUBLICO else [])
    publico = "".join(f"<li><strong>{e(a)}.</strong> {e(b)}</li>" for a, b in perfis)
    cp = C.COMPRAR[lang]
    passos = "".join(f"<li>{e(x.format(d=dlonga, h=hora_txt, tel=C.PARCEIRO['emergencia']))}</li>" for x in cp["passos"])
    faq_html = "".join(f'<details class="faq-item"><summary>{e(q)}</summary><p>{e(a)}</p>'
                       + (f'<p class="faq-link">{lk} <span aria-hidden="true">→</span></p>' if lk else "") + '</details>' for q, a, lk in faq)
    conferido = rt["conferido"].format(conf=data_num(ev["conferido"], lang)) if ev.get("conferido") else t["date_note"]
    crumbs_mid = "".join(f'<a href="{rel(pagina, cam)}">{e(nome)}</a><span aria-hidden="true">›</span>' for nome, cam in trilha[1:-1]) \
        or f'<a href="{rel(pagina, caminho_home(lang))}#partidas">{e(t["events"])}</a><span aria-hidden="true">›</span>'
    ingresso = link_ingresso(pagina, ev)
    corpo = f"""
<body>
{topo(lang, pagina, alternos)}
<main>
<section class="ev-hero" data-parallax aria-labelledby="ev-h">
  <div class="layer l-photo photo" data-depth="0.15" style="{bg(ev.get('banner', ev['img']), 1800, pagina, 'opacity:.55')}"></div>
  <div class="layer l-shade"></div>
  <div class="wrap on-night">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{rel(pagina, caminho_home(lang))}">{e(t['home'])}</a><span aria-hidden="true">›</span>{crumbs_mid}<span>{e(titulo)}</span></nav>
    <p class="kicker">{kicker_tipo} · {link_hub(comp_nome, hub_comp, comp.get('dock'))}</p>
    <h1 id="ev-h">{e(titulo)}</h1>
    <span class="flapline" data-flap="{e(L(ev['painel'], lang))}" data-w="22" aria-hidden="true">{e(L(ev['painel'], lang))}</span>
    <dl class="facts">
      <div class="fact"><dt>{e(t['f_date'])}</dt><dd>{e(dlonga)}</dd></div>
      {f'<div class="fact"><dt>{e(rt["f_time"])}</dt><dd>{e(rt["hora_local"].format(h=ev["hora"]))}</dd></div>' if ev.get("hora") else ''}
      <div class="fact"><dt>{e(t['f_venue'])}</dt><dd>{e(ev['local'])}</dd></div>
      <div class="fact"><dt>{e(t['f_city'])}</dt><dd>{cidade_html}, {e(L(ev['pais'], lang))}</dd></div>
      <div class="fact"><dt>{e(quarto[0])}</dt><dd>{quarto[1]}</dd></div>
    </dl>
    <div class="ev-cta">
      {mag(ingresso, e(t['ev_cta']))}
      {mag('#alertas', e(t['ev_alert']), 'btn btn-ghost', ext=False, seta=False)}
    </div>
    <p class="disclose">{e(C.LEGAL[lang]['face'])} {e(t['aff_note'])} {e(conferido)} <a href="{rel(pagina, C.DIVULGACAO[lang]['path'])}">{e(C.LEGAL[lang]['pagina_link'].capitalize())}</a></p>
  </div>
</section>

<section class="band" aria-label="{e(titulo)}">
  <div class="wrap event">
    <div class="short-slot">
      <span class="photo" style="{bg(ev['img'], 600, pagina)}"></span>
      <span class="short-tag">{e(t['short_tag'])}</span>
      <span class="short-title">{e(t['short_t'].format(t=titulo))}</span>
      <div class="platforms"><span>SHORTS</span><span>REELS</span><span>TIKTOK</span></div>
    </div>
    <div class="event-main">
      <p class="lead">{e(L(ev['intro'], lang))}</p>
      {botoes_pinterest(lang, pagina, ev.get("banner", ev["img"]), f"{titulo_pg}. {L(ev['intro'], lang)}")}
      <div class="tips">
        <div><h2>{e(t['get_h'])}</h2><ul>{chegar}</ul></div>
        <div><h2>{e(t['tips_h'])}</h2><ul>{dicas}</ul></div>
      </div>
      <div class="tips">
        <div><h2>{e(rt['entrada_h'])}</h2><ul>{entrada}</ul></div>
        <div><h2>{e(rt['publico_h'])}</h2><ul>{publico}</ul></div>
      </div>
      {aviso_evento(lang, ev, pagina)}
      {onde_comprar}
      <div class="howto">
        <h2>{e(cp['h'].format(t=titulo))}</h2>
        <ol>{passos}</ol>
        <p class="disclose"><a href="{rel(pagina, C.GUIA[lang]['path'])}">{e(rt['guia_h'])}</a> · <a href="{rel(pagina, C.COMO_FUNCIONA[lang]['path'])}">{e(rt['como_h'])}</a></p>
      </div>
      <div class="faq">
        <h2>{e(rt['faq_h'])}</h2>
        {faq_html}
      </div>
      <div class="tips">
        <div><h2>{e(t['also'])}</h2><ul>{tambem_html}</ul></div>
        <div class="ev-cta" style="align-self:end">{mag(ingresso, e(t['ev_cta']))}</div>
      </div>
    </div>
  </div>
</section>

<section class="band" aria-labelledby="more-h" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head"><div><p class="kicker">{e(t['more_k'])}</p><h2 id="more-h" data-scramble>{e(t['more_h'])}</h2></div></div>
    <p class="swipe-hint">{e(DESLIZE[lang])}</p>
    <div class="cards cards-swipe">{mais}</div>
  </div>
</section>
{alertas(lang, eventos, ev['slug'])}
</main>
<div class="buybar" id="buybar" aria-hidden="true"><div class="wrap">
  <div class="buybar-info"><strong>{e(titulo)}</strong><span>{e(data_curta(ev['data'], lang))}{(' · ' + e(ev['hora'])) if ev.get('hora') else ''} · {e(C.local_curto(ev['local']))}</span></div>
  {mag(ingresso, e(t['cta']), 'btn btn-signal btn-sm', seta=False)}
</div></div>
"""
    return h + corpo + rodape(lang, pagina, alternos)


def hub(lang, g, eventos, hubs):
    """Página-guia de um esporte, cidade ou competição: ranqueia termos amplos como
    "ingressos La Liga" ou "ingressos em Barcelona" e distribui links internos para os eventos."""
    t, h = T[lang], HT[lang]
    pagina = caminho_hub(lang, g)
    alternos = {l: caminho_hub(l, g) for l in IDIOMAS}
    titulo = titulo_hub(lang, g)
    evs = sorted(g["eventos"], key=lambda x: x["data"])
    nomes = [L(x["titulo"], lang) for x in evs[:3]]
    lista = ", ".join(nomes)
    desc = h["desc"].format(n=len(evs), lista=lista)
    itens = {"@context": "https://schema.org", "@type": "ItemList", "name": titulo, "numberOfItems": len(evs),
             "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{BASE_URL}/{caminho_evento(lang, x['slug'])}",
                                  "name": L(x["titulo"], lang)} for i, x in enumerate(evs)]}
    trilha = [(t["home"], caminho_home(lang)), (titulo, pagina)]
    cab = cabeca(lang, pagina, f"{titulo} | MyTickets Tours", desc, alternos,
                 ld_script(itens, ld_breadcrumb(trilha)) + '<script>dataLayer.push({page_type:"hub"});</script>')
    cards = "".join(cartao(lang, pagina, x) for x in evs)
    outros = [x for x in sorted(hubs.values(), key=lambda x: (x["tipo"], x["slug"][lang])) if x is not g]
    outros_html = ""
    if outros:
        outros_html = ('<div class="chips-group" style="margin-top:40px"><h3>' + e(h["guides"]) + '</h3><div class="chips">' +
                       "".join(f'<a class="chip chip-own" href="{rel(pagina, caminho_hub(lang, x))}">{e(titulo_hub(lang, x))}</a>' for x in outros) +
                       "</div></div>")
    cta = mag(parceiro(lang, g["dock"]), e(h["partner"])) if g["dock"] else ""
    foto_topo = evs[0].get("banner", evs[0]["img"])
    corpo = f"""
<body>
{topo(lang, pagina, alternos)}
<main>
<section class="ev-hero" data-parallax aria-labelledby="hub-h">
  <div class="layer l-photo photo" data-depth="0.15" style="{bg(foto_topo, 1800, pagina, 'opacity:.45')}"></div>
  <div class="layer l-shade"></div>
  <div class="wrap on-night">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{rel(pagina, caminho_home(lang))}">{e(t['home'])}</a><span aria-hidden="true">›</span><span>{e(titulo)}</span></nav>
    <p class="kicker">{e(h['kicker'])}</p>
    <h1 id="hub-h">{e(titulo)}</h1>
    <p class="hero-sub" style="max-width:60ch">{e(h['lead'].format(n=len(evs)))}</p>
    <div class="ev-cta">{cta}</div>
    <p class="disclose">{e(t['aff_note'])}</p>
  </div>
</section>
<section class="band" aria-labelledby="list-h">
  <div class="wrap">
    <div class="sec-head"><div><p class="kicker">{e(titulo)}</p><h2 id="list-h" data-scramble>{e(h['list_h'])}</h2></div></div>
    <div class="cards">{cards}</div>
    {outros_html}
  </div>
</section>
{alertas(lang, eventos, evs[0]['slug'])}
</main>
"""
    return cab + corpo + rodape(lang, pagina, alternos)


def pagina_texto(lang, pg, pagina, alternos, ld, extra_html="", imagem=None):
    """Página editorial simples (guia ou institucional) no estilo da política de privacidade."""
    v = {"empresa": C.PARCEIRO["empresa"], "endereco": C.PARCEIRO[{"pt": "endereco", "en": "endereco_en", "es": "endereco_es"}[lang]],
         "tel": C.PARCEIRO["emergencia"], "email": CONTATO_EMAIL}
    secoes = "".join(f'<h2 id="s{i}">{e(tit)}</h2>' + "".join(f"<p>{e(x.format(**v))}</p>" for x in pars)
                     for i, (tit, pars) in enumerate(pg["secoes"], 1))
    trilha = [(T[lang]["home"], caminho_home(lang)), (pg["h1"], pagina)]
    cab = cabeca(lang, pagina, pg["title"], pg["desc"], alternos, ld_script(ld, ld_breadcrumb(trilha)), imagem=imagem)
    pin = botoes_pinterest(lang, pagina, imagem, f"{pg['title']}. {pg['desc']}") if imagem else ""
    corpo = f"""
<body>
{topo(lang, pagina, alternos)}
<main class="band">
  <article class="wrap legal">
    <nav class="crumbs crumbs-light" aria-label="Breadcrumb"><a href="{rel(pagina, caminho_home(lang))}">{e(T[lang]['home'])}</a><span aria-hidden="true">›</span><span>{e(pg['h1'])}</span></nav>
    <p class="kicker">MyTickets Tours</p>
    <h1>{e(pg['h1'])}</h1>
    <p class="lead">{e(pg['lead'])}</p>
    {pin}
    {secoes}
    {extra_html}
  </article>
</main>
"""
    return cab + corpo + rodape(lang, pagina, alternos)


def divulgacao(lang):
    pg = dict(C.DIVULGACAO[lang])
    pg["secoes"] = [(t, [x.replace("{parceiros}", C.nomes_parceiros()) for x in pars]) for t, pars in pg["secoes"]]
    pagina = pg["path"]
    alternos = {l: C.DIVULGACAO[l]["path"] for l in IDIOMAS}
    ld = {"@context": "https://schema.org", "@type": "WebPage", "name": pg["title"], "url": f"{BASE_URL}/{pagina}", "inLanguage": HREFLANG[lang],
          "publisher": {"@id": f"{BASE_URL}/#org"}}
    return pagina_texto(lang, pg, pagina, alternos, ld)


def como_funciona(lang):
    pg = C.COMO_FUNCIONA[lang]
    pagina = pg["path"]
    alternos = {l: C.COMO_FUNCIONA[l]["path"] for l in IDIOMAS}
    ld = {"@context": "https://schema.org", "@type": "AboutPage", "name": pg["title"], "url": f"{BASE_URL}/{pagina}", "inLanguage": HREFLANG[lang],
          "about": {"@id": f"{BASE_URL}/#org"},
          "mainEntity": {"@type": "Organization", "@id": f"{BASE_URL}/#org", "name": "MyTickets Tours", "url": f"{BASE_URL}/", "email": CONTATO_EMAIL,
                         "founder": {"@type": "Person", "name": RESPONSAVEL}}}
    links = (f'<h2>{e(pg["links_h"])}</h2><p><a href="{C.PARCEIRO["termos"]}" target="_blank" rel="noopener">{e(pg["termos"])}</a><br>'
             f'<a href="{C.PARCEIRO["faq"]}" target="_blank" rel="noopener">{e(pg["faq"])}</a></p>'
             f'<p>{e(PRIV[lang]["resp"])}: {e(RESPONSAVEL)} · <a href="mailto:{CONTATO_EMAIL}">{CONTATO_EMAIL}</a></p>')
    return pagina_texto(lang, pg, pagina, alternos, ld, links)


def guia(lang, eventos, hubs):
    pg = C.GUIA[lang]
    pagina = pg["path"]
    alternos = {l: C.GUIA[l]["path"] for l in IDIOMAS}
    hoje = dt.date.today().isoformat()
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": pg["title"], "description": pg["desc"], "inLanguage": HREFLANG[lang],
          "url": f"{BASE_URL}/{pagina}", "mainEntityOfPage": f"{BASE_URL}/{pagina}", "datePublished": "2026-10-15", "dateModified": C.PARCEIRO["conferido"],
          "author": {"@type": "Organization", "@id": f"{BASE_URL}/#org", "name": "MyTickets Tours"},
          "publisher": {"@type": "Organization", "@id": f"{BASE_URL}/#org", "name": "MyTickets Tours"}}
    url = f"{BASE_URL}/{pagina}"
    snippet = f'<a href="{url}">{pg["h1"]}</a> (MyTickets Tours)'
    cards = "".join(cartao(lang, pagina, x) for x in eventos[:3])
    guias = "".join(f'<a class="chip chip-own" href="{rel(pagina, caminho_hub(lang, g))}">{e(titulo_hub(lang, g))}</a>' for g in hubs.values())
    extra = (f'<div class="cite"><h2>{e(pg["cite_h"])}</h2><p>{e(pg["cite_p"])}</p>'
             f'<pre class="cite-code" tabindex="0"><code>{e(snippet)}</code></pre></div>'
             f'<h2>{e(pg["eventos_h"])}</h2><div class="cards">{cards}</div><div class="chips" style="margin-top:16px">{guias}'
             f'<a class="chip chip-own" href="{rel(pagina, C.GUIA_BARCA[lang]["path"])}">{e(C.GUIA_BARCA[lang]["h1"])}</a></div>')
    return pagina_texto(lang, pg, pagina, alternos, ld, extra, imagem="06-champions.jpg")


def guia_barca(lang, eventos):
    pg = C.GUIA_BARCA[lang]
    pagina = pg["path"]
    alternos = {l: C.GUIA_BARCA[l]["path"] for l in IDIOMAS}
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": pg["title"], "description": pg["desc"], "inLanguage": HREFLANG[lang],
          "url": f"{BASE_URL}/{pagina}", "mainEntityOfPage": f"{BASE_URL}/{pagina}", "datePublished": "2026-10-16", "dateModified": "2026-10-16",
          "about": {"@type": "SportsTeam", "name": "FC Barcelona"},
          "author": {"@type": "Organization", "@id": f"{BASE_URL}/#org", "name": "MyTickets Tours"},
          "publisher": {"@type": "Organization", "@id": f"{BASE_URL}/#org", "name": "MyTickets Tours"}}
    jogos = [x for x in eventos if x["local"] == "Camp Nou"]
    cards = "".join(cartao(lang, pagina, x) for x in jogos)
    fontes = "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(n)}</a></li>' for n, u in C.GUIA_BARCA_FONTES)
    extra = ((f'<h2>{e(pg["eventos_h"])}</h2><div class="cards">{cards}</div>' if cards else "")
             + f'<p><a href="{rel(pagina, C.GUIA[lang]["path"])}">{e(pg["guia_geral"])} →</a></p>'
             + f'<h2>{e(pg["fontes_h"])}</h2><ul>{fontes}</ul>')
    return pagina_texto(lang, pg, pagina, alternos, ld, extra, imagem="04-la-liga.jpg")


PRIV = {
 "pt": {"path": "privacidade/", "link": "PRIVACIDADE E CONTATO", "title": "Política de privacidade | MyTickets Tours",
  "desc": "Como o MyTickets Tours trata seus dados, e como falar conosco.", "h1": "Política de privacidade",
  "updated": "Atualizada em 16 de outubro de 2026.",
  "sections": [
   ("Quem somos", ["O MyTickets Tours (mytickets.tours) é um site afiliado de ingressos para eventos esportivos e shows, mantido por Everton Bras.",
                   "Não vendemos ingressos. A compra acontece no site da SportsEvents365, que é responsável pela venda, pelo pagamento e pela entrega."]),
   ("Que dados tratamos", ["Navegação: os serviços que hospedam o site (Microsoft Azure e GitHub) registram dados técnicos, como endereço IP e tipo de navegador, para manter o site no ar e protegido.",
                           "Alertas de venda: se você pedir um alerta, guardamos seu e-mail, o evento escolhido e o idioma, com o seu consentimento. O cadastro chega à nossa caixa de e-mail pelo serviço FormSubmit.",
                           "Atendimento no WhatsApp: se você falar conosco, tratamos seu número e suas mensagens para responder, pela plataforma da Meta.",
                           "Pinterest: nas páginas de eventos e guias há um botão para salvar a página no Pinterest. O código do Pinterest só é carregado depois que você aceita os cookies; antes disso, o botão é um link comum para o site do Pinterest, e o que você salvar lá segue a política de privacidade do Pinterest.",
                           "Cookies: usamos o Google Analytics para medir visitas e cliques, e ele só grava cookies depois que você clica em Aceitar no aviso de cookies. Se recusar, nenhum cookie de estatística ou publicidade é gravado. Para mudar a escolha, apague os dados deste site no seu navegador e o aviso aparece de novo.",
                           "Links de afiliado: quando você clica num link para a SportsEvents365, o parceiro registra que você veio do MyTickets (código a_aid) para calcular nossa comissão. A partir daí vale a política de privacidade da SportsEvents365."]),
   ("Para que usamos", ["Enviar o alerta que você pediu, responder suas mensagens e manter o site funcionando e seguro. Não vendemos nem alugamos seus dados."]),
   ("Base legal", ["Consentimento para alertas, atendimento e estatísticas (LGPD, art. 7º, I; GDPR, art. 6(1)(a)). Interesse legítimo para a segurança e o funcionamento do site (LGPD, art. 7º, IX; GDPR, art. 6(1)(f))."]),
   ("Por quanto tempo", ["E-mails de alerta: até o evento acontecer ou até você pedir para sair, o que vier primeiro. Conversas do WhatsApp: até 12 meses."]),
   ("Compartilhamento e transferência internacional", ["Seus dados passam apenas pelos fornecedores citados acima (Microsoft, GitHub, FormSubmit, Meta, Google e Pinterest). Eles podem tratar os dados fora do seu país, sob as garantias contratuais de cada um."]),
   ("Seus direitos", ["Você pode pedir acesso, correção, exclusão e portabilidade dos seus dados, e retirar o consentimento a qualquer momento. Escreva para email@mytickets.tours e respondemos em até 15 dias.",
                      "Você também pode reclamar à ANPD, no Brasil, ou à autoridade de proteção de dados do seu país."]),
   ("Menores de idade", ["O site não é voltado para menores de 18 anos. Compras de ingressos devem ser feitas por adultos."]),
   ("Mudanças", ["Se esta política mudar, a data no topo da página será atualizada."]),
  ],
  "contact_h": "Contato", "resp": "Responsável"},
 "en": {"path": "en/privacy/", "link": "PRIVACY AND CONTACT", "title": "Privacy policy | MyTickets Tours",
  "desc": "How MyTickets Tours handles your data, and how to reach us.", "h1": "Privacy policy",
  "updated": "Last updated October 16, 2026.",
  "sections": [
   ("Who we are", ["MyTickets Tours (mytickets.tours) is an affiliate site for sports and concert tickets, run by Everton Bras.",
                   "We do not sell tickets. Purchases happen on the SportsEvents365 site, which is responsible for the sale, payment and delivery."]),
   ("What data we handle", ["Browsing: the services that host the site (Microsoft Azure and GitHub) log technical data, such as IP address and browser type, to keep the site running and secure.",
                            "Sale alerts: if you ask for an alert, we keep your email, the event you chose and your language, with your consent. The sign-up reaches our inbox through the FormSubmit service.",
                            "WhatsApp support: if you message us, we handle your number and messages to reply, through Meta's platform.",
                            "Pinterest: event and guide pages have a button to save the page to Pinterest. Pinterest's code only loads after you accept cookies; before that, the button is a plain link to Pinterest, and whatever you save there falls under Pinterest's privacy policy.",
                           "Cookies: we use Google Analytics to measure visits and clicks, and it only sets cookies after you click Accept in the cookie notice. If you decline, no analytics or advertising cookies are set. To change your choice, clear this site's data in your browser and the notice will show again.",
                            "Affiliate links: when you click a link to SportsEvents365, the partner records that you came from MyTickets (code a_aid) to calculate our commission. From then on, the SportsEvents365 privacy policy applies."]),
   ("Why we use it", ["To send the alert you asked for, reply to your messages and keep the site running and secure. We never sell or rent your data."]),
   ("Legal basis", ["Consent for alerts, support and analytics (GDPR Art. 6(1)(a); LGPD Art. 7, I). Legitimate interest for security and operation of the site (GDPR Art. 6(1)(f); LGPD Art. 7, IX)."]),
   ("How long we keep it", ["Alert emails: until the event takes place or until you unsubscribe, whichever comes first. WhatsApp conversations: up to 12 months."]),
   ("Sharing and international transfers", ["Your data only goes through the providers named above (Microsoft, GitHub, FormSubmit, Meta, Google and Pinterest). They may process data outside your country under their own contractual safeguards."]),
   ("Your rights", ["You can ask to access, correct, delete or port your data, and withdraw consent at any time. Write to email@mytickets.tours and we will reply within 15 days.",
                    "You can also complain to the data protection authority in your country."]),
   ("Minors", ["The site is not aimed at people under 18. Ticket purchases must be made by adults."]),
   ("Changes", ["If this policy changes, the date at the top of the page will be updated."]),
  ],
  "contact_h": "Contact", "resp": "Responsible person"},
 "es": {"path": "es/privacidad/", "link": "PRIVACIDAD Y CONTACTO", "title": "Política de privacidad | MyTickets Tours",
  "desc": "Cómo MyTickets Tours trata tus datos y cómo contactarnos.", "h1": "Política de privacidad",
  "updated": "Actualizada el 16 de octubre de 2026.",
  "sections": [
   ("Quiénes somos", ["MyTickets Tours (mytickets.tours) es un sitio afiliado de entradas para eventos deportivos y conciertos, gestionado por Everton Bras.",
                      "No vendemos entradas. La compra se hace en el sitio de SportsEvents365, responsable de la venta, el pago y la entrega."]),
   ("Qué datos tratamos", ["Navegación: los servicios que alojan el sitio (Microsoft Azure y GitHub) registran datos técnicos, como la dirección IP y el navegador, para mantener el sitio activo y seguro.",
                           "Alertas de venta: si pides una alerta, guardamos tu correo, el evento elegido y el idioma, con tu consentimiento. El registro llega a nuestro correo mediante el servicio FormSubmit.",
                           "Atención por WhatsApp: si nos escribes, tratamos tu número y tus mensajes para responderte, a través de la plataforma de Meta.",
                           "Pinterest: las páginas de eventos y guías tienen un botón para guardar la página en Pinterest. El código de Pinterest solo se carga después de que aceptes las cookies; antes, el botón es un enlace normal a Pinterest, y lo que guardes allí sigue la política de privacidad de Pinterest.",
                           "Cookies: usamos Google Analytics para medir visitas y clics, y solo guarda cookies después de que haces clic en Aceptar en el aviso de cookies. Si lo rechazas, no se guarda ninguna cookie de estadística ni de publicidad. Para cambiar tu elección, borra los datos de este sitio en tu navegador y el aviso volverá a aparecer.",
                           "Enlaces de afiliado: al hacer clic en un enlace a SportsEvents365, el socio registra que llegaste desde MyTickets (código a_aid) para calcular nuestra comisión. Desde ese momento rige la política de privacidad de SportsEvents365."]),
   ("Para qué los usamos", ["Enviar la alerta que pediste, responder tus mensajes y mantener el sitio funcionando y seguro. Nunca vendemos ni alquilamos tus datos."]),
   ("Base legal", ["Consentimiento para alertas, atención y estadísticas (RGPD, art. 6.1.a; LGPD, art. 7, I). Interés legítimo para la seguridad y el funcionamiento del sitio (RGPD, art. 6.1.f; LGPD, art. 7, IX)."]),
   ("Cuánto tiempo", ["Correos de alerta: hasta que se celebre el evento o hasta que te des de baja, lo que ocurra primero. Conversaciones de WhatsApp: hasta 12 meses."]),
   ("Cesión y transferencias internacionales", ["Tus datos solo pasan por los proveedores citados (Microsoft, GitHub, FormSubmit, Meta, Google y Pinterest). Pueden tratarlos fuera de tu país bajo sus propias garantías contractuales."]),
   ("Tus derechos", ["Puedes pedir acceso, rectificación, supresión y portabilidad de tus datos, y retirar el consentimiento en cualquier momento. Escribe a email@mytickets.tours y respondemos en un plazo de 15 días.",
                     "También puedes reclamar ante la autoridad de protección de datos de tu país."]),
   ("Menores", ["El sitio no está dirigido a menores de 18 años. Las compras de entradas deben hacerlas adultos."]),
   ("Cambios", ["Si esta política cambia, se actualizará la fecha al inicio de la página."]),
  ],
  "contact_h": "Contacto", "resp": "Responsable"},
}
CONTATO_EMAIL = "email@mytickets.tours"
RESPONSAVEL = "Everton Bras"


def privacidade(lang):
    pv = PRIV[lang]
    pagina = pv["path"]
    alternos = {l: PRIV[l]["path"] for l in IDIOMAS}
    h = cabeca(lang, pagina, pv["title"], pv["desc"], alternos)
    secoes = "".join(f"<h2>{e(tit)}</h2>" + "".join(f"<p>{e(x)}</p>" for x in pars) for tit, pars in pv["sections"])
    corpo = f"""
<body>
{topo(lang, pagina, alternos)}
<main class="band">
  <article class="wrap legal">
    <p class="kicker">MyTickets Tours</p>
    <h1>{e(pv['h1'])}</h1>
    <p class="disclose">{e(pv['updated'])}</p>
    {secoes}
    <h2 id="contato">{e(pv['contact_h'])}</h2>
    <p>{e(pv['resp'])}: {e(RESPONSAVEL)}<br>E-mail: <a href="mailto:{CONTATO_EMAIL}">{CONTATO_EMAIL}</a></p>
  </article>
</main>
"""
    return h + corpo + rodape(lang, pagina, alternos)


ROTULOS_CAT = {
 "pt": {"ev": "Eventos com página", "comp": "Ligas e campeonatos", "teams": "Times", "cities": "Cidades", "music": "Artistas", "sports": "Esportes",
        "home": "Catálogo completo do parceiro", "date": "Data", "venue": "Local", "guide": "Guia no site", "tickets": "Ingressos"},
 "en": {"ev": "Events with a page", "comp": "Leagues and competitions", "teams": "Teams", "cities": "Cities", "music": "Artists", "sports": "Sports",
        "home": "Full partner catalogue", "date": "Date", "venue": "Venue", "guide": "Guide on the site", "tickets": "Tickets"},
 "es": {"ev": "Eventos con página", "comp": "Ligas y competiciones", "teams": "Equipos", "cities": "Ciudades", "music": "Artistas", "sports": "Deportes",
        "home": "Catálogo completo del socio", "date": "Fecha", "venue": "Recinto", "guide": "Guía en el sitio", "tickets": "Entradas"},
}


def gerar_catalogo(eventos):
    """Catálogo de links de afiliado para o agente do WhatsApp (mesmos destinos do site)."""
    cat = {"atualizado": dt.date.today().isoformat(), "afiliado": AFILIADO, "idiomas": {}}
    for lang in IDIOMAS:
        c = {
            "catalogo_parceiro": parceiro(lang, "/"),
            "eventos": [{
                "nome": L(ev["titulo"], lang), "data": ev["data"], "data_texto": data_longa(ev["data"], lang),
                "local": ev["local"], "cidade": L(ev["cidade"], lang), "pais": L(ev["pais"], lang),
                "competicao": L(ev["competicao"]["nome"], lang),
                "times": [L(t["nome"], lang) for t in ev.get("times", [])] + ([ev["artista"]["nome"]] if ev.get("artista") else []),
                "ingressos": parceiro(lang, f"/event/{ev['id']}", "whatsapp", lang),
                "guia": f"{BASE_URL}/{caminho_evento(lang, ev['slug'])}",
                "como_chegar": ev["chegar"][lang], "dicas": DICAS[ev["tipo"]][lang],
            } for ev in eventos],
            "competicoes": [{"nome": L(n, lang), "link": parceiro(lang, "/dock/competition/" + s)} for n, s in COMPETICOES],
            "times": [{"nome": L(n, lang), "link": parceiro(lang, "/dock/team/" + s)} for n, s in TIMES],
            "cidades": [{"nome": L(n, lang), "link": parceiro(lang, "/dock/cities/" + s)} for n, s in CIDADES],
            "artistas": [{"nome": L(n, lang), "link": parceiro(lang, "/dock/music/" + s)} for n, s in ARTISTAS],
            "esportes": [{"nome": L(n, lang), "link": parceiro(lang, dock_esporte(cod))} for n, cod, _ in ESPORTES],
        }
        cat["idiomas"][lang] = c
        r = ROTULOS_CAT[lang]
        md = [f"# MyTickets Tours ({lang.upper()})", "", f"{r['home']}: {c['catalogo_parceiro']}", "", f"## {r['ev']}", ""]
        for x in c["eventos"]:
            md += [f"### {x['nome']}", f"- {r['date']}: {x['data_texto']}", f"- {r['venue']}: {x['local']}, {x['cidade']}, {x['pais']} ({x['competicao']})",
                   f"- {r['tickets']}: {x['ingressos']}", f"- {r['guide']}: {x['guia']}"] + [f"- {y}" for y in x["como_chegar"]] + [""]
        for k, h in [("competicoes", "comp"), ("times", "teams"), ("cidades", "cities"), ("artistas", "music"), ("esportes", "sports")]:
            md += [f"## {r[h]}", ""] + [f"- {x['nome']}: {x['link']}" for x in c[k]] + [""]
        (RAIZ / "atendimento").mkdir(exist_ok=True)
        (RAIZ / "atendimento" / f"catalogo-{lang}.md").write_text(chr(10).join(md), encoding="utf-8")
    (RAIZ / "atendimento" / "catalogo.json").write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")


def escrever(caminho, conteudo, manifesto, hoje):
    """Grava a página e atualiza o lastmod só quando o conteúdo muda de verdade.
    O Google ignora lastmod que muda a cada build; com o hash, a data passa a ser confiável."""
    (RAIZ / caminho).mkdir(parents=True, exist_ok=True)
    (RAIZ / caminho / "index.html").write_text(conteudo, encoding="utf-8")
    hsh = hashlib.sha256(conteudo.encode("utf-8")).hexdigest()[:16]
    anterior = manifesto.get(caminho)
    if not anterior or anterior["h"] != hsh:
        manifesto[caminho] = {"h": hsh, "d": hoje}
    return caminho


def sitemap(nome, caminhos, manifesto):
    linhas = "\n".join(f"  <url><loc>{BASE_URL}/{u}</loc><lastmod>{manifesto[u]['d']}</lastmod></url>" for u in caminhos)
    (RAIZ / nome).write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{linhas}\n</urlset>\n', encoding="utf-8")
    return max(manifesto[u]["d"] for u in caminhos)


def main():
    dados = json.loads((RAIZ / "data" / "eventos.json").read_text(encoding="utf-8"))
    hoje = dt.date.today().isoformat()
    eventos = sorted([x for x in dados["eventos"] if x["data"] >= hoje], key=lambda x: x["data"])
    try:
        noticias = json.loads((RAIZ / "dados.json").read_text(encoding="utf-8")).get("paises", [])
    except (OSError, ValueError):
        noticias = []
    arq_manifesto = RAIZ / "data" / "lastmod.json"
    try:
        manifesto = json.loads(arq_manifesto.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        manifesto = {}
    hubs = montar_hubs(eventos)
    grupos = {"paginas": [], "esportes": [], "shows": [], "guias": []}
    for lang in IDIOMAS:
        grupos["paginas"].append(escrever(caminho_home(lang), home(lang, eventos, noticias, hubs), manifesto, hoje))
        for ev in eventos:
            grupo = "shows" if ev["tipo"] == "concert" else "esportes"
            grupos[grupo].append(escrever(caminho_evento(lang, ev["slug"]), evento(lang, ev, eventos, hubs), manifesto, hoje))
        for g in hubs.values():
            grupos["guias"].append(escrever(caminho_hub(lang, g), hub(lang, g, eventos, hubs), manifesto, hoje))
    for lang in IDIOMAS:
        grupos["paginas"].append(escrever(PRIV[lang]["path"], privacidade(lang), manifesto, hoje))
        grupos["paginas"].append(escrever(C.COMO_FUNCIONA[lang]["path"], como_funciona(lang), manifesto, hoje))
        grupos["paginas"].append(escrever(C.DIVULGACAO[lang]["path"], divulgacao(lang), manifesto, hoje))
        grupos["guias"].append(escrever(C.GUIA[lang]["path"], guia(lang, eventos, hubs), manifesto, hoje))
        grupos["guias"].append(escrever(C.GUIA_BARCA[lang]["path"], guia_barca(lang, eventos), manifesto, hoje))
    gerar_catalogo(eventos)
    import pins  # arte vertical dos pins do Pinterest (assets/pins/), redesenhada só quando muda
    feitas = pins.gerar_imagens(eventos)
    if feitas:
        print(f"{feitas} arte(s) de pin do Pinterest gerada(s).")
    # Um sitemap por tipo de página, reunidos num índice. Separar facilita ver no Search Console
    # quantas páginas de evento, de show e de guia foram indexadas.
    nomes = {"paginas": "sitemap-paginas.xml", "esportes": "sitemap-esportes.xml", "shows": "sitemap-shows.xml", "guias": "sitemap-guias.xml"}
    indice = []
    for grupo, caminhos in grupos.items():
        alvo = RAIZ / nomes[grupo]
        if caminhos:
            indice.append((nomes[grupo], sitemap(nomes[grupo], caminhos, manifesto)))
        elif alvo.exists():
            alvo.unlink()
    entradas = "\n".join(f"  <sitemap><loc>{BASE_URL}/{n}</loc><lastmod>{d}</lastmod></sitemap>" for n, d in indice)
    (RAIZ / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entradas}\n</sitemapindex>\n', encoding="utf-8")
    (RAIZ / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /ir/\nDisallow: /go/\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
    for ev in eventos:  # gateway /go/ de cada parceiro ativo; não entra no sitemap
        for lang in IDIOMAS:
            for pk, _p, destino in opcoes_compra(lang, ev):
                (RAIZ / caminho_go(pk, lang, ev)).mkdir(parents=True, exist_ok=True)
                (RAIZ / caminho_go(pk, lang, ev) / "index.html").write_text(pagina_go(pk, lang, ev, destino), encoding="utf-8")
    for ev in eventos:  # endereços antigos /ir/ continuam funcionando (links já compartilhados)
        for lang in IDIOMAS:
            (RAIZ / caminho_ir(ev, lang)).mkdir(parents=True, exist_ok=True)
            (RAIZ / caminho_ir(ev, lang) / "index.html").write_text(pagina_ir(ev, lang), encoding="utf-8")
    if INDEXNOW_KEY:
        (RAIZ / f"{INDEXNOW_KEY}.txt").write_text(INDEXNOW_KEY, encoding="utf-8")
    vivos = {u for cs in grupos.values() for u in cs}
    manifesto = {k: v for k, v in sorted(manifesto.items()) if k in vivos}
    arq_manifesto.write_text(json.dumps(manifesto, indent=1) + "\n", encoding="utf-8")
    n = sum(len(c) for c in grupos.values())
    print(f"{n} páginas geradas: {len(eventos)} eventos e {len(hubs)} guias, em {len(IDIOMAS)} idiomas.")


if __name__ == "__main__":
    main()
