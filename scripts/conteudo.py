"""Textos editoriais do MyTickets Tours (PT, EN, ES), usados por gerar_paginas.py.

Regras para editar:
- Fatos sobre entrega, garantia, cancelamento e contato vêm dos Termos e do FAQ da
  SportsEvents365 (https://sportsevents365.com/terms-and-conditions), conferidos em 15/10/2026.
  Se os termos do parceiro mudarem, atualize PARCEIRO e os textos que citam essas regras.
- Regras de estádio que variam por jogo (tamanho de bolsa, documento) ficam em termos gerais
  e mandam o leitor conferir o e-mail do parceiro. Não escreva regra específica sem fonte.
"""

import re

PARCEIRO = {
    "nome": "SportsEvents365",
    "empresa": "Sports Events 365 Ltd.",
    "endereco": "Agias Fylaxeos 95, 3087 Limassol, Chipre",
    "endereco_en": "Agias Fylaxeos 95, 3087 Limassol, Cyprus",
    "endereco_es": "Agias Fylaxeos 95, 3087 Limasol, Chipre",
    "emergencia": "+32 466 90 16 16",
    "termos": "https://sportsevents365.com/terms-and-conditions",
    "faq": "https://sportsevents365.com/faq",
    "conferido": "2026-10-15",
}

# Artigo antes do nome do local, para títulos como "guia do San Siro" / "guía de la Rod Laver Arena".
ARTIGO_LOCAL = {
    "Rod Laver Arena": {"pt": "da", "es": "de la"},
    "Paris La Défense Arena": {"pt": "da", "es": "de la"},
}


def artigo(local, lang):
    padrao = {"pt": "do", "es": "del", "en": "the"}[lang]
    return ARTIGO_LOCAL.get(local, {}).get(lang, padrao)


def titulo_evento(lang, titulo, ano, local, limite=65):
    """Escolhe o título mais completo que cabe no limite do Google (~60-65 caracteres)."""
    ano_txt = "" if ano in titulo else f" {ano}"
    opcoes = [x.format(t=titulo, ano=ano_txt, art=artigo(local, lang), loc=local_curto(local)) for x in ROT[lang]["titulos"]]
    return next((x for x in opcoes if len(x) <= limite), opcoes[-1])


def local_curto(local):
    """'San Siro (Giuseppe Meazza)' -> 'San Siro' para caber no título."""
    return local.split(" (")[0]


# O que levar e o que costuma ser barrado, por tipo de evento.
ENTRADA = {
 "football": {
  "pt": ["Leve passaporte ou documento com foto. Ingressos de revenda às vezes saem no nome de outra pessoa, e o parceiro explica por e-mail o que apresentar.",
         "Mochilas e bolsas grandes costumam ser barradas em estádios europeus. Leve só o essencial numa bolsa pequena.",
         "Garrafas, sinalizadores e objetos cortantes são proibidos. A revista na entrada pode ser demorada em jogos grandes."],
  "en": ["Bring your passport or a photo ID. Resale tickets sometimes carry another person's name, and the partner explains by email what to show.",
         "Backpacks and large bags are often refused at European stadiums. Carry only the essentials in a small bag.",
         "Bottles, flares and sharp objects are banned. Security checks can be slow at big matches."],
  "es": ["Lleva pasaporte o documento con foto. Las entradas de reventa a veces llevan el nombre de otra persona, y el socio explica por correo qué presentar.",
         "Las mochilas y bolsos grandes suelen rechazarse en estadios europeos. Lleva solo lo esencial en un bolso pequeño.",
         "Botellas, bengalas y objetos cortantes están prohibidos. El control de acceso puede tardar en partidos grandes."]},
 "rugby": {
  "pt": ["Leve passaporte ou documento com foto, além do ingresso no formato que o parceiro enviar.",
         "Bolsas grandes podem ser barradas. Uma bolsa pequena evita fila no guarda-volumes.",
         "Chegue cedo: jogos de seleção lotam o transporte nas duas horas antes do início."],
  "en": ["Bring your passport or a photo ID, plus the ticket in whatever format the partner sends.",
         "Large bags may be refused. A small bag saves you the cloakroom queue.",
         "Arrive early: international matches fill public transport in the two hours before kick-off."],
  "es": ["Lleva pasaporte o documento con foto, además de la entrada en el formato que envíe el socio.",
         "Los bolsos grandes pueden rechazarse. Un bolso pequeño evita la cola de consigna.",
         "Llega temprano: los partidos de selecciones llenan el transporte en las dos horas previas."]},
 "f1": {
  "pt": ["Confira se o ingresso vale só para o domingo ou para o fim de semana inteiro, e quais dias dão acesso a qual arquibancada.",
         "As regras de bolsa e de comida variam por circuito. Siga o e-mail do parceiro e a página oficial do GP.",
         "Leve protetor auricular, protetor solar e documento com foto."],
  "en": ["Check whether the ticket covers Sunday only or the whole weekend, and which days give access to which grandstand.",
         "Bag and food rules vary by circuit. Follow the partner's email and the official race page.",
         "Bring ear protection, sunscreen and a photo ID."],
  "es": ["Comprueba si la entrada vale solo para el domingo o para todo el fin de semana, y qué días dan acceso a cada tribuna.",
         "Las reglas de bolsos y comida cambian según el circuito. Sigue el correo del socio y la web oficial del GP.",
         "Lleva protección para los oídos, protector solar y documento con foto."]},
 "nba": {
  "pt": ["Arenas da NBA limitam o tamanho de bolsas. Na dúvida, entre só com celular, carteira e documento.",
         "O ingresso costuma ser digital, no celular. Deixe a bateria carregada e o ingresso salvo antes de sair.",
         "Leve documento com foto."],
  "en": ["NBA arenas limit bag sizes. When in doubt, go in with just your phone, wallet and ID.",
         "Tickets are usually digital, on your phone. Keep the battery charged and the ticket saved before you leave.",
         "Bring a photo ID."],
  "es": ["Los pabellones de la NBA limitan el tamaño de los bolsos. Ante la duda, entra solo con móvil, cartera y documento.",
         "La entrada suele ser digital, en el móvil. Ten la batería cargada y la entrada guardada antes de salir.",
         "Lleva documento con foto."]},
 "tennis": {
  "pt": ["Confira a sessão impressa no ingresso: a final tem sessão própria, separada dos outros jogos do dia.",
         "Há revista de bolsas na entrada do complexo. Bolsas grandes podem ir para o guarda-volumes.",
         "Leve documento com foto, protetor solar e garrafa de água vazia se o local permitir reabastecer."],
  "en": ["Check the session printed on the ticket: the final has its own session, separate from the day's other matches.",
         "Bags are checked at the complex entrance. Large bags may have to go to the cloakroom.",
         "Bring a photo ID, sunscreen and an empty water bottle if the venue allows refills."],
  "es": ["Revisa la sesión impresa en la entrada: la final tiene su propia sesión, separada de los demás partidos del día.",
         "Hay revisión de bolsos en la entrada del complejo. Los bolsos grandes pueden ir a consigna.",
         "Lleva documento con foto, protector solar y una botella vacía si el recinto permite rellenarla."]},
 "concert": {
  "pt": ["Arenas costumam limitar o tamanho de bolsas e proibir câmeras profissionais.",
         "Leve documento com foto e o ingresso no formato que o parceiro enviar.",
         "Os portões abrem bem antes do show. Chegar cedo garante a fila mais curta na pista."],
  "en": ["Arenas usually limit bag sizes and ban professional cameras.",
         "Bring a photo ID and the ticket in whatever format the partner sends.",
         "Doors open well before the show. Arriving early means a shorter queue for the floor."],
  "es": ["Los recintos suelen limitar el tamaño de los bolsos y prohibir cámaras profesionales.",
         "Lleva documento con foto y la entrada en el formato que envíe el socio.",
         "Las puertas abren mucho antes del concierto. Llegar temprano asegura una cola más corta para la pista."]},
}

# Melhor lugar para família x clima de torcida, por tipo. LOCAL_PUBLICO acrescenta detalhes de estádios conhecidos.
PUBLICO = {
 "football": {
  "pt": [("Família", "Laterais e anéis intermediários: boa visão, clima mais tranquilo e saída mais fácil."),
         ("Torcida vibrante", "Atrás dos gols ficam as torcidas organizadas. É o setor mais barulhento, e quase todos ficam em pé."),
         ("Setor do seu time", "O parceiro separa setores da casa e visitantes. Escolha o lado do time que você vai apoiar e evite a camisa do rival no setor errado.")],
  "en": [("Families", "Side stands and middle tiers: good view, calmer atmosphere and easier exit."),
         ("Loud support", "Behind the goals is where the ultras stand. It is the loudest area, and almost everyone stands."),
         ("Your team's end", "The partner separates home and away sections. Pick your team's side and avoid wearing the rival shirt in the wrong section.")],
  "es": [("Familias", "Laterales y anillos intermedios: buena vista, ambiente más tranquilo y salida más fácil."),
         ("Grada de animación", "Detrás de las porterías se ubican los grupos de animación. Es la zona más ruidosa, y casi todos están de pie."),
         ("Sector de tu equipo", "El socio separa sectores locales y visitantes. Elige el lado de tu equipo y evita la camiseta rival en el sector equivocado.")]},
 "rugby": {
  "pt": [("Família", "Laterais, perto do meio-campo: melhor leitura das jogadas e clima amigável."),
         ("Clima de festa", "Atrás dos in-goals o ingresso é mais barato e a torcida canta o jogo todo. No rúgbi as torcidas se misturam sem problema.")],
  "en": [("Families", "Side stands near halfway: best view of the play and a friendly crowd."),
         ("Party atmosphere", "Behind the in-goal areas tickets are cheaper and fans sing all game. Rugby fans mix freely.")],
  "es": [("Familias", "Laterales cerca del medio campo: mejor lectura del juego y ambiente amistoso."),
         ("Ambiente de fiesta", "Detrás de las zonas de ensayo la entrada es más barata y la afición canta todo el partido. En el rugby las aficiones se mezclan sin problema.")]},
 "f1": {
  "pt": [("Família", "Arquibancadas cobertas e com telão: mais conforto num dia longo."),
         ("Emoção", "Arquibancadas em curvas lentas e retas de frenagem mostram mais ultrapassagens.")],
  "en": [("Families", "Covered grandstands with a big screen: more comfort over a long day."),
         ("Action", "Grandstands at slow corners and braking zones show the most overtakes.")],
  "es": [("Familias", "Tribunas cubiertas y con pantalla gigante: más comodidad en un día largo."),
         ("Emoción", "Las tribunas en curvas lentas y zonas de frenada muestran más adelantamientos.")]},
 "nba": {
  "pt": [("Família", "Nível inferior nas laterais ou nível intermediário: visão completa da quadra."),
         ("Economia", "Nível superior e atrás das cestas custam menos e ainda mostram o jogo inteiro.")],
  "en": [("Families", "Lower-level sideline or mid-level seats: a full view of the court."),
         ("Budget", "Upper level and behind the baskets cost less and still show the whole game.")],
  "es": [("Familias", "Nivel inferior en los laterales o nivel intermedio: vista completa de la pista."),
         ("Económico", "El nivel superior y detrás de las canastas cuestan menos y muestran todo el partido.")]},
 "tennis": {
  "pt": [("Família", "Lugares nas laterais da quadra, em fileiras médias: veem os dois jogadores sem virar a cabeça a cada ponto."),
         ("Economia", "Os níveis superiores custam bem menos e, numa arena coberta, a visão continua boa.")],
  "en": [("Families", "Side seats in middle rows: you see both players without turning your head every point."),
         ("Budget", "Upper levels cost far less and, in a covered arena, the view stays good.")],
  "es": [("Familias", "Asientos laterales en filas medias: ves a los dos jugadores sin girar la cabeza en cada punto."),
         ("Económico", "Los niveles superiores cuestan mucho menos y, en un estadio cubierto, la vista sigue siendo buena.")]},
 "concert": {
  "pt": [("Família", "Cadeiras numeradas de frente para o palco: lugar garantido e melhor som."),
         ("Na frente do palco", "Pista em pé: mais perto do artista, mas exige chegar cedo e ficar de pé o show todo.")],
  "en": [("Families", "Reserved seats facing the stage: a guaranteed spot and the best sound."),
         ("Up front", "Standing floor: closest to the artist, but you need to arrive early and stand all night.")],
  "es": [("Familias", "Asientos numerados frente al escenario: lugar asegurado y mejor sonido."),
         ("Delante del escenario", "Pista de pie: más cerca del artista, pero hay que llegar temprano y estar de pie todo el concierto.")]},
}
LOCAL_PUBLICO = {
 "San Siro (Giuseppe Meazza)": {
  "pt": ("No San Siro", "A Curva Sud é a casa da torcida organizada do Milan, e a Curva Nord, da Inter. No dérbi as duas lotam. Para ver com calma, prefira as laterais."),
  "en": ("At San Siro", "The Curva Sud is home to Milan's ultras and the Curva Nord to Inter's. Both are packed for the derby. For a calmer view, choose the side stands."),
  "es": ("En San Siro", "La Curva Sud es la casa de los ultras del Milan y la Curva Nord la del Inter. En el derbi las dos se llenan. Para ver con calma, elige los laterales.")},
 "Camp Nou": {
  "pt": ("No Camp Nou", "Pela regra do parceiro, no Camp Nou um par de lugares pode ficar na diagonal ou lado a lado em fileiras vizinhas, e não só um ao lado do outro."),
  "en": ("At Camp Nou", "Under the partner's rules, a pair of seats at Camp Nou may be diagonal or in adjoining rows, not only side by side."),
  "es": ("En el Camp Nou", "Según las reglas del socio, en el Camp Nou un par de asientos puede estar en diagonal o en filas contiguas, no solo uno al lado del otro.")},
}

# "Como comprar saindo do Brasil" (cauda longa). {t}=evento, {d}=data, {h}=hora, {c}=cidade.
COMPRAR = {
 "pt": {"h": "Como comprar ingresso para {t} saindo do Brasil",
        "passos": ["Abra o evento no parceiro, escolha o setor e a quantidade. O preço aparece em dólar ou euro; no cartão brasileiro entra também o IOF de compra internacional.",
                   "Pague com cartão de crédito internacional. A SportsEvents365 bloqueia o valor e confirma o pedido em até 1 dia útil.",
                   "Informe o hotel ou o endereço de entrega até uma semana antes do evento. A forma de entrega (e-ticket, celular, hotel ou retirada) aparece antes do pagamento.",
                   "Planeje o voo com folga: o horário de {d} às {h} pode mudar por decisão do organizador ou da TV.",
                   "Salve no celular a central de emergência do parceiro ({tel}) para qualquer problema no dia."]},
 "en": {"h": "How to buy {t} tickets from abroad",
        "passos": ["Open the event at the partner, pick the section and quantity. Prices show in dollars or euros; your card may add a foreign transaction fee.",
                   "Pay by credit card. SportsEvents365 holds the amount and confirms the order within 1 business day.",
                   "Give your hotel or delivery address at least a week before the event. The delivery method (e-ticket, mobile, hotel or pickup) is shown before you pay.",
                   "Book flights with some slack: the {d}, {h} start can still be moved by the organizer or broadcasters.",
                   "Save the partner's emergency line ({tel}) on your phone for any problem on the day."]},
 "es": {"h": "Cómo comprar entradas para {t} desde otro país",
        "passos": ["Abre el evento en el socio, elige el sector y la cantidad. El precio aparece en dólares o euros; tu tarjeta puede sumar una comisión por compra internacional.",
                   "Paga con tarjeta de crédito. SportsEvents365 retiene el importe y confirma el pedido en un plazo de 1 día hábil.",
                   "Indica tu hotel o dirección de entrega al menos una semana antes del evento. La forma de entrega (e-ticket, móvil, hotel o recogida) aparece antes de pagar.",
                   "Reserva los vuelos con margen: el horario del {d} a las {h} aún puede cambiar por decisión del organizador o de la TV.",
                   "Guarda en el móvil la línea de emergencia del socio ({tel}) para cualquier problema el día del evento."]},
}

# Perguntas frequentes de cada evento. As respostas seguem os termos do parceiro.
# Terceiro item = qual link acompanha a resposta (ver FAQ_LINK). {of} = canal oficial do evento (OFICIAL).
FAQ = {
 "pt": [
  ("Que horas começa {t}?", "{d}, às {h} no horário local de {c}, segundo o catálogo do parceiro conferido em {conf}. O organizador ainda pode mudar o horário.", "oficial"),
  ("Existe venda oficial para {t}?", "Sim, pelo canal oficial: {of}. Lá o preço é o de face, mas a venda costuma priorizar sócios e esgota rápido em jogos e shows disputados. A SportsEvents365 é revenda: tem lugares quando a venda oficial acaba, com preço que segue a procura.", "oficial"),
  ("Comprar em revenda é seguro? Como não cair em golpe?", "Compre só de empresa identificada, com termos publicados e garantia por escrito. A SportsEvents365 é a {empresa} e tem central de emergência. Desconfie de Pix ou transferência para pessoa física, de preço muito abaixo do mercado e de print do ingresso como prova: o mesmo QR code pode ser vendido várias vezes.", "golpe"),
  ("Meu cartão brasileiro pode ser recusado? Dá para parcelar?", "Pode ser recusado: o antifraude do banco às vezes barra compra internacional. Avise o banco antes e tenha um segundo cartão, como o de uma conta global em dólar ou euro. O preço sai em moeda estrangeira, com IOF cobrado pelo banco; o parcelamento depende do seu cartão e da tela de pagamento do parceiro.", "pagamento"),
  ("O ingresso é nominal? Preciso levar documento?", "Alguns clubes e competições emitem ingresso em nome do comprador e conferem documento na entrada. Na revenda, o ingresso pode estar no nome de outra pessoa, e o parceiro explica antes o que apresentar. Leve o passaporte: os termos da SportsEvents365 permitem pedir cópia dele para emitir o pedido.", "nominal"),
  ("O ingresso é digital?", "Depende do lote. A SportsEvents365 entrega por e-ticket, ingresso no celular, entrega no hotel ou ponto de retirada, e mostra a forma de entrega antes do pagamento. O parceiro pode trocar a forma de entrega se precisar, avisando antes.", "parceiro_faq"),
  ("Como funciona a entrega e quando recebo?", "O pedido é confirmado em até 1 dia útil. Os ingressos chegam perto da data, como é comum na revenda. Informe o hotel até uma semana antes do evento. Se a entrega for no hotel, confira até as 9h do dia do evento se os ingressos chegaram.", "parceiro_faq"),
  ("O ingresso é garantido?", "A SportsEvents365 oferece garantia de entrega: se não entregar os ingressos confirmados por falha dela, devolve até 100% do valor dos ingressos. Qualquer problema no dia deve ser avisado na hora pela central de emergência: {tel}.", "como"),
  ("Por que o preço é maior que o valor impresso no ingresso?", "A SportsEvents365 atua na revenda (mercado secundário), onde o preço segue a procura. Em jogos e shows muito disputados, o preço costuma passar do valor de face.", "comprar"),
  ("Posso cancelar? E se o evento mudar de data?", "O pedido confirmado não pode ser cancelado sem aprovação do parceiro, e o cancelamento pode ter taxa. Se o evento for adiado, o ingresso costuma valer para a nova data; se você não puder ir, o parceiro tenta reembolso ou revenda, sem garantia.", "termos"),
  ("Vamos sentar juntos?", "Sim, os lugares saem em pares, a menos que o lote diga 'Single seats'. Para grupos de 9 ou mais, o parceiro tem um pedido de grupo.", "comprar"),
 ],
 "en": [
  ("What time does {t} start?", "{d}, at {h} local time in {c}, according to the partner's catalogue checked on {conf}. The organizer can still change the time.", "oficial"),
  ("Is there an official sale for {t}?", "Yes, through the official channel: {of}. Prices there are face value, but sales usually favour members and sell out fast for high-demand games and shows. SportsEvents365 is a resale marketplace: it has seats when the official sale runs out, at prices that follow demand.", "oficial"),
  ("Is buying resale safe? How do I avoid scams?", "Buy only from an identified company with published terms and a written guarantee. SportsEvents365 is {empresa} and runs an emergency line. Be wary of bank transfers or payment apps to a private person, prices far below the market, and screenshots of a ticket as 'proof': the same QR code can be sold many times.", "golpe"),
  ("Will my card work? Are there extra fees?", "Your bank's fraud checks sometimes block foreign purchases. Tell your bank before you buy and keep a second card handy. Prices are in dollars or euros, so your card may add a foreign transaction fee and use its own exchange rate.", "pagamento"),
  ("Are tickets in my name? Do I need ID?", "Some clubs and competitions issue tickets in the buyer's name and check ID at the gate. On resale, the ticket may carry someone else's name, and the partner explains in advance what to show. Bring your passport: SportsEvents365's terms allow it to ask for a copy to process the order.", "nominal"),
  ("Is the ticket digital?", "It depends on the listing. SportsEvents365 delivers by e-ticket, mobile ticket, hotel delivery or pickup point, and shows the delivery method before you pay. The partner may change the method if needed, with notice.", "parceiro_faq"),
  ("How does delivery work and when do I get the tickets?", "The order is confirmed within 1 business day. Tickets arrive close to the date, as is usual for resale. Give your hotel details at least a week before the event. For hotel delivery, check by 9 am on the day that the tickets have arrived.", "parceiro_faq"),
  ("Are the tickets guaranteed?", "SportsEvents365 offers a delivery guarantee: if it fails to deliver confirmed tickets for reasons on its side, it refunds up to 100% of the ticket price. Report any problem on the day straight away to the emergency line: {tel}.", "como"),
  ("Why is the price above face value?", "SportsEvents365 works in the resale (secondary) market, where prices follow demand. For high-demand games and shows, prices are often above face value.", "comprar"),
  ("Can I cancel? What if the date changes?", "A confirmed order cannot be cancelled without the partner's approval, and a fee may apply. If the event is postponed, tickets are usually valid for the new date; if you cannot attend, the partner will try to get a refund or resell them, without a guarantee.", "termos"),
  ("Will we sit together?", "Yes, seats come in pairs unless the listing says 'Single seats'. For groups of 9 or more, the partner offers group orders.", "comprar"),
 ],
 "es": [
  ("¿A qué hora empieza {t}?", "{d}, a las {h} hora local de {c}, según el catálogo del socio revisado el {conf}. El organizador todavía puede cambiar el horario.", "oficial"),
  ("¿Hay venta oficial para {t}?", "Sí, por el canal oficial: {of}. Allí el precio es el nominal, pero la venta suele priorizar a los socios y se agota rápido en partidos y conciertos muy buscados. SportsEvents365 es reventa: tiene asientos cuando la venta oficial se acaba, con precios que siguen la demanda.", "oficial"),
  ("¿Es seguro comprar en reventa? ¿Cómo evito estafas?", "Compra solo a una empresa identificada, con términos publicados y garantía por escrito. SportsEvents365 es {empresa} y tiene línea de emergencia. Desconfía de transferencias o apps de pago a una persona física, de precios muy por debajo del mercado y de capturas de la entrada como 'prueba': el mismo código QR puede venderse varias veces.", "golpe"),
  ("¿Mi tarjeta puede ser rechazada? ¿Hay comisiones?", "El antifraude del banco a veces bloquea compras en el extranjero. Avisa a tu banco antes y ten una segunda tarjeta a mano. El precio sale en dólares o euros, así que tu tarjeta puede sumar una comisión por compra internacional y aplicar su propio tipo de cambio.", "pagamento"),
  ("¿La entrada es nominal? ¿Necesito documento?", "Algunos clubes y competiciones emiten entradas a nombre del comprador y piden documento en el acceso. En la reventa, la entrada puede ir a nombre de otra persona, y el socio explica antes qué presentar. Lleva el pasaporte: los términos de SportsEvents365 permiten pedir una copia para tramitar el pedido.", "nominal"),
  ("¿La entrada es digital?", "Depende del lote. SportsEvents365 entrega por e-ticket, entrada en el móvil, entrega en el hotel o punto de recogida, y muestra la forma de entrega antes del pago. El socio puede cambiar la forma de entrega si hace falta, avisando antes.", "parceiro_faq"),
  ("¿Cómo funciona la entrega y cuándo la recibo?", "El pedido se confirma en un plazo de 1 día hábil. Las entradas llegan cerca de la fecha, como es habitual en la reventa. Indica tu hotel al menos una semana antes del evento. Si la entrega es en el hotel, comprueba antes de las 9:00 del día del evento que hayan llegado.", "parceiro_faq"),
  ("¿La entrada está garantizada?", "SportsEvents365 ofrece garantía de entrega: si no entrega las entradas confirmadas por causas propias, devuelve hasta el 100% del valor de las entradas. Avisa cualquier problema el mismo día a la línea de emergencia: {tel}.", "como"),
  ("¿Por qué el precio es mayor que el valor impreso?", "SportsEvents365 opera en la reventa (mercado secundario), donde el precio sigue a la demanda. En partidos y conciertos muy buscados, el precio suele superar el valor nominal.", "comprar"),
  ("¿Puedo cancelar? ¿Y si cambia la fecha?", "Un pedido confirmado no se puede cancelar sin aprobación del socio, y puede tener un cargo. Si el evento se aplaza, la entrada suele valer para la nueva fecha; si no puedes ir, el socio intenta el reembolso o la reventa, sin garantía.", "termos"),
  ("¿Nos sentaremos juntos?", "Sí, los asientos van en pares, salvo que el lote diga 'Single seats'. Para grupos de 9 o más, el socio tiene pedidos de grupo.", "comprar"),
 ],
}

# Texto do link que acompanha cada resposta do FAQ. "guia#sN" aponta para a seção N do guia de compra segura.
FAQ_LINK = {
 "pt": {"oficial": "Abrir o canal oficial: {of}", "mapa": "Ver a rota no Google Maps", "golpe": "Guia: sinais de golpe",
        "pagamento": "Guia: preço final, câmbio e IOF", "nominal": "Guia: ingresso nominal e documento",
        "parceiro_faq": "Ler o FAQ da SportsEvents365", "como": "Como funcionam as garantias",
        "comprar": "Ver preços e setores na SportsEvents365", "termos": "Ler os termos da SportsEvents365"},
 "en": {"oficial": "Open the official channel: {of}", "mapa": "Get directions on Google Maps", "golpe": "Guide: scam warning signs",
        "pagamento": "Guide: final price, currency and fees", "nominal": "Guide: named tickets and ID",
        "parceiro_faq": "Read the SportsEvents365 FAQ", "como": "How the guarantees work",
        "comprar": "See prices and sections at SportsEvents365", "termos": "Read the SportsEvents365 terms"},
 "es": {"oficial": "Abrir el canal oficial: {of}", "mapa": "Ver la ruta en Google Maps", "golpe": "Guía: señales de estafa",
        "pagamento": "Guía: precio final, cambio y comisiones", "nominal": "Guía: entradas nominales y documento",
        "parceiro_faq": "Leer el FAQ de SportsEvents365", "como": "Cómo funcionan las garantías",
        "comprar": "Ver precios y sectores en SportsEvents365", "termos": "Leer los términos de SportsEvents365"},
}
# Seção do guia de compra segura (GUIA) para cada link "guia".
FAQ_GUIA_SECAO = {"golpe": 2, "pagamento": 4, "nominal": 3}

# Canal oficial de venda de cada evento (slug sem a data). Só domínios oficiais conhecidos.
OFICIAL = {
 "barcelona-vs-real-madrid": ("FC Barcelona (fcbarcelona.com)", "https://www.fcbarcelona.com/"),
 "barcelona-vs-manchester-city": ("FC Barcelona (fcbarcelona.com)", "https://www.fcbarcelona.com/"),
 "milan-vs-inter": ("AC Milan (acmilan.com)", "https://www.acmilan.com/"),
 "italia-vs-franca": ("FIGC (figc.it)", "https://www.figc.it/"),
 "franca-vs-africa-do-sul": ("Stade de France (stadefrance.com)", "https://www.stadefrance.com/"),
 "gp-abu-dhabi-f1": ("Yas Marina Circuit (yasmarinacircuit.com)", "https://www.yasmarinacircuit.com/"),
 "knicks-vs-nuggets": ("Madison Square Garden (msg.com)", "https://www.msg.com/"),
 "final-australian-open": ("Australian Open (ausopen.com)", "https://ausopen.com/"),
 "celine-dion-paris": ("Celine Dion (celinedion.com)", "https://www.celinedion.com/"),
 "final-champions-league": ("UEFA (uefa.com)", "https://www.uefa.com/"),
}


def chave_evento(slug):
    """'barcelona-vs-real-madrid-2026-10-25' -> 'barcelona-vs-real-madrid'."""
    return re.sub(r"-\d{4}-\d{2}-\d{2}$", "", slug)


# Aviso "Antes de comprar" de cada evento: fatos com fonte que mudam a decisão de compra.
# (texto, rótulo da fonte, url da fonte). "barca" liga ao guia do Barça.
AVISO = {
 "barcelona-vs-real-madrid": {
  "pt": "Os ingressos do Barça são nominais: o clube pede os dados de cada pessoa dias antes e confere o documento na entrada. Em clássicos, a venda oficial é curta e prioriza sócios.",
  "en": "Barça tickets are issued by name: the club asks for each fan's details a few days before and checks ID at the gate. For El Clásico, the official sale is short and favours members.",
  "es": "Las entradas del Barça son nominales: el club pide los datos de cada persona días antes y revisa el documento en el acceso. En el Clásico, la venta oficial es corta y prioriza a los socios.",
  "fonte": ("r/Barca", "https://www.reddit.com/r/Barca/comments/1lgri7m/"), "barca": True},
 "barcelona-vs-manchester-city": {
  "pt": "Os ingressos do Barça são nominais e o documento é conferido na entrada. Na Champions, a regra da UEFA limita a compra de lugares do setor da casa por torcedores do time visitante, e cartão do país do visitante pode dar problema.",
  "en": "Barça tickets are issued by name and ID is checked at the gate. In the Champions League, UEFA rules limit away fans from buying home-section seats, and a card from the away team's country may cause problems.",
  "es": "Las entradas del Barça son nominales y se revisa el documento en el acceso. En la Champions, la norma de la UEFA limita la compra de asientos del sector local por aficionados del equipo visitante, y una tarjeta del país visitante puede dar problemas.",
  "fonte": ("r/Barca", "https://www.reddit.com/r/Barca/comments/1lgri7m/"), "barca": True},
 "final-champions-league": {
  "pt": "A UEFA vende os ingressos da final só pelo UEFA.com e os entrega pelo app da UEFA. Ela avisa que ingresso comprado de terceiros pode ser cancelado e a entrada, negada. Pese esse risco antes de comprar na revenda.",
  "en": "UEFA sells final tickets only on UEFA.com and delivers them in the UEFA app. It warns that tickets bought from third parties can be cancelled and entry refused. Weigh that risk before buying resale.",
  "es": "La UEFA vende las entradas de la final solo en UEFA.com y las entrega en su app. Avisa de que las entradas compradas a terceros pueden anularse y negarse el acceso. Valora ese riesgo antes de comprar en reventa.",
  "fonte": ("The Ticketing Business", "https://www.theticketingbusiness.com/2024/05/uefa-issues-resale-threat-ahead-of-champions-league-final/")},
 "final-australian-open": {
  "pt": "No estado de Victoria, a lei limita a revenda de ingressos de grandes eventos a 10% acima do valor de face, salvo vendedor autorizado. Compare com o preço oficial no ausopen.com antes de comprar.",
  "en": "In Victoria, the law caps resale of major-event tickets at 10% above face value unless the seller is authorised. Compare with the official price on ausopen.com before you buy.",
  "es": "En el estado de Victoria, la ley limita la reventa de entradas de grandes eventos al 10% por encima del valor nominal, salvo vendedor autorizado. Compara con el precio oficial en ausopen.com antes de comprar.",
  "fonte": ("Governo de Victoria", "https://djsir.vic.gov.au/ticket-scalping/about")},
 "celine-dion-paris": {
  "pt": "Os shows da Celine Dion em Paris atraíram muitos golpes com ingresso falso. Não pague por transferência a pessoa física e não compre por print ou foto do ingresso.",
  "en": "Celine Dion's Paris shows have drawn many fake-ticket scams. Do not pay a private person by transfer, and do not buy from a screenshot or photo of a ticket.",
  "es": "Los conciertos de Celine Dion en París han atraído muchas estafas con entradas falsas. No pagues por transferencia a una persona física ni compres a partir de una captura o foto de la entrada.",
  "fonte": ("ABC News", "https://abcnews.com/amp/Entertainment/wireStory/tech-tip-avoid-celine-dion-ticket-scams-makes-136236734")},
}
AVISO_H = {"pt": "Antes de comprar", "en": "Before you buy", "es": "Antes de comprar"}
AVISO_FONTE = {"pt": "Fonte", "en": "Source", "es": "Fuente"}

ROT = {
 "pt": {"entrada_h": "O que levar e o que é barrado", "publico_h": "Melhor setor para cada perfil", "faq_h": "Perguntas frequentes",
        "conferido": "Data e horário conferidos no parceiro em {conf}.", "hora_local": "{h} (horário local)",
        # Palavra de busca primeiro ("Ingressos ..."), como SeatPick, Ticombo e P1 Travel (aprovado em 24/10/2026).
        "titulos": ["Ingressos {t}{ano}: com garantia + guia {art} {loc}", "Ingressos {t}{ano} | {loc}",
                    "Ingressos {t}{ano}", "Ingressos {t}"],
        "desc": "Ingressos (bilhetes) para {t}: {d} às {h}, {loc}. Garantia de entrega do parceiro, como chegar, melhor setor para família ou torcida e o que levar.",
        "f_time": "Horário", "como_h": "Como funciona e garantias", "guia_h": "Comprar ingressos na Europa sem risco"},
 "en": {"entrada_h": "What to bring and what gets refused", "publico_h": "Best section for each fan", "faq_h": "Frequently asked questions",
        "conferido": "Date and time checked with the partner on {conf}.", "hora_local": "{h} (local time)",
        "titulos": ["{t}{ano} tickets: guaranteed delivery + {loc} guide", "{t}{ano} tickets: guaranteed delivery",
                    "{t} tickets: guaranteed delivery", "{t} tickets"],
        "desc": "Tickets for {t}: {d}, {h}, {loc}. Partner delivery guarantee, getting there, best sections for families or loud support, and what to bring.",
        "f_time": "Start", "como_h": "How it works and guarantees", "guia_h": "Buying tickets in Europe safely"},
 "es": {"entrada_h": "Qué llevar y qué no se permite", "publico_h": "Mejor sector para cada perfil", "faq_h": "Preguntas frecuentes",
        "conferido": "Fecha y hora revisadas con el socio el {conf}.", "hora_local": "{h} (hora local)",
        "titulos": ["Entradas {t}{ano}: con garantía + guía {art} {loc}", "Entradas {t}{ano}: garantía de entrega",
                    "Entradas {t}: garantía de entrega", "Entradas {t}"],
        "desc": "Entradas para {t}: {d} a las {h}, {loc}. Garantía de entrega del socio, cómo llegar, mejor sector para familias o animación y qué llevar.",
        "f_time": "Hora", "como_h": "Cómo funciona y garantías", "guia_h": "Comprar entradas en Europa sin riesgo"},
}

# ---------- Página "Como funciona e garantias" (confiança) ----------
COMO_FUNCIONA = {
 "pt": {"path": "como-funciona/", "title": "Como funciona o MyTickets e quais são as garantias",
  "desc": "Quem vende, quem entrega, garantia de entrega, cancelamento, adiamento e contato de emergência. Tudo o que você precisa saber antes de comprar.",
  "h1": "Como funciona e garantias", "lead": "O MyTickets Tours é um guia de eventos com links de afiliado. A venda, o pagamento e a entrega são feitos pela SportsEvents365. Abaixo, o que isso significa para você.",
  "secoes": [
   ("Quem faz o quê", ["O MyTickets escreve os guias (data, local, como chegar, setores) e aponta para a página certa do parceiro. Não vendemos ingressos e não recebemos seu pagamento.",
                      "A SportsEvents365 é operada pela {empresa}, com endereço registrado em {endereco}. É ela que confirma o pedido, cobra e entrega os ingressos.",
                      "Quando você compra por um link nosso, o parceiro nos paga uma comissão. O preço para você é o mesmo."]),
   ("Garantia de entrega", ["Se o parceiro não entregar os ingressos confirmados por falha dele, a responsabilidade dele é devolver até 100% do valor dos ingressos.",
                            "Se o ingresso vier em setor pior que o comprado, o parceiro devolve a diferença. Lugares em par são garantidos, salvo lotes marcados como 'Single seats'.",
                            "Qualquer problema no dia (atraso na entrega, setor errado, dificuldade na entrada) deve ser avisado na hora pela central de emergência do parceiro: {tel}. Os termos dizem que problemas não avisados por esse canal não são cobertos."]),
   ("Preço e revenda", ["A SportsEvents365 atua no mercado de revenda. Em eventos muito procurados o preço costuma ficar acima do valor impresso no ingresso.",
                        "O pedido é confirmado em até 1 dia útil. O valor é bloqueado no cartão e cobrado na confirmação."]),
   ("Cancelamento e adiamento", ["Pedidos confirmados só podem ser cancelados com aprovação do parceiro, e pode haver taxa.",
                                 "Se o evento for adiado, o ingresso costuma valer para a nova data. Se você não puder ir, o parceiro tenta reembolso junto ao fornecedor ou a revenda, sem garantia.",
                                 "Datas de ligas europeias às vezes só são confirmadas semanas antes por causa da TV. Planeje a viagem com folga."]),
   ("Como mantemos as informações em dia", ["Conferimos data e horário de cada evento no catálogo do parceiro e mostramos na página quando foi a última conferência.",
                                            "Eventos que já aconteceram saem do site na atualização seguinte.",
                                            "Encontrou algo errado? Escreva para {email} e corrigimos."]),
  ],
  "links_h": "Documentos do parceiro", "termos": "Termos e condições da SportsEvents365", "faq": "Perguntas frequentes da SportsEvents365"},
 "en": {"path": "en/how-it-works/", "title": "How MyTickets works and what is guaranteed",
  "desc": "Who sells, who delivers, the delivery guarantee, cancellations, postponements and the emergency contact. What to know before you buy.",
  "h1": "How it works and guarantees", "lead": "MyTickets Tours is an event guide with affiliate links. Sale, payment and delivery are handled by SportsEvents365. Here is what that means for you.",
  "secoes": [
   ("Who does what", ["MyTickets writes the guides (date, venue, getting there, sections) and points to the right partner page. We do not sell tickets and never take your payment.",
                      "SportsEvents365 is operated by {empresa}, registered at {endereco}. It confirms the order, charges you and delivers the tickets.",
                      "When you buy through our link, the partner pays us a commission. Your price is the same."]),
   ("Delivery guarantee", ["If the partner fails to deliver confirmed tickets for reasons on its side, its responsibility is to refund up to 100% of the ticket price.",
                           "If you get a worse category than ordered, the partner refunds the difference. Seats in pairs are guaranteed unless a listing says 'Single seats'.",
                           "Report any problem on the day (late delivery, wrong section, trouble at the gate) straight away to the partner's emergency line: {tel}. The terms say problems not reported this way are not covered."]),
   ("Price and resale", ["SportsEvents365 works in the resale market. For high-demand events prices are often above face value.",
                         "Orders are confirmed within 1 business day. The amount is held on your card and charged on confirmation."]),
   ("Cancellations and postponements", ["Confirmed orders can only be cancelled with the partner's approval, and a fee may apply.",
                                        "If the event is postponed, tickets are usually valid for the new date. If you cannot go, the partner will try to get a refund from its supplier or resell them, without a guarantee.",
                                        "European league fixtures are sometimes confirmed only weeks ahead because of TV. Plan your trip with some slack."]),
   ("How we keep information current", ["We check each event's date and time in the partner's catalogue and show on the page when it was last checked.",
                                        "Past events are removed on the next update.",
                                        "Spotted a mistake? Write to {email} and we will fix it."]),
  ],
  "links_h": "Partner documents", "termos": "SportsEvents365 terms and conditions", "faq": "SportsEvents365 FAQ"},
 "es": {"path": "es/como-funciona/", "title": "Cómo funciona MyTickets y qué está garantizado",
  "desc": "Quién vende, quién entrega, garantía de entrega, cancelaciones, aplazamientos y contacto de emergencia. Lo que debes saber antes de comprar.",
  "h1": "Cómo funciona y garantías", "lead": "MyTickets Tours es una guía de eventos con enlaces de afiliado. La venta, el pago y la entrega los hace SportsEvents365. Esto es lo que significa para ti.",
  "secoes": [
   ("Quién hace qué", ["MyTickets escribe las guías (fecha, recinto, cómo llegar, sectores) y enlaza a la página correcta del socio. No vendemos entradas ni recibimos tu pago.",
                       "SportsEvents365 está operada por {empresa}, con domicilio registrado en {endereco}. Es quien confirma el pedido, cobra y entrega las entradas.",
                       "Cuando compras con nuestro enlace, el socio nos paga una comisión. Tu precio es el mismo."]),
   ("Garantía de entrega", ["Si el socio no entrega las entradas confirmadas por causas propias, su responsabilidad es devolver hasta el 100% del valor de las entradas.",
                            "Si recibes una categoría peor que la comprada, el socio devuelve la diferencia. Los asientos en pareja están garantizados, salvo lotes marcados como 'Single seats'.",
                            "Avisa cualquier problema el mismo día (retraso en la entrega, sector equivocado, problema en el acceso) de inmediato a la línea de emergencia del socio: {tel}. Los términos indican que los problemas no avisados por esa vía no están cubiertos."]),
   ("Precio y reventa", ["SportsEvents365 opera en el mercado de reventa. En eventos muy buscados el precio suele superar el valor nominal.",
                         "El pedido se confirma en un plazo de 1 día hábil. El importe se retiene en la tarjeta y se cobra al confirmar."]),
   ("Cancelaciones y aplazamientos", ["Los pedidos confirmados solo se pueden cancelar con aprobación del socio, y puede haber un cargo.",
                                      "Si el evento se aplaza, la entrada suele valer para la nueva fecha. Si no puedes ir, el socio intenta el reembolso con su proveedor o la reventa, sin garantía.",
                                      "Las fechas de las ligas europeas a veces se confirman solo semanas antes por la TV. Planifica el viaje con margen."]),
   ("Cómo mantenemos la información al día", ["Revisamos la fecha y la hora de cada evento en el catálogo del socio y mostramos en la página cuándo fue la última revisión.",
                                              "Los eventos ya celebrados salen del sitio en la siguiente actualización.",
                                              "¿Ves un error? Escribe a {email} y lo corregimos."]),
  ],
  "links_h": "Documentos del socio", "termos": "Términos y condiciones de SportsEvents365", "faq": "Preguntas frecuentes de SportsEvents365"},
}

# ---------- Guia-referência (linkable asset) ----------
GUIA = {
 "pt": {"path": "guias/comprar-ingressos-europa-sem-risco/", "title": "Como comprar ingressos para jogos na Europa sem cair em golpe (guia 2026)",
  "desc": "Guia prático para brasileiros: onde comprar, sinais de golpe, ingresso nominal, câmbio e taxas, datas que mudam por causa da TV, entrega e o que fazer no dia.",
  "h1": "Comprar ingressos na Europa sem risco", "lead": "Um guia prático para quem sai do Brasil para ver futebol, rúgbi, Fórmula 1 ou um show na Europa. Pode citar e linkar à vontade.",
  "secoes": [
   ("1. Onde comprar", ["Bilheteria oficial do clube: é o preço de face, mas a venda geral costuma ir primeiro para sócios e esgota rápido em clássicos e finais.",
                        "Revendedora com garantia por escrito: o preço segue a procura, mas há empresa identificada, termos publicados e um canal de emergência. É o caso da SportsEvents365, nossa parceira.",
                        "Evite grupos de rede social, anúncios de classificados e vendedores sem empresa identificada. Ali não há a quem recorrer se o ingresso não chegar."]),
   ("2. Sinais de golpe", ["Pedido de pagamento por Pix, transferência ou carteira digital para pessoa física.",
                           "Preço muito abaixo do que as revendas conhecidas cobram para o mesmo setor.",
                           "Pressa: 'só hoje', 'último par'. Golpistas usam urgência para impedir que você pesquise.",
                           "Foto ou print do ingresso como 'prova'. O mesmo QR code pode ser vendido para várias pessoas, e só a primeira entra."]),
   ("3. Ingresso nominal e documento", ["Alguns clubes e competições emitem ingressos em nome do comprador. Na revenda, o ingresso pode estar no nome de outra pessoa; o vendedor sério explica antes o que apresentar.",
                                        "Leve passaporte no dia. Os termos da SportsEvents365 preveem que o parceiro pode pedir cópia do passaporte para emitir o pedido."]),
   ("4. Preço final: câmbio, IOF e taxas", ["Compare o preço final, com taxas de serviço e entrega, e não o preço anunciado.",
                                            "No cartão brasileiro, compras em moeda estrangeira pagam IOF, e a conversão do câmbio segue a regra do seu banco. Confira antes de fechar.",
                                            "Cartão brasileiro é recusado com frequência em sites estrangeiros. Avise o banco antes e tenha um segundo cartão, como o de uma conta global em dólar ou euro.",
                                            "Ingresso de revenda para jogo grande custa mais que o valor impresso. Isso é normal no mercado secundário, não é golpe, desde que o vendedor deixe claro."]),
   ("5. A data ainda pode mudar", ["Nas ligas europeias, dia e horário dos jogos costumam ser confirmados poucas semanas antes, por causa da TV.",
                                   "Reserve voo e hotel com uma noite de folga antes e depois, ou com tarifa remarcável.",
                                   "Se o jogo for adiado, o ingresso costuma valer para a nova data, mas o reembolso não é garantido."]),
   ("6. Entrega", ["Os ingressos chegam perto da data: e-ticket, ingresso no celular, entrega no hotel ou ponto de retirada.",
                   "Informe o hotel com pelo menos uma semana de antecedência.",
                   "Se a entrega for no hotel, confirme até a manhã do jogo que o envelope chegou e avise o vendedor na hora se não chegou."]),
   ("7. Setor certo", ["Estádios europeus separam a torcida da casa da visitante. Compre o setor do time que você vai apoiar.",
                       "Vestir a camisa do rival no setor errado pode impedir a entrada ou acabar em expulsão."]),
   ("8. No dia", ["Chegue pelo menos 90 minutos antes em clássicos: a revista é lenta.",
                  "Leve só uma bolsa pequena. Mochilas costumam ser barradas.",
                  "Tenha à mão o passaporte, o ingresso e o telefone de emergência do vendedor."]),
  ],
  "cite_h": "Use este guia no seu site", "cite_p": "Blogs de viagem e de futebol podem linkar este guia livremente. Copie o código abaixo:",
  "eventos_h": "Guias de eventos com essas dicas aplicadas"},
 "en": {"path": "en/guides/buy-tickets-europe-safely/", "title": "How to buy tickets for games in Europe without getting scammed (2026 guide)",
  "desc": "A practical guide for international fans: where to buy, scam warning signs, named tickets, currency and fees, dates that move for TV, delivery and match day.",
  "h1": "Buying tickets in Europe safely", "lead": "A practical guide for fans travelling to see football, rugby, Formula 1 or a concert in Europe. Feel free to cite and link it.",
  "secoes": [
   ("1. Where to buy", ["The club's official box office: face value, but general sale usually goes to members first and sells out fast for derbies and finals.",
                        "A resale company with a written guarantee: prices follow demand, but there is an identified company, published terms and an emergency line. SportsEvents365, our partner, is one.",
                        "Avoid social media groups, classified ads and sellers with no identified company. There is no one to turn to if the ticket never arrives."]),
   ("2. Scam warning signs", ["Being asked to pay by bank transfer or a payment app to a private person.",
                              "A price far below what known resellers charge for the same section.",
                              "Pressure: 'today only', 'last pair'. Scammers use urgency to stop you checking.",
                              "A photo or screenshot of the ticket as 'proof'. The same QR code can be sold to many people, and only the first one gets in."]),
   ("3. Named tickets and ID", ["Some clubs and competitions issue tickets in the buyer's name. On resale, the ticket may carry someone else's name; a serious seller explains in advance what to show.",
                                "Bring your passport on the day. SportsEvents365's terms allow the partner to ask for a passport copy to process the order."]),
   ("4. Final price: currency and fees", ["Compare the final price, with service and delivery fees, not the headline price.",
                                          "Your card may add a foreign transaction fee and use its own exchange rate.",
                                          "Resale tickets for big games cost more than face value. That is normal in the secondary market, not a scam, as long as the seller says so."]),
   ("5. The date can still change", ["In European leagues, match days and kick-off times are often confirmed only a few weeks ahead because of TV.",
                                     "Book flights and hotels with a spare night either side, or with changeable fares.",
                                     "If a match is postponed, tickets are usually valid for the new date, but a refund is not guaranteed."]),
   ("6. Delivery", ["Tickets arrive close to the date: e-ticket, mobile ticket, hotel delivery or pickup point.",
                    "Give your hotel details at least a week ahead.",
                    "For hotel delivery, check by the morning of the match that the envelope has arrived, and tell the seller straight away if not."]),
   ("7. The right section", ["European stadiums separate home and away fans. Buy in the section of the team you support.",
                             "Wearing the rival shirt in the wrong section can get you refused entry or removed."]),
   ("8. On the day", ["Arrive at least 90 minutes early for big games: security is slow.",
                      "Carry only a small bag. Backpacks are often refused.",
                      "Keep your passport, ticket and the seller's emergency number at hand."]),
  ],
  "cite_h": "Use this guide on your site", "cite_p": "Travel and football blogs are welcome to link to this guide. Copy the code below:",
  "eventos_h": "Event guides with these tips applied"},
 "es": {"path": "es/guias/comprar-entradas-europa-sin-riesgo/", "title": "Cómo comprar entradas para partidos en Europa sin caer en estafas (guía 2026)",
  "desc": "Guía práctica para aficionados de viaje: dónde comprar, señales de estafa, entradas nominales, cambio y comisiones, fechas que cambian por la TV, entrega y el día del partido.",
  "h1": "Comprar entradas en Europa sin riesgo", "lead": "Una guía práctica para quien viaja a ver fútbol, rugby, Fórmula 1 o un concierto en Europa. Puedes citarla y enlazarla libremente.",
  "secoes": [
   ("1. Dónde comprar", ["La taquilla oficial del club: precio nominal, pero la venta general suele ir primero a socios y se agota rápido en clásicos y finales.",
                         "Una reventa con garantía por escrito: el precio sigue la demanda, pero hay una empresa identificada, términos publicados y una línea de emergencia. SportsEvents365, nuestro socio, es una de ellas.",
                         "Evita grupos de redes sociales, anuncios clasificados y vendedores sin empresa identificada. No hay a quién reclamar si la entrada no llega."]),
   ("2. Señales de estafa", ["Que te pidan pagar por transferencia o app de pagos a una persona física.",
                             "Un precio muy por debajo de lo que cobran las reventas conocidas por el mismo sector.",
                             "Prisa: 'solo hoy', 'último par'. Los estafadores usan la urgencia para que no compruebes nada.",
                             "Una foto o captura de la entrada como 'prueba'. El mismo código QR puede venderse a muchas personas, y solo entra la primera."]),
   ("3. Entradas nominales y documento", ["Algunos clubes y competiciones emiten entradas a nombre del comprador. En la reventa, la entrada puede llevar el nombre de otra persona; un vendedor serio explica antes qué presentar.",
                                          "Lleva el pasaporte el día del evento. Los términos de SportsEvents365 permiten al socio pedir copia del pasaporte para tramitar el pedido."]),
   ("4. Precio final: cambio y comisiones", ["Compara el precio final, con comisiones de servicio y entrega, no el precio anunciado.",
                                             "Tu tarjeta puede sumar una comisión por compra en moneda extranjera y aplicar su propio tipo de cambio.",
                                             "Las entradas de reventa para partidos grandes cuestan más que su valor nominal. Es normal en el mercado secundario, no es estafa, siempre que el vendedor lo indique."]),
   ("5. La fecha todavía puede cambiar", ["En las ligas europeas, el día y la hora de los partidos suelen confirmarse pocas semanas antes por la TV.",
                                          "Reserva vuelos y hotel con una noche de margen antes y después, o con tarifa modificable.",
                                          "Si el partido se aplaza, la entrada suele valer para la nueva fecha, pero el reembolso no está garantizado."]),
   ("6. Entrega", ["Las entradas llegan cerca de la fecha: e-ticket, entrada en el móvil, entrega en el hotel o punto de recogida.",
                   "Indica tu hotel con al menos una semana de antelación.",
                   "Si la entrega es en el hotel, confirma la mañana del partido que el sobre llegó, y avisa enseguida al vendedor si no llegó."]),
   ("7. El sector correcto", ["Los estadios europeos separan la afición local de la visitante. Compra en el sector del equipo al que vas a apoyar.",
                              "Llevar la camiseta rival en el sector equivocado puede impedirte entrar o acabar en expulsión."]),
   ("8. El día del evento", ["Llega al menos 90 minutos antes en partidos grandes: el control de acceso es lento.",
                             "Lleva solo un bolso pequeño. Las mochilas suelen rechazarse.",
                             "Ten a mano el pasaporte, la entrada y el teléfono de emergencia del vendedor."]),
  ],
  "cite_h": "Usa esta guía en tu web", "cite_p": "Los blogs de viajes y de fútbol pueden enlazar esta guía libremente. Copia el código:",
  "eventos_h": "Guías de eventos con estos consejos aplicados"},
}


# ---------- Parceiros de venda (modelo agregador) ----------
# Cada parceiro aparece no site só com "ativo": True E com um link de afiliado real. Para ligar um parceiro novo
# depois da aprovação no programa (Partnerize, Awin, Tiqets...): preencha "url" com o deeplink do painel,
# troque "ativo" para True e rode o gerador. O botão passa pelo gateway /go/<parceiro>/<idioma>/<evento>/,
# então trocar o link depois exige mudar só esta linha.
#
# Situação em 16/10/2026: Sports Events 365 aprovada. StubHub e viagogo (Partnerize) apenas "elegíveis",
# Awin sem anunciantes aprovados, GetYourGuide e Tiqets sem conta ativa.
PARCEIROS = {
 "se365": {
  "ativo": True, "nome": "Sports Events 365", "tipo": "evento",
  "selo": {"pt": "Garantia de entrega e lugares em par", "en": "Delivery guarantee and seats in pairs",
           "es": "Garantía de entrega y asientos en pareja"},
  "fatos": {
   "pt": ["Revenda com garantia de entrega: se a entrega falhar por culpa do parceiro, ele devolve até 100% do valor dos ingressos.",
          "Lugares em par, salvo lotes marcados como 'Single seats'.",
          "Pedido confirmado em até 1 dia útil; central de emergência no dia do evento."],
   "en": ["Resale with a delivery guarantee: if delivery fails on the partner's side, it refunds up to 100% of the ticket price.",
          "Seats in pairs unless a listing says 'Single seats'.",
          "Order confirmed within 1 business day; emergency line on event day."],
   "es": ["Reventa con garantía de entrega: si la entrega falla por causa del socio, devuelve hasta el 100% del valor de las entradas.",
          "Asientos en pareja, salvo lotes marcados como 'Single seats'.",
          "Pedido confirmado en un plazo de 1 día hábil; línea de emergencia el día del evento."]},
  "termos": "https://sportsevents365.com/terms-and-conditions",
 },
 # Os parceiros abaixo ficam desligados até haver aprovação e link de afiliado.
 "viagogo": {"ativo": False, "nome": "viagogo", "tipo": "evento", "url": "",
  "selo": {"pt": "Marketplace de revenda", "en": "Resale marketplace", "es": "Marketplace de reventa"}, "fatos": {}, "termos": ""},
 "stubhub": {"ativo": False, "nome": "StubHub", "tipo": "evento", "url": "",
  "selo": {"pt": "Marketplace de revenda", "en": "Resale marketplace", "es": "Marketplace de reventa"}, "fatos": {}, "termos": ""},
 "tiqets": {"ativo": False, "nome": "Tiqets", "tipo": "tour", "url": "",
  "selo": {"pt": "Tour do estádio e museu", "en": "Stadium tour and museum", "es": "Tour del estadio y museo"}, "fatos": {}, "termos": ""},
 # P1 Travel (Partnerize): ingresso avulso e pacote ingresso + hotel para futebol europeu, F1, MotoGP, Roland-Garros e shows.
 # Depois da aprovação: ligue "ativo", preencha "termos" e, em data/eventos.json, "links": {"p1travel": "<deeplink do feed>"}.
 "p1travel": {"ativo": False, "nome": "P1 Travel", "tipo": "evento", "url": "https://www.p1travel.com/",
  "selo": {"pt": "Ingresso avulso ou pacote com hotel", "en": "Single ticket or ticket + hotel package", "es": "Entrada suelta o paquete con hotel"},
  "fatos": {}, "termos": ""},
 # SuperIngressos (CJ / Awin / Webgains): vendedor brasileiro para NBA, NFL, MLB, NHL, MLS, shows e Broadway nos EUA.
 "superingressos": {"ativo": False, "nome": "SuperIngressos", "tipo": "evento", "url": "https://www.superingressos.com/",
  "selo": {"pt": "Atendimento em português para eventos nos EUA", "en": "Portuguese-speaking seller for US events", "es": "Atención en portugués para eventos en EE. UU."},
  "fatos": {}, "termos": ""},
}


def parceiros_ativos(tipo=None):
    return [(k, p) for k, p in PARCEIROS.items() if p["ativo"] and (tipo is None or p["tipo"] == tipo)]


def nomes_parceiros():
    return ", ".join(p["nome"] for _, p in parceiros_ativos())


# Textos legais do modelo agregador. {parceiros} = nomes dos parceiros ativos (nunca cite quem não é parceiro).
LEGAL = {
 "pt": {
  "foot": "O MyTickets Tours é um guia independente de ingressos para esporte e shows. Não somos bilheteria oficial, organizador nem administrador dos locais. Os ingressos são vendidos e emitidos pelos parceiros indicados em cada página ({parceiros}), que atuam na revenda; o contrato de compra é feito diretamente com o parceiro escolhido. Os preços são definidos pelos vendedores e podem ficar acima ou abaixo do valor impresso no ingresso. Quando você compra pelos nossos links, podemos receber comissão, sem custo extra para você. Nomes de clubes, ligas e eventos são usados só para identificação; não temos vínculo oficial com eles.",
  "face": "Preços no parceiro podem ser maiores ou menores que o valor impresso no ingresso. Taxas de serviço e entrega podem ser somadas no checkout do parceiro: confira o total antes de pagar.",
  "onde_h": "Onde comprar", "onde_sub": "Compare e escolha. A compra, o pagamento e a entrega acontecem no site do parceiro.",
  "vendedor": "Vendedor", "ver_termos": "Termos do parceiro", "cta": "Ver ingressos na {nome}",
  "pagina_link": "AFILIADOS E AVISO LEGAL",
 },
 "en": {
  "foot": "MyTickets Tours is an independent ticket guide for sports and shows. We are not an official box office, event organizer or venue operator. Tickets are sold and issued by the partners shown on each page ({parceiros}), which operate in resale; the purchase contract is made directly with the partner you choose. Prices are set by sellers and may be above or below the face value printed on the ticket. When you buy through our links we may earn a commission at no extra cost to you. Club, league and event names are used for identification only; we have no official connection with them.",
  "face": "Prices at the partner may be higher or lower than the face value printed on the ticket. Service and delivery fees may be added at the partner's checkout: check the total before you pay.",
  "onde_h": "Where to buy", "onde_sub": "Compare and choose. Purchase, payment and delivery happen on the partner's site.",
  "vendedor": "Seller", "ver_termos": "Partner terms", "cta": "See tickets at {nome}",
  "pagina_link": "AFFILIATES AND LEGAL",
 },
 "es": {
  "foot": "MyTickets Tours es una guía independiente de entradas para deportes y conciertos. No somos taquilla oficial, organizador ni operador de los recintos. Las entradas las venden y emiten los socios indicados en cada página ({parceiros}), que operan en la reventa; el contrato de compra se celebra directamente con el socio elegido. Los precios los fijan los vendedores y pueden estar por encima o por debajo del valor nominal impreso en la entrada. Cuando compras con nuestros enlaces podemos recibir una comisión sin costo extra para ti. Los nombres de clubes, ligas y eventos se usan solo para identificarlos; no tenemos vínculo oficial con ellos.",
  "face": "Los precios en el socio pueden ser mayores o menores que el valor nominal impreso en la entrada. El socio puede sumar cargos de servicio y entrega en su checkout: revisa el total antes de pagar.",
  "onde_h": "Dónde comprar", "onde_sub": "Compara y elige. La compra, el pago y la entrega se hacen en el sitio del socio.",
  "vendedor": "Vendedor", "ver_termos": "Términos del socio", "cta": "Ver entradas en {nome}",
  "pagina_link": "AFILIADOS Y AVISO LEGAL",
 },
}

# Página "Afiliados e aviso legal" (divulgação de afiliados + termos de uso).
DIVULGACAO = {
 "pt": {"path": "afiliados-e-aviso-legal/", "title": "Afiliados e aviso legal | MyTickets Tours",
  "desc": "Como o MyTickets Tours funciona como guia e agregador de ingressos, como ganhamos dinheiro, quem vende, preços acima do valor de face e uso de marcas.",
  "h1": "Afiliados e aviso legal",
  "lead": "O MyTickets Tours é um guia editorial e comparativo de ingressos. Esta página explica o que fazemos, o que não fazemos e quem responde pela sua compra.",
  "secoes": [
   ("O que é o MyTickets", ["Publicamos guias de eventos (data, local, como chegar, setores) e indicamos onde comprar. Não temos estoque de ingressos, não processamos pagamentos e não emitimos ingressos físicos ou digitais.",
                            "Parceiros de venda hoje: {parceiros}. Cada página de evento mostra o nome do vendedor antes do clique."]),
   ("Quem vende e quem responde pela compra", ["O contrato de compra é feito diretamente entre você e o parceiro escolhido. Pagamento, emissão, entrega, troca, cancelamento, reembolso e atendimento depois do checkout seguem os termos desse parceiro.",
                                              "Garantias (entrada válida, lugares juntos, reposição ou reembolso) são dadas exclusivamente pela política do parceiro onde a compra for concluída. Leia os termos no checkout antes de pagar."]),
   ("Preço, valor de face e taxas", ["Os parceiros atuam na revenda. O preço é definido pelo vendedor e pode ficar acima ou abaixo do valor impresso no ingresso.",
                                     "Taxas de serviço, de entrega e impostos podem ser somados no checkout do parceiro. Confira o valor total antes de pagar."]),
   ("Como ganhamos dinheiro", ["O site participa de programas de afiliados. Quando você clica num link de compra e conclui um pedido, o parceiro pode nos pagar uma comissão. O preço para você é o mesmo.",
                               "Os links de compra são marcados como patrocinados (rel=\"sponsored\") e passam por endereços /go/ do nosso domínio, que só redirecionam ao parceiro."]),
   ("Marcas e nomes de eventos", ["Nomes de clubes, ligas, competições, artistas e locais (como UEFA, La Liga, Premier League, FC Barcelona ou Real Madrid) aparecem só para identificar o evento. O MyTickets não tem vínculo oficial, patrocínio ou autorização de clubes, ligas, organizadores ou locais.",
                                  "Revenda de ingressos tem regras próprias em alguns países e competições. Verifique as regras do evento e do país antes de comprar."]),
   ("Correções e contato", ["Conferimos datas e horários no catálogo do parceiro e mostramos na página quando foi a última conferência. Encontrou algo errado? Escreva para {email}."]),
  ]},
 "en": {"path": "en/affiliate-disclosure/", "title": "Affiliate disclosure and legal notice | MyTickets Tours",
  "desc": "How MyTickets Tours works as a ticket guide and aggregator, how we make money, who sells, prices above face value and use of trademarks.",
  "h1": "Affiliate disclosure and legal notice",
  "lead": "MyTickets Tours is an editorial and comparison guide to tickets. This page explains what we do, what we don't do, and who is responsible for your purchase.",
  "secoes": [
   ("What MyTickets is", ["We publish event guides (date, venue, getting there, sections) and show where to buy. We hold no ticket inventory, process no payments and issue no physical or digital tickets.",
                          "Current sales partners: {parceiros}. Each event page names the seller before you click."]),
   ("Who sells and who is responsible", ["The purchase contract is made directly between you and the partner you choose. Payment, issuing, delivery, exchanges, cancellations, refunds and after-checkout support follow that partner's terms.",
                                         "Guarantees (valid entry, seats together, replacement or refund) are given only under the policy of the partner where you complete the purchase. Read the terms at checkout before paying."]),
   ("Price, face value and fees", ["Partners operate in resale. The price is set by the seller and may be above or below the face value printed on the ticket.",
                                   "Service fees, delivery fees and taxes may be added at the partner's checkout. Check the total before you pay."]),
   ("How we make money", ["This site takes part in affiliate programs. If you click a booking link and complete an order, the partner may pay us a commission. Your price is the same.",
                          "Booking links are marked as sponsored (rel=\"sponsored\") and go through /go/ addresses on our domain, which only redirect to the partner."]),
   ("Trademarks and event names", ["Club, league, competition, artist and venue names (such as UEFA, La Liga, the Premier League, FC Barcelona or Real Madrid) are used only to identify the event. MyTickets has no official connection with, sponsorship from or authorization by any club, league, organizer or venue.",
                                   "Ticket resale has its own rules in some countries and competitions. Check the event's and the country's rules before you buy."]),
   ("Corrections and contact", ["We check dates and times in the partner's catalogue and show on the page when they were last checked. Spotted a mistake? Write to {email}."]),
  ]},
 "es": {"path": "es/afiliados-y-aviso-legal/", "title": "Afiliados y aviso legal | MyTickets Tours",
  "desc": "Cómo funciona MyTickets Tours como guía y agregador de entradas, cómo ganamos dinero, quién vende, precios por encima del valor nominal y uso de marcas.",
  "h1": "Afiliados y aviso legal",
  "lead": "MyTickets Tours es una guía editorial y comparativa de entradas. Esta página explica qué hacemos, qué no hacemos y quién responde por tu compra.",
  "secoes": [
   ("Qué es MyTickets", ["Publicamos guías de eventos (fecha, recinto, cómo llegar, sectores) e indicamos dónde comprar. No tenemos stock de entradas, no procesamos pagos y no emitimos entradas físicas ni digitales.",
                         "Socios de venta actuales: {parceiros}. Cada página de evento muestra el nombre del vendedor antes del clic."]),
   ("Quién vende y quién responde por la compra", ["El contrato de compra se celebra directamente entre tú y el socio elegido. Pago, emisión, entrega, cambios, cancelaciones, reembolsos y atención posterior al checkout siguen los términos de ese socio.",
                                                  "Las garantías (acceso válido, asientos juntos, reposición o reembolso) las da exclusivamente la política del socio donde completes la compra. Lee los términos en el checkout antes de pagar."]),
   ("Precio, valor nominal y cargos", ["Los socios operan en la reventa. El precio lo fija el vendedor y puede estar por encima o por debajo del valor nominal impreso en la entrada.",
                                       "El socio puede sumar cargos de servicio, de entrega e impuestos en su checkout. Revisa el total antes de pagar."]),
   ("Cómo ganamos dinero", ["El sitio participa en programas de afiliados. Si haces clic en un enlace de compra y completas un pedido, el socio puede pagarnos una comisión. Tu precio es el mismo.",
                            "Los enlaces de compra están marcados como patrocinados (rel=\"sponsored\") y pasan por direcciones /go/ de nuestro dominio, que solo redirigen al socio."]),
   ("Marcas y nombres de eventos", ["Los nombres de clubes, ligas, competiciones, artistas y recintos (como UEFA, La Liga, Premier League, FC Barcelona o Real Madrid) se usan solo para identificar el evento. MyTickets no tiene vínculo oficial, patrocinio ni autorización de clubes, ligas, organizadores o recintos.",
                                    "La reventa de entradas tiene reglas propias en algunos países y competiciones. Revisa las reglas del evento y del país antes de comprar."]),
   ("Correcciones y contacto", ["Revisamos fechas y horarios en el catálogo del socio y mostramos en la página cuándo fue la última revisión. ¿Ves un error? Escribe a {email}."]),
  ]},
}


# ---------- Guia do Barça (busca "como comprar ingresso jogo do Barcelona") ----------
# Fatos conferidos em 16/10/2026 no guia do r/Barca e no Guia Melhores Destinos (links em "fontes").
GUIA_BARCA_FONTES = [
 ("r/Barca: Visiting Camp Nou Guide 2025", "https://www.reddit.com/r/Barca/comments/1lgri7m/"),
 ("Guia Melhores Destinos: Camp Nou", "https://guia.melhoresdestinos.com.br/camp-nou-estadio-barcelona.html"),
]
GUIA_BARCA = {
 "pt": {"path": "guias/ingresso-barcelona-camp-nou/", "title": "Ingresso do Barcelona no Camp Nou: como comprar com segurança",
  "desc": "Venda oficial, quando os ingressos saem, ingresso nominal, cartão brasileiro recusado, regra da UEFA na Champions e revenda com garantia. Guia para quem sai do Brasil.",
  "h1": "Ingresso do Barça: como comprar com segurança", "lead": "Tudo o que um torcedor que sai do Brasil precisa saber para ver o Barcelona no Camp Nou, do canal oficial à revenda com garantia.",
  "secoes": [
   ("1. Comece pelo canal oficial", ["O Barça vende pelo site oficial (fcbarcelona.com), nas bilheterias do Camp Nou e nas lojas oficiais do clube em Barcelona. É o preço de face e o caminho mais seguro.",
                                    "Os ingressos vão sendo liberados aos poucos, conforme os sócios devolvem os lugares que não vão usar. Escolher a cadeira exata muitas vezes só é possível de 1 a 2 semanas antes do jogo.",
                                    "Em clássicos e jogos grandes de Champions, a venda oficial é curta e esgota rápido. Esperar é arriscado."]),
   ("2. A data só fecha perto do jogo", ["Na La Liga, dia e horário são confirmados de 10 a 15 dias antes; até lá a data é provisória.",
                                         "Na Champions, a data e o horário saem no sorteio. Reserve voo e hotel com uma noite de folga, ou com tarifa remarcável."]),
   ("3. O ingresso é nominal", ["Os ingressos do Barça são nominais e os lugares, marcados. Dias antes do jogo, o clube pede por e-mail os dados de cada pessoa.",
                                "O documento é conferido na entrada: leve o passaporte. O ingresso no celular é aceito, mas o clube recomenda imprimir."]),
   ("4. Cartão brasileiro e pagamento", ["Cartão brasileiro é recusado com frequência no site do clube. Avise o banco antes e tenha um segundo cartão, como o de uma conta global em euro ou dólar.",
                                         "A compra sai em euro, com IOF cobrado pelo banco. Compare o preço final, com todas as taxas."]),
   ("5. Champions: a regra da UEFA", ["A UEFA limita a compra de lugares do setor da casa por torcedores do time visitante. Pagar com cartão do país do visitante pode bloquear a compra.",
                                      "O setor visitante é vendido pelo clube visitante, para os sócios dele."]),
   ("6. Quando a venda oficial acaba: revenda com garantia", ["Revendedoras têm lugares depois que a venda oficial esgota, com preço que segue a procura e costuma passar do valor de face.",
                                                              "Compre só de empresa identificada, com termos publicados, garantia de entrega e central de emergência. É o caso da SportsEvents365, nossa parceira ({empresa}).",
                                                              "Na revenda, o ingresso pode estar no nome de outra pessoa. O vendedor sério explica antes o que apresentar na entrada."]),
   ("7. No dia do jogo", ["Metrô L3 (Palau Reial ou Les Corts) ou L5 (Collblanc ou Badal). Compre a volta antes do jogo para fugir da fila.",
                          "Os portões abrem cerca de 1h30 antes. Em clássicos, chegue com 2 horas de folga: a revista é lenta.",
                          "Leve bolsa pequena. Garrafas com tampa e bebida alcoólica são barradas."]),
  ],
  "eventos_h": "Próximos jogos do Barça", "fontes_h": "Fontes", "guia_geral": "Guia completo: comprar ingressos na Europa sem risco"},
 "en": {"path": "en/guides/barcelona-tickets-camp-nou/", "title": "FC Barcelona tickets at Camp Nou: how to buy safely as a tourist",
  "desc": "Official sale, when tickets are released, named tickets and ID, card problems, UEFA's Champions League rule and resale with a guarantee. A guide for visiting fans.",
  "h1": "Barcelona tickets: how to buy safely as a tourist", "lead": "What a visiting fan needs to know to see Barça at Camp Nou, from the official sale to resale with a guarantee.",
  "secoes": [
   ("1. Start with the official sale", ["Barça sells through its official site (fcbarcelona.com), the Camp Nou ticket offices and the club's official stores in Barcelona. That is face value and the safest route.",
                                       "Tickets are released gradually as members give back seats they will not use. Picking an exact seat is often only possible 1 to 2 weeks before the game.",
                                       "For El Clásico and big Champions League nights, the official sale is short and sells out fast. Waiting is risky."]),
   ("2. The date is set late", ["In La Liga, match day and kick-off are confirmed 10 to 15 days ahead; until then the date is provisional.",
                                "In the Champions League, date and time come with the draw. Book flights and hotels with a spare night, or with changeable fares."]),
   ("3. Tickets are issued by name", ["Barça tickets are named and seats are allocated. A few days before the game, the club emails asking for each fan's details.",
                                      "ID is checked at the gate: bring your passport. Mobile tickets are accepted, but the club advises printing them."]),
   ("4. Cards and payment", ["Foreign cards are sometimes declined on the club's site. Tell your bank before you buy and keep a second card handy.",
                             "You pay in euros, and your card may add a foreign transaction fee. Compare the final price with all fees."]),
   ("5. Champions League: UEFA's rule", ["UEFA limits away fans from buying home-section seats. Paying with a card from the away team's country can block the purchase, which matters for English fans at Barça vs Manchester City.",
                                         "The away section is sold by the visiting club to its own members."]),
   ("6. When the official sale is over: resale with a guarantee", ["Resale marketplaces have seats after the official sale sells out, at prices that follow demand and often exceed face value.",
                                                                   "Buy only from an identified company with published terms, a delivery guarantee and an emergency line. SportsEvents365, our partner ({empresa}), is one.",
                                                                   "On resale, the ticket may carry someone else's name. A serious seller explains in advance what to show at the gate."]),
   ("7. On match day", ["Metro L3 (Palau Reial or Les Corts) or L5 (Collblanc or Badal). Buy your return ticket before the game to skip the queue.",
                        "Gates open about 1h30 before kick-off. For El Clásico, allow 2 hours: security is slow.",
                        "Carry a small bag. Bottles with caps and alcohol are refused."]),
  ],
  "eventos_h": "Upcoming Barça games", "fontes_h": "Sources", "guia_geral": "Full guide: buying tickets in Europe safely"},
 "es": {"path": "es/guias/entradas-barcelona-camp-nou/", "title": "Entradas del Barça en el Camp Nou: cómo comprar con seguridad",
  "desc": "Venta oficial, cuándo salen las entradas, entradas nominales, tarjetas rechazadas, la norma de la UEFA en Champions y reventa con garantía. Guía para quien viaja.",
  "h1": "Entradas del Barça: cómo comprar con seguridad", "lead": "Lo que necesita saber un aficionado que viaja para ver al Barça en el Camp Nou, desde la venta oficial hasta la reventa con garantía.",
  "secoes": [
   ("1. Empieza por la venta oficial", ["El Barça vende en su web oficial (fcbarcelona.com), en las taquillas del Camp Nou y en las tiendas oficiales del club en Barcelona. Es el precio nominal y la vía más segura.",
                                        "Las entradas salen poco a poco, a medida que los socios liberan los asientos que no usarán. Elegir el asiento exacto a menudo solo es posible de 1 a 2 semanas antes.",
                                        "En el Clásico y en las grandes noches de Champions, la venta oficial es corta y se agota rápido. Esperar es arriesgado."]),
   ("2. La fecha se fija tarde", ["En La Liga, el día y la hora se confirman de 10 a 15 días antes; hasta entonces la fecha es provisional.",
                                  "En la Champions, la fecha y la hora salen con el sorteo. Reserva vuelo y hotel con una noche de margen, o con tarifa modificable."]),
   ("3. La entrada es nominal", ["Las entradas del Barça son nominales y con asiento asignado. Días antes del partido, el club pide por correo los datos de cada persona.",
                                 "El documento se revisa en el acceso: lleva el pasaporte. La entrada en el móvil se acepta, pero el club recomienda imprimirla."]),
   ("4. Tarjeta y pago", ["Las tarjetas extranjeras a veces se rechazan en la web del club. Avisa a tu banco antes y ten una segunda tarjeta a mano.",
                          "Pagas en euros, y tu tarjeta puede sumar una comisión por compra internacional. Compara el precio final con todas las comisiones."]),
   ("5. Champions: la norma de la UEFA", ["La UEFA limita la compra de asientos del sector local por aficionados del equipo visitante. Pagar con una tarjeta del país visitante puede bloquear la compra.",
                                          "El sector visitante lo vende el club visitante a sus propios socios."]),
   ("6. Cuando se acaba la venta oficial: reventa con garantía", ["Las reventas tienen asientos cuando la venta oficial se agota, con precios que siguen la demanda y suelen superar el valor nominal.",
                                                                  "Compra solo a una empresa identificada, con términos publicados, garantía de entrega y línea de emergencia. SportsEvents365, nuestro socio ({empresa}), es una.",
                                                                  "En la reventa, la entrada puede ir a nombre de otra persona. Un vendedor serio explica antes qué presentar en el acceso."]),
   ("7. El día del partido", ["Metro L3 (Palau Reial o Les Corts) o L5 (Collblanc o Badal). Compra la vuelta antes del partido para evitar la cola.",
                              "Las puertas abren 1h30 antes. En el Clásico, llega con 2 horas de margen: el control es lento.",
                              "Lleva un bolso pequeño. Se rechazan botellas con tapón y alcohol."]),
  ],
  "eventos_h": "Próximos partidos del Barça", "fontes_h": "Fuentes", "guia_geral": "Guía completa: comprar entradas en Europa sin riesgo"},
}


# Organizador de cada evento (dados estruturados "organizer"): quem promove o jogo ou o show.
# Jogos de clube: o mandante. Seleções: a federação da casa. Final da Champions: a UEFA.
ORGANIZADOR = {
 "barcelona-vs-real-madrid": ("SportsOrganization", "FC Barcelona", "https://www.fcbarcelona.com/"),
 "barcelona-vs-manchester-city": ("SportsOrganization", "FC Barcelona", "https://www.fcbarcelona.com/"),
 "milan-vs-inter": ("SportsOrganization", "AC Milan", "https://www.acmilan.com/"),
 "italia-vs-franca": ("SportsOrganization", "Federazione Italiana Giuoco Calcio (FIGC)", "https://www.figc.it/"),
 "franca-vs-africa-do-sul": ("SportsOrganization", "Fédération Française de Rugby", "https://www.ffr.fr/"),
 "gp-abu-dhabi-f1": ("SportsOrganization", "Formula 1", "https://www.formula1.com/"),
 "knicks-vs-nuggets": ("SportsOrganization", "New York Knicks", "https://www.nba.com/knicks"),
 "final-australian-open": ("SportsOrganization", "Tennis Australia", "https://ausopen.com/"),
 "celine-dion-paris": ("Person", "Celine Dion", "https://www.celinedion.com/"),
 "final-champions-league": ("SportsOrganization", "UEFA", "https://www.uefa.com/"),
}

# Participantes já definidos de eventos sem "times" (dados estruturados "performer").
# Finais com finalistas ainda indefinidos (Australian Open, Champions) ficam sem: preencha quando sair o confronto.
PARTICIPANTES = {
 "gp-abu-dhabi-f1": ["McLaren", "Ferrari", "Mercedes", "Red Bull Racing", "Aston Martin", "Alpine", "Williams",
                     "Racing Bulls", "Haas", "Audi", "Cadillac"],
}


# ---------- Camada de viagem: "Planeje a viagem" na página de cada evento ----------
# Cada parceiro mostra um link útil mesmo sem comissão (busca na cidade, nas datas do evento). Quando o campo "id"
# for preenchido (Booking: aid; Omio e GetYourGuide: marker/partner_id, que vêm do painel do Travelpayouts ou do
# programa direto), o link vira link de afiliado, passa pelo /go/ do site e ganha rel="sponsored".
VIAGEM = {
 "booking": {"nome": "Booking.com", "id": "", "param": "aid",
  "h": {"pt": "Hospedagem perto {art} {loc}", "en": "Hotels near {loc}", "es": "Alojamiento cerca {art} {loc}"},
  "p": {"pt": "Busca em {cidade} já com as datas do evento (véspera e dia seguinte). Cancelamento grátis na maioria dos hotéis até perto da data.",
        "en": "Search in {cidade} with the event dates filled in (the night before and the night after). Most hotels allow free cancellation until close to the date.",
        "es": "Búsqueda en {cidade} con las fechas del evento (víspera y día siguiente). La mayoría de los hoteles permite cancelar gratis hasta cerca de la fecha."},
  "cta": {"pt": "Ver hotéis em {cidade}", "en": "See hotels in {cidade}", "es": "Ver hoteles en {cidade}"}},
 "omio": {"nome": "Omio", "id": "", "param": "marker",
  "h": {"pt": "Como chegar a {cidade}", "en": "Getting to {cidade}", "es": "Cómo llegar a {cidade}"},
  "p": {"pt": "Trens, ônibus e voos dentro da Europa num só lugar, com bilhete no celular. Compare antes de fechar o voo internacional.",
        "en": "Trains, buses and flights within Europe in one place, with mobile tickets. Compare before you lock in the long-haul flight.",
        "es": "Trenes, autobuses y vuelos dentro de Europa en un solo lugar, con billete en el móvil. Compara antes de cerrar el vuelo internacional."},
  "cta": {"pt": "Comparar trens, ônibus e voos", "en": "Compare trains, buses and flights", "es": "Comparar trenes, autobuses y vuelos"}},
 "getyourguide": {"nome": "GetYourGuide", "id": "ROXVLTV", "param": "partner_id",
  "h": {"pt": "Tour {art} {loc} e passeios em {cidade}", "en": "{loc} tour and things to do in {cidade}", "es": "Tour {art} {loc} y planes en {cidade}"},
  "p": {"pt": "Visita ao estádio e museu na véspera do jogo, e o que fazer na cidade nos outros dias. Cancelamento grátis até 24 h antes na maioria das atividades.",
        "en": "Stadium and museum tour the day before the game, plus things to do in the city on the other days. Most activities can be cancelled free up to 24 h before.",
        "es": "Visita al estadio y al museo la víspera del partido, y qué hacer en la ciudad los demás días. La mayoría de las actividades se cancela gratis hasta 24 h antes."},
  "cta": {"pt": "Ver tours e passeios", "en": "See tours and activities", "es": "Ver tours y actividades"}},
}

VIAGEM_TXT = {
 "pt": {"k": "Planeje a viagem", "h": "Do aeroporto à arquibancada", "sub": "O ingresso é só uma parte. Hotel perto do estádio, como se deslocar e o que fazer nos outros dias, já nas datas de {t}.",
        "disc": "Links de parceiros de viagem: se você reservar por eles, podemos receber comissão, sem custo extra. Preços e condições são dos parceiros.",
        "sem_aff": "Links externos, sem comissão para o site por enquanto."},
 "en": {"k": "Plan the trip", "h": "From the airport to the stands", "sub": "The ticket is only part of it. A hotel near the stadium, how to get around and things to do on the other days, already on the dates of {t}.",
        "disc": "Travel partner links: if you book through them we may earn a commission at no extra cost to you. Prices and terms are the partners'.",
        "sem_aff": "External links; the site earns no commission on them for now."},
 "es": {"k": "Planifica el viaje", "h": "Del aeropuerto a la grada", "sub": "La entrada es solo una parte. Hotel cerca del estadio, cómo moverte y qué hacer los demás días, ya en las fechas de {t}.",
        "disc": "Enlaces de socios de viaje: si reservas con ellos podemos recibir una comisión, sin costo extra. Precios y condiciones son de los socios.",
        "sem_aff": "Enlaces externos; el sitio no recibe comisión por ellos por ahora."},
}

# ---------- Vídeos do YouTube (data/videos.json) ----------
VIDEOS_TXT = {
 "pt": {"path": "videos/", "title": "Vídeos: jogos, shows e viagens | MyTickets Tours", "h1": "Vídeos",
        "desc": "Vídeos curtos sobre jogos, shows e viagens, cada um com o link para ver ingressos ou reservar o que aparece no vídeo.",
        "k": "Em vídeo", "h": "Veja antes de ir", "sub": "Cada vídeo leva ao guia do evento e ao link para ver ingressos ou reservar o que aparece nele.",
        "todos": "Todos os vídeos", "ver_guia": "Ver guia do evento", "ingressos": "Ver ingressos", "reservar": "Reservar", "assistir": "Assistir ao vídeo",
        "play": "Reproduzir", "som": "Toque para ouvir", "canal": "Canal no YouTube", "vazio": "Os primeiros vídeos estão sendo preparados. Inscreva-se no canal para receber.",
        "ev_h": "Em vídeo", "disc": "O vídeo carrega do YouTube só quando você aperta o play (modo sem cookies).", "idioma": {"pt": "PT", "en": "EN", "es": "ES"}},
 "en": {"path": "en/videos/", "title": "Videos: games, concerts and trips | MyTickets Tours", "h1": "Videos",
        "desc": "Short videos about games, concerts and trips, each with the link to see tickets or book what appears in the video.",
        "k": "On video", "h": "Watch before you go", "sub": "Every video leads to the event guide and to the link to see tickets or book what appears in it.",
        "todos": "All videos", "ver_guia": "See event guide", "ingressos": "See tickets", "reservar": "Book", "assistir": "Watch the video",
        "play": "Play", "som": "Tap for sound", "canal": "YouTube channel", "vazio": "The first videos are being prepared. Subscribe to the channel to get them.",
        "ev_h": "On video", "disc": "The video loads from YouTube only when you press play (no-cookie mode).", "idioma": {"pt": "PT", "en": "EN", "es": "ES"}},
 "es": {"path": "es/videos/", "title": "Videos: partidos, conciertos y viajes | MyTickets Tours", "h1": "Videos",
        "desc": "Videos cortos sobre partidos, conciertos y viajes, cada uno con el enlace para ver entradas o reservar lo que aparece en el video.",
        "k": "En video", "h": "Míralo antes de ir", "sub": "Cada video lleva a la guía del evento y al enlace para ver entradas o reservar lo que aparece en él.",
        "todos": "Todos los videos", "ver_guia": "Ver guía del evento", "ingressos": "Ver entradas", "reservar": "Reservar", "assistir": "Ver el video",
        "play": "Reproducir", "som": "Toca para oír", "canal": "Canal de YouTube", "vazio": "Los primeros videos están en preparación. Suscríbete al canal para recibirlos.",
        "ev_h": "En video", "disc": "El video se carga desde YouTube solo cuando pulsas play (modo sin cookies).", "idioma": {"pt": "PT", "en": "EN", "es": "ES"}},
}


# ---------- Cartões de próximo evento nos vãos da home ----------
PROMO_TXT = {
 "pt": {"k": "Próximo jogo", "k_show": "Próximo show", "ingressos": "Ver ingressos", "guia": "Ver guia",
        "tours": "Passeios em {cidade}", "plan_k": "Planeje a viagem",
        "plan_h": "Quem vai ao jogo também precisa dormir, chegar e passear",
        "plan_sub": "As datas de {t} já entram na busca.", "hotel": "Hotel em {cidade}", "transporte": "Como chegar"},
 "en": {"k": "Next match", "k_show": "Next concert", "ingressos": "See tickets", "guia": "See guide",
        "tours": "Things to do in {cidade}", "plan_k": "Plan the trip",
        "plan_h": "Whoever goes to the game also has to sleep, arrive and explore",
        "plan_sub": "The dates of {t} are already in the search.", "hotel": "Hotel in {cidade}", "transporte": "Getting there"},
 "es": {"k": "Próximo partido", "k_show": "Próximo concierto", "ingressos": "Ver entradas", "guia": "Ver guía",
        "tours": "Planes en {cidade}", "plan_k": "Planifica el viaje",
        "plan_h": "Quien va al partido también necesita dormir, llegar y pasear",
        "plan_sub": "Las fechas de {t} ya entran en la búsqueda.", "hotel": "Hotel en {cidade}", "transporte": "Cómo llegar"},
}


# ---------- Faixa AO VIVO (scripts/aovivo.py escreve data/aovivo.json; a faixa só existe em português) ----------
AOVIVO_TXT = {
 "pt": {"k": "Ao vivo agora", "h": "Assista enquanto a bola rola",
        "sub": "Transmissão aberta do canal que tem os direitos, no player do YouTube. Carrega só quando você aperta o play.",
        "play": "Assistir ao vivo", "ingressos": "Ver ingressos", "guia": "Ver guia do evento",
        "regiao": "Transmissão liberada para o Brasil pelo canal detentor dos direitos.",
        "contador": "· {n} ao mesmo tempo"},
}


# ---------- Monitor de venda (scripts/vendas.py): página oficial de ingressos de cada evento ----------
# chave_evento(slug) -> (nome do canal oficial, URL da página de ingressos, palavras que identificam o evento nessa página).
# O robô lê a página, procura trechos perto dessas palavras e classifica: a_venda, em_breve, esgotado ou desconhecido.
VENDA_OFICIAL = {
 "barcelona-vs-real-madrid": ("FC Barcelona", "https://www.fcbarcelona.com/en/tickets/football/first-team", ["real madrid", "clásico", "clasico"]),
 "barcelona-vs-manchester-city": ("FC Barcelona", "https://www.fcbarcelona.com/en/tickets/football/first-team", ["manchester city", "man city"]),
 "milan-vs-inter": ("AC Milan", "https://www.acmilan.com/en/tickets/serie-a", ["inter", "derby"]),
 "italia-vs-franca": ("FIGC", "https://www.figc.it/en/national-teams/tickets/", ["france", "francia"]),
 "franca-vs-africa-do-sul": ("FFR", "https://billetterie.ffr.fr/", ["afrique du sud", "south africa", "springboks"]),
 "gp-abu-dhabi-f1": ("Yas Marina Circuit", "https://www.yasmarinacircuit.com/en/formula-1", ["grand prix", "f1", "formula 1"]),
 "knicks-vs-nuggets": ("New York Knicks", "https://www.nba.com/knicks/tickets", ["nuggets", "single game", "single-game"]),
 "final-australian-open": ("Australian Open", "https://ausopen.com/tickets", ["final", "2027"]),
 "celine-dion-paris": ("Celine Dion", "https://www.celinedion.com/tour/", ["paris", "la défense", "defense"]),
 "final-champions-league": ("UEFA", "https://www.uefa.com/uefachampionsleague/tickets/", ["final", "2027"]),
}

VENDA_TXT = {
 "pt": {"f": "Venda", "oficial": "Canal oficial", "parceiro": "Parceiro", "a_venda": "à venda", "em_breve": "em breve", "esgotado": "esgotado",
        "desconhecido": "sem informação", "parceiro_lotes": "{n} lotes a partir de {p}", "conferido": "conferido {d}",
        "aviso": "Status lido automaticamente nas páginas oficiais e do parceiro; confirme no site antes de comprar."},
 "en": {"f": "Sales", "oficial": "Official channel", "parceiro": "Partner", "a_venda": "on sale", "em_breve": "coming soon", "esgotado": "sold out",
        "desconhecido": "no information", "parceiro_lotes": "{n} listings from {p}", "conferido": "checked {d}",
        "aviso": "Status read automatically from the official and partner pages; confirm on the site before you buy."},
 "es": {"f": "Venta", "oficial": "Canal oficial", "parceiro": "Socio", "a_venda": "a la venta", "em_breve": "próximamente", "esgotado": "agotado",
        "desconhecido": "sin información", "parceiro_lotes": "{n} lotes desde {p}", "conferido": "revisado {d}",
        "aviso": "Estado leído automáticamente en las páginas oficiales y del socio; confírmalo en el sitio antes de comprar."},
}

# ---------- Alertas de golpe: artigos (data/artigos.json) e formulário de denúncia ----------
ARTIGOS_TXT = {
 "pt": {"path": "alertas-de-golpe/", "title": "Alertas de golpe com ingressos | MyTickets Tours", "h1": "Alertas de golpe",
        "desc": "Como reconhecer sites falsos de ingressos, golpes comuns em jogos e shows, e um canal para denunciar páginas suspeitas.",
        "k": "Segurança", "h": "Antes de pagar, leia isto", "sub": "Relatos apurados, sinais de alerta e um canal para denunciar páginas suspeitas. Não publicamos acusações sem evidência.",
        "ler": "Ler", "publicado": "Publicado em", "atualizado": "atualizado em", "autor": "Por", "eventos_h": "Eventos citados",
        "den_k": "Denuncie", "den_h": "Viu uma página suspeita?", "den_sub": "Mande o endereço e o que aconteceu. Apuramos antes de publicar; nada vai ao ar automaticamente.",
        "den_url": "Endereço da página suspeita", "den_evento": "Evento (opcional)", "den_relato": "O que aconteceu", "den_email": "Seu e-mail (opcional, para retorno)",
        "den_enviar": "Enviar denúncia", "den_ok": "Recebido. Obrigado: vamos apurar.", "den_err": "Preencha o endereço e o relato.", "den_fail": "Não deu para enviar agora. Tente de novo em alguns minutos.",
        "den_priv": "Usamos o relato só para apurar e, se publicarmos, sem o seu nome. Sem spam.", "ugc": "Relatos de leitores são moderados e publicados sem identificação.",
        "todos": "Todos os alertas", "voltar": "Todos os alertas de golpe"},
 "en": {"path": "en/scam-alerts/", "title": "Ticket scam alerts | MyTickets Tours", "h1": "Scam alerts",
        "desc": "How to spot fake ticket sites, common scams around games and concerts, and a channel to report suspicious pages.",
        "k": "Safety", "h": "Read this before you pay", "sub": "Verified reports, warning signs and a channel to report suspicious pages. We publish no accusation without evidence.",
        "ler": "Read", "publicado": "Published", "atualizado": "updated", "autor": "By", "eventos_h": "Events mentioned",
        "den_k": "Report", "den_h": "Seen a suspicious page?", "den_sub": "Send the address and what happened. We check before publishing; nothing goes live automatically.",
        "den_url": "Address of the suspicious page", "den_evento": "Event (optional)", "den_relato": "What happened", "den_email": "Your email (optional, for a reply)",
        "den_enviar": "Send report", "den_ok": "Received. Thank you: we will look into it.", "den_err": "Fill in the address and what happened.", "den_fail": "We couldn't send it right now. Try again in a few minutes.",
        "den_priv": "We use the report only to investigate and, if published, without your name. No spam.", "ugc": "Reader reports are moderated and published without identification.",
        "todos": "All alerts", "voltar": "All scam alerts"},
 "es": {"path": "es/alertas-de-estafas/", "title": "Alertas de estafas con entradas | MyTickets Tours", "h1": "Alertas de estafas",
        "desc": "Cómo reconocer sitios falsos de entradas, estafas comunes en partidos y conciertos, y un canal para denunciar páginas sospechosas.",
        "k": "Seguridad", "h": "Antes de pagar, lee esto", "sub": "Relatos verificados, señales de alerta y un canal para denunciar páginas sospechosas. No publicamos acusaciones sin pruebas.",
        "ler": "Leer", "publicado": "Publicado el", "atualizado": "actualizado el", "autor": "Por", "eventos_h": "Eventos citados",
        "den_k": "Denuncia", "den_h": "¿Viste una página sospechosa?", "den_sub": "Envía la dirección y qué pasó. Verificamos antes de publicar; nada se publica automáticamente.",
        "den_url": "Dirección de la página sospechosa", "den_evento": "Evento (opcional)", "den_relato": "Qué pasó", "den_email": "Tu correo (opcional, para responderte)",
        "den_enviar": "Enviar denuncia", "den_ok": "Recibido. Gracias: lo vamos a verificar.", "den_err": "Completa la dirección y el relato.", "den_fail": "No se pudo enviar ahora. Inténtalo de nuevo en unos minutos.",
        "den_priv": "Usamos el relato solo para verificar y, si lo publicamos, sin tu nombre. Sin spam.", "ugc": "Los relatos de lectores se moderan y se publican sin identificación.",
        "todos": "Todas las alertas", "voltar": "Todas las alertas de estafas"},
}
