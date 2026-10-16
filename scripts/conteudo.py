"""Textos editoriais do MyTickets Tours (PT, EN, ES), usados por gerar_paginas.py.

Regras para editar:
- Fatos sobre entrega, garantia, cancelamento e contato vêm dos Termos e do FAQ da
  SportsEvents365 (https://sportsevents365.com/terms-and-conditions), conferidos em 15/10/2026.
  Se os termos do parceiro mudarem, atualize PARCEIRO e os textos que citam essas regras.
- Regras de estádio que variam por jogo (tamanho de bolsa, documento) ficam em termos gerais
  e mandam o leitor conferir o e-mail do parceiro. Não escreva regra específica sem fonte.
"""

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
FAQ = {
 "pt": [
  ("Que horas começa {t}?", "{d}, às {h} no horário local de {c}, segundo o catálogo do parceiro conferido em {conf}. O organizador ainda pode mudar o horário."),
  ("O ingresso é digital?", "Depende do lote. A SportsEvents365 entrega por e-ticket, ingresso no celular, entrega no hotel ou ponto de retirada, e mostra a forma de entrega antes do pagamento. O parceiro pode trocar a forma de entrega se precisar, avisando antes."),
  ("Como funciona a entrega e quando recebo?", "O pedido é confirmado em até 1 dia útil. Os ingressos chegam perto da data, como é comum na revenda. Informe o hotel até uma semana antes do evento. Se a entrega for no hotel, confira até as 9h do dia do evento se os ingressos chegaram."),
  ("O ingresso é garantido?", "A SportsEvents365 oferece garantia de entrega: se não entregar os ingressos confirmados por falha dela, devolve até 100% do valor dos ingressos. Qualquer problema no dia deve ser avisado na hora pela central de emergência: {tel}."),
  ("Por que o preço é maior que o valor impresso no ingresso?", "A SportsEvents365 atua na revenda (mercado secundário), onde o preço segue a procura. Em jogos e shows muito disputados, o preço costuma passar do valor de face."),
  ("Posso cancelar? E se o evento mudar de data?", "O pedido confirmado não pode ser cancelado sem aprovação do parceiro, e o cancelamento pode ter taxa. Se o evento for adiado, o ingresso costuma valer para a nova data; se você não puder ir, o parceiro tenta reembolso ou revenda, sem garantia."),
  ("Vamos sentar juntos?", "Sim, os lugares saem em pares, a menos que o lote diga 'Single seats'. Para grupos de 9 ou mais, o parceiro tem um pedido de grupo."),
 ],
 "en": [
  ("What time does {t} start?", "{d}, at {h} local time in {c}, according to the partner's catalogue checked on {conf}. The organizer can still change the time."),
  ("Is the ticket digital?", "It depends on the listing. SportsEvents365 delivers by e-ticket, mobile ticket, hotel delivery or pickup point, and shows the delivery method before you pay. The partner may change the method if needed, with notice."),
  ("How does delivery work and when do I get the tickets?", "The order is confirmed within 1 business day. Tickets arrive close to the date, as is usual for resale. Give your hotel details at least a week before the event. For hotel delivery, check by 9 am on the day that the tickets have arrived."),
  ("Are the tickets guaranteed?", "SportsEvents365 offers a delivery guarantee: if it fails to deliver confirmed tickets for reasons on its side, it refunds up to 100% of the ticket price. Report any problem on the day straight away to the emergency line: {tel}."),
  ("Why is the price above face value?", "SportsEvents365 works in the resale (secondary) market, where prices follow demand. For high-demand games and shows, prices are often above face value."),
  ("Can I cancel? What if the date changes?", "A confirmed order cannot be cancelled without the partner's approval, and a fee may apply. If the event is postponed, tickets are usually valid for the new date; if you cannot attend, the partner will try to get a refund or resell them, without a guarantee."),
  ("Will we sit together?", "Yes, seats come in pairs unless the listing says 'Single seats'. For groups of 9 or more, the partner offers group orders."),
 ],
 "es": [
  ("¿A qué hora empieza {t}?", "{d}, a las {h} hora local de {c}, según el catálogo del socio revisado el {conf}. El organizador todavía puede cambiar el horario."),
  ("¿La entrada es digital?", "Depende del lote. SportsEvents365 entrega por e-ticket, entrada en el móvil, entrega en el hotel o punto de recogida, y muestra la forma de entrega antes del pago. El socio puede cambiar la forma de entrega si hace falta, avisando antes."),
  ("¿Cómo funciona la entrega y cuándo la recibo?", "El pedido se confirma en un plazo de 1 día hábil. Las entradas llegan cerca de la fecha, como es habitual en la reventa. Indica tu hotel al menos una semana antes del evento. Si la entrega es en el hotel, comprueba antes de las 9:00 del día del evento que hayan llegado."),
  ("¿La entrada está garantizada?", "SportsEvents365 ofrece garantía de entrega: si no entrega las entradas confirmadas por causas propias, devuelve hasta el 100% del valor de las entradas. Avisa cualquier problema el mismo día a la línea de emergencia: {tel}."),
  ("¿Por qué el precio es mayor que el valor impreso?", "SportsEvents365 opera en la reventa (mercado secundario), donde el precio sigue a la demanda. En partidos y conciertos muy buscados, el precio suele superar el valor nominal."),
  ("¿Puedo cancelar? ¿Y si cambia la fecha?", "Un pedido confirmado no se puede cancelar sin aprobación del socio, y puede tener un cargo. Si el evento se aplaza, la entrada suele valer para la nueva fecha; si no puedes ir, el socio intenta el reembolso o la reventa, sin garantía."),
  ("¿Nos sentaremos juntos?", "Sí, los asientos van en pares, salvo que el lote diga 'Single seats'. Para grupos de 9 o más, el socio tiene pedidos de grupo."),
 ],
}

ROT = {
 "pt": {"entrada_h": "O que levar e o que é barrado", "publico_h": "Melhor setor para cada perfil", "faq_h": "Perguntas frequentes",
        "conferido": "Data e horário conferidos no parceiro em {conf}.", "hora_local": "{h} (horário local)",
        "titulos": ["{t}{ano}: ingressos com garantia + guia {art} {loc}", "{t}{ano}: ingressos com garantia de entrega",
                    "{t}{ano}: ingressos com garantia", "{t}: ingressos com garantia"],
        "desc": "Ingressos para {t}: {d} às {h}, {loc}. Garantia de entrega do parceiro, como chegar, melhor setor para família ou torcida e o que levar.",
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
