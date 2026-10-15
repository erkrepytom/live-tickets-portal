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
import os
import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# Troque para https://mytickets.tours quando o domínio apontar para o GitHub Pages.
BASE_URL = "https://mytickets.tours"
AFILIADO = "6821d72fcdbe3"
# Todos os idiomas usam o site principal do parceiro, onde o a_aid é contabilizado.
PARCEIRO = {"pt": "https://sportsevents365.com", "en": "https://sportsevents365.com", "es": "https://sportsevents365.com"}
IDIOMAS = ["pt", "en", "es"]
# Formulário de alertas: o FormSubmit entrega cada cadastro como e-mail na caixa do Titan.
# Coloque aqui https://formsubmit.co/ajax/<seu-email-titan> (ou o código aleatório que o
# FormSubmit envia depois da ativação). Vazio = formulário mostra "em breve".
FORM_ENDPOINT = "https://formsubmit.co/ajax/email@mytickets.tours"
# ID de medição do Google Analytics 4 (G-XXXXXXX). Vazio = sem Analytics no site.
GA_MEASUREMENT_ID = ""
HREFLANG = {"pt": "pt-BR", "en": "en", "es": "es"}
FOTO_TOPO = "hero.jpg"  # imagens locais ficam em assets/img (banners do portal anterior)

T = {
 "pt": {
  "brand_title": "MyTickets Tours | Ingressos para esporte e shows no mundo todo",
  "home_desc": "Ingressos para La Liga, Serie A, Champions League, NBA, Fórmula 1, tênis e shows internacionais, com o guia de cada evento. Venda e entrega pela SportsEvents365.",
  "nav": ["Partidas", "Explorar", "Como funciona", "Alertas"], "cta": "Ver ingressos",
  "hero_kicker": "Ingressos para esporte e shows no mundo todo", "hero_l1": "PARTIDAS PARA", "hero_l2": "O JOGO", "hero_h1": "Partidas para o jogo",
  "hero_sub": "Escolha o evento, entenda a viagem e compre no parceiro oficial. Em português, inglês e espanhol.",
  "hero_cta2": "Receber alertas", "hero_note": "Ingressos vendidos e entregues pela SportsEvents365.", "gate": "PORTÃO",
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
  "ev_title": "{t}: ingressos e guia | MyTickets Tours", "ev_desc": "Ingressos para {t} em {d}, {v}, {c}. Como chegar, dicas de setor e compra no parceiro oficial.",
  "date_note": "Data do catálogo do parceiro. O horário é confirmado pelo organizador.",
 },
 "en": {
  "brand_title": "MyTickets Tours | Tickets for sports and shows worldwide",
  "home_desc": "Tickets for La Liga, Serie A, the Champions League, NBA, Formula 1, tennis and concerts worldwide, with a guide to every event. Sold and delivered by SportsEvents365.",
  "nav": ["Departures", "Explore", "How it works", "Alerts"], "cta": "See tickets",
  "hero_kicker": "Tickets for sports and shows worldwide", "hero_l1": "DEPARTURES TO", "hero_l2": "THE GAME", "hero_h1": "Departures to the game",
  "hero_sub": "Pick the event, plan the trip and buy from the official partner. In Portuguese, English and Spanish.",
  "hero_cta2": "Get alerts", "hero_note": "Tickets sold and delivered by SportsEvents365.", "gate": "GATE",
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
  "ev_title": "{t}: tickets and guide | MyTickets Tours", "ev_desc": "Tickets for {t} on {d} at {v}, {c}. Getting there, seating tips and booking with the official partner.",
  "date_note": "Date from the partner's catalogue. Start time is confirmed by the organizer.",
 },
 "es": {
  "brand_title": "MyTickets Tours | Entradas para deportes y shows en todo el mundo",
  "home_desc": "Entradas para La Liga, Serie A, Champions League, NBA, Fórmula 1, tenis y conciertos internacionales, con la guía de cada evento. Venta y entrega por SportsEvents365.",
  "nav": ["Salidas", "Explorar", "Cómo funciona", "Alertas"], "cta": "Ver entradas",
  "hero_kicker": "Entradas para deportes y shows en todo el mundo", "hero_l1": "SALIDAS HACIA", "hero_l2": "EL PARTIDO", "hero_h1": "Salidas hacia el partido",
  "hero_sub": "Elige el evento, planea el viaje y compra en el socio oficial. En portugués, inglés y español.",
  "hero_cta2": "Recibir alertas", "hero_note": "Entradas vendidas y entregadas por SportsEvents365.", "gate": "PUERTA",
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
  "ev_title": "{t}: entradas y guía | MyTickets Tours", "ev_desc": "Entradas para {t} el {d} en {v}, {c}. Cómo llegar, consejos de sector y compra en el socio oficial.",
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

ESPORTES = [  # (nome por idioma, caminho no parceiro, foto do site anterior)
 ({"pt": "Futebol", "en": "Football", "es": "Fútbol"}, "/events/type/1000", "10-brazil.jpg"),
 ({"pt": "Tênis", "en": "Tennis", "es": "Tenis"}, "/events/type/1001", "photo-1554068865-24cecd4e34b8"),
 ({"pt": "Basquete", "en": "Basketball", "es": "Baloncesto"}, "/events/type/1002", "photo-1546519638-68e109498ffc"),
 ({"pt": "Automobilismo", "en": "Motor racing", "es": "Automovilismo"}, "/events/type/1003", "01-formula-1.jpg"),
 ({"pt": "Rúgbi", "en": "Rugby", "es": "Rugby"}, "/events/type/1020", "08-six-nations.jpg"),
 ({"pt": "Beisebol", "en": "Baseball", "es": "Béisbol"}, "/events/type/1005", "photo-1508344928928-7165b67de128"),
 ({"pt": "Hóquei no gelo", "en": "Ice hockey", "es": "Hockey sobre hielo"}, "/events/type/1010", "photo-1515703407324-5f753afd8be8"),
 ({"pt": "Shows", "en": "Concerts", "es": "Conciertos"}, "/concerts", "11-concerts.jpg"),
]
COMPETICOES = [("Premier League", "premier-league"), ("La Liga", "la-liga"), ("Serie A", "serie-a"), ("NBA", "nba"),
               ("NHL", "nhl"), ("MLB", "major-league-baseball"), ("Fórmula 1|Formula 1|Fórmula 1", "formula-1")]
TIMES = [("FC Barcelona", "barcelona-fc"), ("AC Milan", "ac-milan"), ("Inter", "inter"), ("AS Roma", "as-roma")]
CIDADES = [("Barcelona|Barcelona|Barcelona", "barcelona"), ("Madri|Madrid|Madrid", "madrid"), ("Roma|Rome|Roma", "rome"),
           ("Milão|Milan|Milán", "milano"), ("Londres|London|Londres", "london"), ("Paris|Paris|París", "paris"),
           ("Amsterdã|Amsterdam|Ámsterdam", "amsterdam"), ("Berlim|Berlin|Berlín", "berlin")]
ARTISTAS = [("Oasis", "oasis"), ("Stevie Wonder", "steviewonder"), ("Andrea Bocelli", "andrea-bocelli"), ("Shakira", "shakira"),
            ("BTS", "bts"), ("Celine Dion", "celine-dion"), ("Dua Lipa", "dua-lipa"), ("Backstreet Boys", "backstreet-boys")]

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


def parceiro(lang, caminho):
    return f"{PARCEIRO[lang]}{caminho}?a_aid={AFILIADO}"


def foto(img, w=1200, pagina=""):
    """Foto do Unsplash (id photo-...) ou imagem local do portal anterior em assets/img."""
    if img.startswith("photo-"):
        return f"https://images.unsplash.com/{img}?w={w}&q=70&auto=format&fit=crop"
    return rel(pagina, f"assets/img/{img}") + versao(f"assets/img/{img}")


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
    alvo = ' target="_blank" rel="sponsored noopener"' if ext else ""
    s = ' <span class="arrow" aria-hidden="true">→</span>' if seta else ""
    return f'<a class="{cls}" data-magnetic href="{e(href)}"{alvo}><span class="mag-inner">{texto}{s}</span></a>'


def ga_tag():
    if not GA_MEASUREMENT_ID:
        return ""
    g = GA_MEASUREMENT_ID
    return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={g}"></script>'
            f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{g}');</script>")


def cabeca(lang, pagina, titulo, desc, alternos, extra=""):
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
    langs = "".join(f'<a href="{rel(pagina, alternos[l])}" hreflang="{HREFLANG[l]}" aria-current="{str(l == lang).lower()}">{l.upper()}</a>' for l in IDIOMAS)
    return f"""<header class="top">
  <div class="wrap">
    <a class="brand" href="{home}" aria-label="MyTickets Tours">MY<b>TICKETS</b>.TOURS</a>
    <nav class="nav" aria-label="Menu">{nav}</nav>
    <div class="top-r">
      <nav class="langs" aria-label="Idioma / Language">{langs}</nav>
      {mag(parceiro(lang, '/'), e(t['cta']), 'btn btn-signal btn-sm', seta=False)}
    </div>
  </div>
</header>"""


def alertas(lang, eventos, escolhido=None):
    t = T[lang]
    ops = "".join(f'<option value="{ev["slug"]}"{" selected" if ev["slug"] == escolhido else ""}>{e(L(ev["titulo"], lang))}</option>' for ev in eventos)
    lops = "".join(f'<option value="{l}"{" selected" if l == lang else ""}>{n}</option>' for l, n in [("pt", "Português"), ("en", "English"), ("es", "Español")])
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


def rodape(lang, pagina, alternos):
    t = T[lang]
    langs = "".join(f'<a href="{rel(pagina, alternos[l])}" hreflang="{HREFLANG[l]}">{n}</a>' for l, n in [("pt", "PORTUGUÊS"), ("en", "ENGLISH"), ("es", "ESPAÑOL")])
    return f"""<footer class="foot">
  <div class="wrap">
    <a class="brand" href="{rel(pagina, caminho_home(lang))}">MY<b>TICKETS</b>.TOURS</a>
    <p class="foot-disc">{e(t['foot_disc'])}</p>
    <div class="foot-links">{langs}<a href="{rel(pagina, PRIV[lang]['path'])}">{PRIV[lang]['link']}</a><a href="{e(parceiro(lang, '/'))}" target="_blank" rel="sponsored noopener">SPORTSEVENTS365</a></div>
    <p>{e(RESPONSAVEL)} · {CONTATO_EMAIL}</p>
    <p>© {dt.date.today().year} MyTickets Tours</p>
  </div>
</footer>
<div class="cur off" id="cur-blob" aria-hidden="true"><em>{'VER' if lang != 'en' else 'VIEW'}</em></div>
<div class="cur off" id="cur-dot" aria-hidden="true"></div>
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


def home(lang, eventos, noticias):
    t = T[lang]
    pagina = caminho_home(lang)
    alternos = {l: caminho_home(l) for l in IDIOMAS}
    solar_css = (RAIZ / "assets" / "solar-banner.css").read_text(encoding="utf-8")
    h = cabeca(lang, pagina, t["brand_title"], t["home_desc"], alternos, f"<style>\n{solar_css}</style>")
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
        f'<a class="flapline b-status blink" href="{e(parceiro(lang, "/event/" + str(ev["id"])))}" target="_blank" rel="sponsored noopener" data-magnetic data-flap="{t["go"]}" data-w="8" aria-label="{e(t["go"])}: {e(L(ev["titulo"], lang))}">{t["go"]}</a>'
        f'</div>' for ev in eventos)
    atributos = ["", "", ' class="b-city"', ' style="justify-self:end"']
    head_row = "".join(f"<span{a}>{c}</span>" for a, c in zip(atributos, t["cols"]))
    cards = "".join(cartao(lang, pagina, ev) for ev in eventos[:3])
    tiles = "".join(f'<a class="ptile" href="{e(parceiro(lang, p))}" target="_blank" rel="sponsored noopener"><span class="photo" style="{bg(img, 600, pagina)}"></span><span>{e(L(n, lang))}</span></a>' for n, p, img in ESPORTES)
    def chips(itens, base):
        return "".join(f'<a class="chip" href="{e(parceiro(lang, base + s))}" target="_blank" rel="sponsored noopener">{e(L(n, lang))}</a>' for n, s in itens)
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
      <p class="hero-note">{e(t['hero_note'])}</p>
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
    <div class="cards">{cards}</div>
  </div>
</section>

<section class="band" id="explorar" aria-labelledby="exp-h" style="padding-top:0">
  <div class="wrap explore">
    <div class="sec-head" style="margin:0"><div><p class="kicker">{e(t['exp_kicker'])}</p><h2 id="exp-h" data-scramble>{e(t['exp_h'])}</h2></div><p>{e(t['exp_sub'])}</p></div>
    <div class="tiles-photo">{tiles}</div>
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
      <a href="{e(parceiro(lang, '/'))}" target="_blank" rel="sponsored noopener" data-magnetic><span class="mag-inner">{e(t['cta'])} →</span></a>
    </div>
  </div>
</section>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script src="{rel(pagina, 'assets/solar.js')}{versao('assets/solar.js')}"></script>

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


def evento(lang, ev, eventos):
    t = T[lang]
    pagina = caminho_evento(lang, ev["slug"])
    alternos = {l: caminho_evento(l, ev["slug"]) for l in IDIOMAS}
    titulo = L(ev["titulo"], lang)
    cidade = L(ev["cidade"], lang)
    dlonga = data_longa(ev["data"], lang)
    tipo = "MusicEvent" if ev["tipo"] == "concert" else "SportsEvent"
    ld = {"@context": "https://schema.org", "@type": tipo, "name": titulo, "startDate": ev["data"],
          "eventStatus": "https://schema.org/EventScheduled", "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
          "location": {"@type": "Place", "name": ev["local"], "address": {"@type": "PostalAddress", "addressLocality": cidade, "addressCountry": L(ev["pais"], lang)}},
          "image": [foto_abs(ev.get("banner", ev["img"]))], "description": L(ev["intro"], lang),
          "offers": {"@type": "Offer", "url": parceiro(lang, f"/event/{ev['id']}"), "availability": "https://schema.org/InStock"}}
    if ev.get("artista"):
        ld["performer"] = {"@type": "MusicGroup", "name": ev["artista"]["nome"]}
    extra = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    h = cabeca(lang, pagina, t["ev_title"].format(t=titulo), t["ev_desc"].format(t=titulo, d=dlonga, v=ev["local"], c=cidade), alternos, extra)

    def link_parceiro(nome, dock):
        return f'<a href="{e(parceiro(lang, dock))}" target="_blank" rel="sponsored noopener">{e(nome)}</a>' if dock else e(nome)
    comp = ev["competicao"]
    comp_nome = L(comp["nome"], lang)
    cidade_html = link_parceiro(cidade, ev["cidade"].get("dock"))
    if ev.get("artista"):
        quarto = (t["f_artist"], link_parceiro(ev["artista"]["nome"], ev["artista"]["dock"]))
    else:
        quarto = (t["f_comp"], link_parceiro(comp_nome, comp.get("dock")))
    tipo_nome = TIPO_NOME[ev["tipo"]][lang]
    kicker_tipo = link_parceiro(tipo_nome, f"/events/type/{ev['esporte_tipo']}" if ev["esporte_tipo"] else "/concerts")
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
    tambem.append(link_parceiro(tipo_nome, f"/events/type/{ev['esporte_tipo']}" if ev["esporte_tipo"] else "/concerts"))
    chegar = "".join(f"<li>{e(x)}</li>" for x in ev["chegar"][lang])
    dicas = "".join(f"<li>{e(x)}</li>" for x in DICAS[ev["tipo"]][lang])
    tambem_html = "".join(f"<li>{x}</li>" for x in tambem)
    outros = [x for x in eventos if x["slug"] != ev["slug"]]
    idx = eventos.index(ev)
    outros = (eventos[idx + 1:] + eventos[:idx])[:3]
    mais = "".join(cartao(lang, pagina, x) for x in outros)
    ingresso = parceiro(lang, f"/event/{ev['id']}")
    corpo = f"""
<body>
{topo(lang, pagina, alternos)}
<main>
<section class="ev-hero" data-parallax aria-labelledby="ev-h">
  <div class="layer l-photo photo" data-depth="0.15" style="{bg(ev.get('banner', ev['img']), 1800, pagina, 'opacity:.55')}"></div>
  <div class="layer l-shade"></div>
  <div class="wrap on-night">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{rel(pagina, caminho_home(lang))}">{e(t['home'])}</a><span aria-hidden="true">›</span><a href="{rel(pagina, caminho_home(lang))}#partidas">{e(t['events'])}</a><span aria-hidden="true">›</span><span>{e(titulo)}</span></nav>
    <p class="kicker">{kicker_tipo} · {link_parceiro(comp_nome, comp.get('dock'))}</p>
    <h1 id="ev-h">{e(titulo)}</h1>
    <span class="flapline" data-flap="{e(L(ev['painel'], lang))}" data-w="22" aria-hidden="true">{e(L(ev['painel'], lang))}</span>
    <dl class="facts">
      <div class="fact"><dt>{e(t['f_date'])}</dt><dd>{e(dlonga)}</dd></div>
      <div class="fact"><dt>{e(t['f_venue'])}</dt><dd>{e(ev['local'])}</dd></div>
      <div class="fact"><dt>{e(t['f_city'])}</dt><dd>{cidade_html}, {e(L(ev['pais'], lang))}</dd></div>
      <div class="fact"><dt>{e(quarto[0])}</dt><dd>{quarto[1]}</dd></div>
    </dl>
    <div class="ev-cta">
      {mag(ingresso, e(t['ev_cta']))}
      {mag('#alertas', e(t['ev_alert']), 'btn btn-ghost', ext=False, seta=False)}
    </div>
    <p class="disclose">{e(t['aff_note'])} {e(t['date_note'])}</p>
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
      <div class="tips">
        <div><h2>{e(t['get_h'])}</h2><ul>{chegar}</ul></div>
        <div><h2>{e(t['tips_h'])}</h2><ul>{dicas}</ul></div>
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
    <div class="cards">{mais}</div>
  </div>
</section>
{alertas(lang, eventos, ev['slug'])}
</main>
"""
    return h + corpo + rodape(lang, pagina, alternos)


PRIV = {
 "pt": {"path": "privacidade/", "link": "PRIVACIDADE E CONTATO", "title": "Política de privacidade | MyTickets Tours",
  "desc": "Como o MyTickets Tours trata seus dados, e como falar conosco.", "h1": "Política de privacidade",
  "updated": "Atualizada em 14 de outubro de 2026.",
  "sections": [
   ("Quem somos", ["O MyTickets Tours (mytickets.tours) é um site afiliado de ingressos para eventos esportivos e shows, mantido por Everton Bras.",
                   "Não vendemos ingressos. A compra acontece no site da SportsEvents365, que é responsável pela venda, pelo pagamento e pela entrega."]),
   ("Que dados tratamos", ["Navegação: os serviços que hospedam o site (Microsoft Azure e GitHub) registram dados técnicos, como endereço IP e tipo de navegador, para manter o site no ar e protegido.",
                           "Alertas de venda: se você pedir um alerta, guardamos seu e-mail, o evento escolhido e o idioma, com o seu consentimento. O cadastro chega à nossa caixa de e-mail pelo serviço FormSubmit.",
                           "Atendimento no WhatsApp: se você falar conosco, tratamos seu número e suas mensagens para responder, pela plataforma da Meta.",
                           "Cookies: hoje o site não usa cookies de estatística nem de publicidade. Se passarmos a usar o Google Analytics, vamos pedir seu consentimento antes.",
                           "Links de afiliado: quando você clica num link para a SportsEvents365, o parceiro registra que você veio do MyTickets (código a_aid) para calcular nossa comissão. A partir daí vale a política de privacidade da SportsEvents365."]),
   ("Para que usamos", ["Enviar o alerta que você pediu, responder suas mensagens e manter o site funcionando e seguro. Não vendemos nem alugamos seus dados."]),
   ("Base legal", ["Consentimento para alertas, atendimento e estatísticas (LGPD, art. 7º, I; GDPR, art. 6(1)(a)). Interesse legítimo para a segurança e o funcionamento do site (LGPD, art. 7º, IX; GDPR, art. 6(1)(f))."]),
   ("Por quanto tempo", ["E-mails de alerta: até o evento acontecer ou até você pedir para sair, o que vier primeiro. Conversas do WhatsApp: até 12 meses."]),
   ("Compartilhamento e transferência internacional", ["Seus dados passam apenas pelos fornecedores citados acima (Microsoft, GitHub, FormSubmit, Meta e, se ativado, Google). Eles podem tratar os dados fora do seu país, sob as garantias contratuais de cada um."]),
   ("Seus direitos", ["Você pode pedir acesso, correção, exclusão e portabilidade dos seus dados, e retirar o consentimento a qualquer momento. Escreva para email@mytickets.tours e respondemos em até 15 dias.",
                      "Você também pode reclamar à ANPD, no Brasil, ou à autoridade de proteção de dados do seu país."]),
   ("Menores de idade", ["O site não é voltado para menores de 18 anos. Compras de ingressos devem ser feitas por adultos."]),
   ("Mudanças", ["Se esta política mudar, a data no topo da página será atualizada."]),
  ],
  "contact_h": "Contato", "resp": "Responsável"},
 "en": {"path": "en/privacy/", "link": "PRIVACY AND CONTACT", "title": "Privacy policy | MyTickets Tours",
  "desc": "How MyTickets Tours handles your data, and how to reach us.", "h1": "Privacy policy",
  "updated": "Last updated October 14, 2026.",
  "sections": [
   ("Who we are", ["MyTickets Tours (mytickets.tours) is an affiliate site for sports and concert tickets, run by Everton Bras.",
                   "We do not sell tickets. Purchases happen on the SportsEvents365 site, which is responsible for the sale, payment and delivery."]),
   ("What data we handle", ["Browsing: the services that host the site (Microsoft Azure and GitHub) log technical data, such as IP address and browser type, to keep the site running and secure.",
                            "Sale alerts: if you ask for an alert, we keep your email, the event you chose and your language, with your consent. The sign-up reaches our inbox through the FormSubmit service.",
                            "WhatsApp support: if you message us, we handle your number and messages to reply, through Meta's platform.",
                            "Cookies: the site currently uses no analytics or advertising cookies. If we start using Google Analytics, we will ask for your consent first.",
                            "Affiliate links: when you click a link to SportsEvents365, the partner records that you came from MyTickets (code a_aid) to calculate our commission. From then on, the SportsEvents365 privacy policy applies."]),
   ("Why we use it", ["To send the alert you asked for, reply to your messages and keep the site running and secure. We never sell or rent your data."]),
   ("Legal basis", ["Consent for alerts, support and analytics (GDPR Art. 6(1)(a); LGPD Art. 7, I). Legitimate interest for security and operation of the site (GDPR Art. 6(1)(f); LGPD Art. 7, IX)."]),
   ("How long we keep it", ["Alert emails: until the event takes place or until you unsubscribe, whichever comes first. WhatsApp conversations: up to 12 months."]),
   ("Sharing and international transfers", ["Your data only goes through the providers named above (Microsoft, GitHub, FormSubmit, Meta and, if enabled, Google). They may process data outside your country under their own contractual safeguards."]),
   ("Your rights", ["You can ask to access, correct, delete or port your data, and withdraw consent at any time. Write to email@mytickets.tours and we will reply within 15 days.",
                    "You can also complain to the data protection authority in your country."]),
   ("Minors", ["The site is not aimed at people under 18. Ticket purchases must be made by adults."]),
   ("Changes", ["If this policy changes, the date at the top of the page will be updated."]),
  ],
  "contact_h": "Contact", "resp": "Responsible person"},
 "es": {"path": "es/privacidad/", "link": "PRIVACIDAD Y CONTACTO", "title": "Política de privacidad | MyTickets Tours",
  "desc": "Cómo MyTickets Tours trata tus datos y cómo contactarnos.", "h1": "Política de privacidad",
  "updated": "Actualizada el 14 de octubre de 2026.",
  "sections": [
   ("Quiénes somos", ["MyTickets Tours (mytickets.tours) es un sitio afiliado de entradas para eventos deportivos y conciertos, gestionado por Everton Bras.",
                      "No vendemos entradas. La compra se hace en el sitio de SportsEvents365, responsable de la venta, el pago y la entrega."]),
   ("Qué datos tratamos", ["Navegación: los servicios que alojan el sitio (Microsoft Azure y GitHub) registran datos técnicos, como la dirección IP y el navegador, para mantener el sitio activo y seguro.",
                           "Alertas de venta: si pides una alerta, guardamos tu correo, el evento elegido y el idioma, con tu consentimiento. El registro llega a nuestro correo mediante el servicio FormSubmit.",
                           "Atención por WhatsApp: si nos escribes, tratamos tu número y tus mensajes para responderte, a través de la plataforma de Meta.",
                           "Cookies: hoy el sitio no usa cookies de estadística ni de publicidad. Si empezamos a usar Google Analytics, te pediremos el consentimiento antes.",
                           "Enlaces de afiliado: al hacer clic en un enlace a SportsEvents365, el socio registra que llegaste desde MyTickets (código a_aid) para calcular nuestra comisión. Desde ese momento rige la política de privacidad de SportsEvents365."]),
   ("Para qué los usamos", ["Enviar la alerta que pediste, responder tus mensajes y mantener el sitio funcionando y seguro. Nunca vendemos ni alquilamos tus datos."]),
   ("Base legal", ["Consentimiento para alertas, atención y estadísticas (RGPD, art. 6.1.a; LGPD, art. 7, I). Interés legítimo para la seguridad y el funcionamiento del sitio (RGPD, art. 6.1.f; LGPD, art. 7, IX)."]),
   ("Cuánto tiempo", ["Correos de alerta: hasta que se celebre el evento o hasta que te des de baja, lo que ocurra primero. Conversaciones de WhatsApp: hasta 12 meses."]),
   ("Cesión y transferencias internacionales", ["Tus datos solo pasan por los proveedores citados (Microsoft, GitHub, FormSubmit, Meta y, si se activa, Google). Pueden tratarlos fuera de tu país bajo sus propias garantías contractuales."]),
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
                "ingressos": parceiro(lang, f"/event/{ev['id']}"),
                "guia": f"{BASE_URL}/{caminho_evento(lang, ev['slug'])}",
                "como_chegar": ev["chegar"][lang], "dicas": DICAS[ev["tipo"]][lang],
            } for ev in eventos],
            "competicoes": [{"nome": L(n, lang), "link": parceiro(lang, "/dock/competition/" + s)} for n, s in COMPETICOES],
            "times": [{"nome": L(n, lang), "link": parceiro(lang, "/dock/team/" + s)} for n, s in TIMES],
            "cidades": [{"nome": L(n, lang), "link": parceiro(lang, "/dock/cities/" + s)} for n, s in CIDADES],
            "artistas": [{"nome": L(n, lang), "link": parceiro(lang, "/dock/music/" + s)} for n, s in ARTISTAS],
            "esportes": [{"nome": L(n, lang), "link": parceiro(lang, p)} for n, p, _ in ESPORTES],
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


def main():
    dados = json.loads((RAIZ / "data" / "eventos.json").read_text(encoding="utf-8"))
    hoje = dt.date.today().isoformat()
    eventos = sorted([x for x in dados["eventos"] if x["data"] >= hoje], key=lambda x: x["data"])
    try:
        noticias = json.loads((RAIZ / "dados.json").read_text(encoding="utf-8")).get("paises", [])
    except (OSError, ValueError):
        noticias = []
    urls = []
    for lang in IDIOMAS:
        p = caminho_home(lang)
        (RAIZ / p).mkdir(parents=True, exist_ok=True)
        (RAIZ / p / "index.html").write_text(home(lang, eventos, noticias), encoding="utf-8")
        urls.append(p)
        for ev in eventos:
            p = caminho_evento(lang, ev["slug"])
            (RAIZ / p).mkdir(parents=True, exist_ok=True)
            (RAIZ / p / "index.html").write_text(evento(lang, ev, eventos), encoding="utf-8")
            urls.append(p)
    for lang in IDIOMAS:
        p = PRIV[lang]["path"]
        (RAIZ / p).mkdir(parents=True, exist_ok=True)
        (RAIZ / p / "index.html").write_text(privacidade(lang), encoding="utf-8")
        urls.append(p)
    gerar_catalogo(eventos)
    mapa ="\n".join(f"  <url><loc>{BASE_URL}/{u}</loc><lastmod>{hoje}</lastmod></url>" for u in urls)
    (RAIZ / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{mapa}\n</urlset>\n', encoding="utf-8")
    (RAIZ / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
    print(f"{len(urls)} páginas geradas ({len(eventos)} eventos x {len(IDIOMAS)} idiomas + 3 iniciais).")


if __name__ == "__main__":
    main()
