from .rules import ATTACK_CARDS, CARD_DEFS, CHARACTERS, CLASSIC_EVENT, CATEGORIES, NUMBER_CATEGORIES, ROUND_EVENTS


INFO_TABS = ["CLASICO", "PLUS", "CARTAS", "PERSONAJES", "EVENTOS", "CONTROLES", "PLANILLA", "ESTADOS"]


CHARACTER_SHORT_TEXT = {
    "matematico": "+/-1 dado cada 4 turnos",
    "apostador": "+8 si declara bien",
    "defensivo": "Escudo inicial y cancelacion",
    "estratega": "Renueva el mercado",
    "suertudo": "Recupera 1 en compras caras",
    "conservador": "Evita una tachada",
    "agresivo": "Ataques cuestan -1",
    "caotico": "Carta gratis al turno",
    "coleccionista": "Mano maxima 4",
    "precavido": "Plan B cada 3 turnos",
    "ambicioso": "Duplica bonus y riesgo",
    "tecnico": "Sugiere mejor categoria",
    "ilusionista": "Invierte un dado cada 3 turnos",
    "crupier": "Cambia una carta del mercado",
    "audaz": "Reroll desde segunda tirada",
    "tesorero": "Comunes -1 y +1 inicial",
}


CARD_DETAILS = {
    "ajuste_fino": "Permite subir o bajar en 1 el valor de un dado elegido. Sirve para corregir una tirada cercana sin fabricar una jugada perfecta desde cero. Si ayuda a formar una jugada especial, esa jugada cuenta como asistida.",
    "reintento": "Permite volver a tirar un dado adicional una vez. Es una carta de correccion: te da una oportunidad puntual, pero no reemplaza las tres tiradas normales del turno.",
    "espejo": "Invierte el valor de un dado: 1 se vuelve 6, 2 se vuelve 5, 3 se vuelve 4 y viceversa. Es util cuando una tirada quedo cerca de escalera, full o poker por un valor opuesto.",
    "seguro": "Si ibas a anotar menos de 10 puntos en una categoria numerica o estabas por tachar, te permite anotar 10 en su lugar. No se usa para Generala doble y no convierte una mala jugada en especial.",
    "reciclaje": "Cambia una carta de tu mano por una carta del mercado. Es una herramienta de administracion de mano: mejora opciones futuras sin modificar directamente los dados.",
    "mano_estable": "Permite conservar un dado extra cuando un evento o efecto obliga a cambiar dados. Sirve como proteccion tactica contra caos, no como mejora directa de puntaje.",
    "correccion_minima": "Si estas a un solo numero de completar escalera, permite modificar un dado en +1 o -1 solo para completar esa escalera. La escalera resultante es asistida.",
    "tirada_extra": "Agrega una cuarta tirada al turno. Mantiene el foco en los dados: no cambia valores por si sola, solo te da una oportunidad mas de tirar los dados no retenidos.",
    "copia": "Copia el valor de un dado propio en otro dado propio. Es fuerte para acercarse a poker o generala, pero la jugada obtenida cuenta como asistida.",
    "comodin": "Un dado cuenta como cualquier numero para formar una jugada especial. No cambia visualmente el dado; solo altera la evaluacion. Toda jugada lograda asi es asistida.",
    "escudo": "Bloquea el proximo ataque recibido de otro jugador. Protege contra cartas agresivas, pero no mejora tus dados ni tu puntaje directamente.",
    "escalera_rota": "Si tienes cuatro numeros consecutivos, permite anotar una escalera reducida de 15 puntos. No cuenta como escalera natural ni como jugada servida.",
    "ultima_oportunidad": "Si despues de la tercera tirada no lograste una jugada especial, puedes repetir una vez mas los dados no retenidos. Es una salida de emergencia, no una garantia.",
    "dado_dorado": "Marca un dado como dorado. Si ese dado participa en la jugada anotada, suma +5 puntos respetando los limites de bonus. Es mejor cuando ya tienes una jugada razonable.",
    "dado_maestro": "Permite fijar un dado al valor que quieras. Es una carta fuerte y cara; la jugada resultante cuenta como asistida, por eso no siempre conviene gastarla.",
    "duplicador": "La jugada anotada suma 50% extra con un maximo de +15 puntos. No se puede usar sobre Generala doble. Es potente, pero el techo evita diferencias exageradas.",
    "rescate": "Recupera una categoria tachada anteriormente. La categoria queda vacia y podra usarse en otro turno. No da puntos al instante: compra una segunda oportunidad.",
    "generala_falsa": "Si tienes cuatro dados iguales, puedes anotarlo como Generala reducida de 35 puntos. No habilita Generala doble y no cuenta como Generala natural.",
    "no_cuenta": "Anula un turno malo y permite volver a jugar el turno completo, pero ese turno no entrega monedas. Debe usarse antes de anotar categoria.",
    "milagro_controlado": "Convierte una jugada asistida en natural solo para calcular puntaje. Nunca la convierte en servida. Es poderosa porque mejora el valor, no porque cree la jugada.",
    "sabotaje": "Antes del turno rival, obliga a que repita un dado aleatorio despues de su primera tirada. No destruye una jugada ya conseguida.",
    "candado": "Antes del turno rival, bloquea una categoria durante su proximo turno. Sirve para presionar decisiones, no para borrar puntos ya anotados.",
    "robo": "Roba una carta aleatoria de la mano de un rival. Si el rival no tiene cartas, no produce efecto. Es ataque de recursos, no de dados.",
    "intercambio": "Efecto simplificado de ataque: el rival repite un dado y el atacante gana 1 moneda. Representa interferencia sin romper completamente el turno rival.",
    "mano_pesada": "Reduce en una la cantidad de tiradas del rival en su proximo turno. No puede encadenarse sobre el mismo jugador dentro de la misma ronda.",
    "presion": "El rival debe declarar que categoria intentara antes de tirar. Si anota otra cosa, no recibe monedas al final del turno.",
    "foco_numerico": "Prepara una anotacion numerica: si terminas anotando Unos, Doses, Treses, Cuatros, Cincos o Seises y consigues puntos, suma +3 respetando el limite general de bonus. No ayuda a formar jugadas especiales.",
    "vision_clara": "Consulta la mejor categoria actual segun los dados y la planilla. No modifica dados ni puntaje, pero consume la carta y ayuda a evitar una mala decision.",
    "ancla": "Retiene todos los dados actuales de una sola vez. No cambia valores ni puntajes: sirve para cerrar una decision de conservacion rapidamente y evitar soltar dados uno por uno.",
    "apertura": "Libera todos los dados retenidos de una sola vez. Es una herramienta tactica para cambiar de plan cuando una jugada deja de convenir despues de una tirada.",
    "pulso_controlado": "Repite una vez todos los dados que no estan retenidos. Es una tirada tactica de correccion: mejora un intento cercano, pero no cambia dados guardados.",
    "dado_duplicador": "Marca un dado para que cuente doble si lo anotas en su categoria numerica correspondiente. No mejora full, poker ni generala; empuja la planilla numerica.",
    "veto_mercado": "Ataque suave: el rival juega su turno normalmente, pero pierde la fase de compra al final. No toca sus dados ni su puntaje.",
    "mesa_fria": "Ataque economico: el rival juega su turno, pero no gana monedas durante ese turno. Sirve para cortar acumulacion sin arruinar una jugada conseguida.",
}


EVENT_EXTRAS = {
    "clasica": "Refuerza la base del juego: sin cartas, habilidades ni ataques. Solo importan tiradas, retencion y planilla.",
    "dorada": "Premia la primera jugada especial de la ronda con +5, asi que genera tension por quien anota primero una escalera, full, poker o generala.",
    "espejo": "Da una inversion gratuita de dado durante el turno. Es similar al concepto de Espejo, pero aparece como regla global de ronda.",
    "austera": "Corta temporalmente la economia de cartas: se juega el turno, pero no se puede comprar al final.",
    "caotica": "Introduce caos controlado: un solo dado cambia una vez despues de la segunda tirada.",
    "defensiva": "Todos reciben proteccion temporal, bajando el impacto de ataques durante esa ronda.",
    "apuestas": "Aumenta el valor de declarar objetivo, pero tambien la penalizacion por fallar.",
    "descuento": "La primera compra de cada jugador cuesta 1 moneda menos, haciendo mas atractivo el mercado.",
    "presion": "Todos deben elegir una categoria objetivo antes de tirar. Lograrla premia con moneda extra.",
    "recuperacion": "Tachar deja de sentirse tan castigador: entrega mas monedas para recomponerse.",
}


def card_detail(key, card=None):
    card = card or CARD_DEFS[key]
    tier = "ATAQUE" if key in ATTACK_CARDS else card.tier.upper()
    detail = CARD_DETAILS.get(key, card.text)
    return f"{detail} Costo: {card.cost} monedas. Tipo: {tier}."


def character_detail(character):
    cooldown = "pasiva" if character.passive else f"cooldown {character.cooldown} turno(s)"
    once = " Uso unico." if character.once else ""
    return f"{character.ability}. {character.text} Funciona como habilidad {cooldown}.{once} Esta identidad cambia la forma de administrar riesgo, monedas, mano o decisiones sin reemplazar la importancia de los dados."


def event_detail(event):
    return f"{event.text} {EVENT_EXTRAS.get(event.key, '')}".strip()


def info_items(tab):
    if tab == "CLASICO":
        return [
            ("clasica", "OBJETIVO DE LA PARTIDA", "Cada jugador completa una planilla con once categorias. En cada turno debes anotar exactamente una categoria disponible. Cuando todos completan toda la planilla, gana quien tenga mas puntos totales."),
            ("dado_dorado", "COMO FUNCIONA UN TURNO", "Tiras cinco dados. Puedes tirar hasta tres veces en total. Despues de cada tirada puedes retener dados para conservarlos y volver a tirar solo los dados libres. La decision importante es elegir que guardar y cuando dejar de arriesgar."),
            ("mano_estable", "RETENER Y SOLTAR DADOS", "Click izquierdo sobre un dado lo retiene o lo libera. Las teclas 1 a 5 hacen lo mismo para cada dado. Si retienes un dado, no cambia en la proxima tirada. La tecla L o click derecho sobre un dado suelta todos los dados retenidos."),
            ("correccion_minima", "CATEGORIAS NUMERICAS", "Unos, Doses, Treses, Cuatros, Cincos y Seises suman solamente los dados de ese valor. Por ejemplo, con 5-5-5-2-1, anotar Cincos da 15 puntos. Si no tienes dados de ese numero, la categoria vale 0."),
            ("escalera_rota", "ESCALERA", "La escalera se logra con 1-2-3-4-5, 2-3-4-5-6 o 1-3-4-5-6. Vale 20 puntos. Si sale en la primera tirada, sin ayudas, vale 25 como jugada servida."),
            ("comodin", "FULL", "Full es una combinacion de tres dados iguales y dos dados iguales de otro valor, por ejemplo 3-3-3-5-5. Vale 30 puntos, o 35 si sale servido. Cinco dados iguales no cuentan como full: eso es Generala."),
            ("duplicador", "POKER", "Poker es exactamente cuatro dados iguales y un quinto dado distinto, por ejemplo 6-6-6-6-2. Vale 40 puntos, o 45 si sale servido. Cinco dados iguales no cuentan como poker: eso es Generala."),
            ("generala_falsa", "GENERALA", "Generala es tener cinco dados iguales. Vale 50 puntos, o 60 si sale servida. En este juego la Generala servida no gana automaticamente la partida: suma mucho, pero la partida sigue."),
            ("dado_maestro", "GENERALA DOBLE", "Generala doble solo puede anotarse si ya conseguiste una Generala valida antes. Si vuelves a hacer cinco iguales, puedes anotar 100 puntos. Una Generala falsa o reducida no habilita esta categoria."),
            ("sabotaje", "TACHAR", "Si no puedes o no quieres puntuar una categoria, puedes tacharla anotando 0. Tachar duele porque esa categoria queda cerrada para siempre, pero en modo Plus puede darte monedas para recuperarte."),
        ]
    if tab == "PLUS":
        return [
            ("dado_dorado", "QUE AGREGA GENERALA PLUS", "Plus conserva la Generala tradicional como base. Los dados siguen siendo lo mas importante. Las cartas, monedas, personajes y eventos existen para corregir tiradas cercanas, abrir decisiones tacticas y generar variedad sin fabricar victorias automaticas."),
            ("bonus", "MONEDAS", "Empiezas con 1 moneda y puedes acumular hasta 10. El ingreso inicial solo aparece si estas en 4 monedas o menos, asi no se acumulan recursos sin decidir. Las mejores ganancias vienen de jugar bien: numéricas altas, jugadas especiales, tachar como recuperacion controlada, no usar cartas cuando conviene y cumplir misiones."),
            ("reciclaje", "MERCADO VISIBLE", "El mercado muestra 3 cartas disponibles. Al terminar tu turno puedes comprar una carta si tienes monedas y espacio en mano. Tambien puedes renovar una carta del mercado con click derecho pagando 1 moneda durante la fase de compra."),
            ("coleccionista", "MANO DE CARTAS", "La mano normal tiene maximo 3 cartas. Algunas personalidades cambian ese limite. Si la mano esta llena, no puedes comprar hasta descartar una carta. Las cartas de mano se usan durante el turno, antes de anotar."),
            ("habilidad_usada", "LIMITES DE BALANCE", "Puedes usar como maximo 1 carta y 1 habilidad por turno. Esta regla evita combos exagerados y mantiene la partida cerca de una Generala clasica: las ayudas importan, pero no deben decidir solas la mesa."),
            ("comodin", "NATURAL, ASISTIDA Y SERVIDA", "Una jugada natural sale solo con dados. Una asistida usa carta, habilidad o evento y puntua un poco menos en jugadas especiales. Una jugada servida solo cuenta si sale en la primera tirada sin ninguna ayuda."),
            ("matematico", "PERSONAJES", "Cada jugador elige un personaje al inicio. Algunos tienen habilidades activas con cooldown, otros tienen efectos pasivos. El personaje da identidad y estilo, pero no reemplaza buenas decisiones con los dados."),
            ("dorada", "EVENTOS DE RONDA", "Cada 3 rondas puede aparecer un evento global. Cada 4 rondas se juega una Ronda Clasica sin cartas, habilidades ni ataques. Esto mantiene el juego anclado en Generala pura."),
            ("tirada_extra", "FASE TURNO", "Durante la fase de turno tiras dados, retienes, puedes usar una ayuda si corresponde y finalmente eliges una categoria para anotar. Hasta que anotes, no puedes comprar cartas."),
            ("descuento", "FASE COMPRA", "Despues de anotar entras en fase compra. Ahi el foco pasa a tu mano y al mercado: puedes comprar una carta, descartar de tu mano o pasar. Luego empieza el turno del siguiente jugador."),
        ]
    if tab == "CARTAS":
        return [
            ("ajuste_fino", "COMO LEER UNA CARTA", "Cada carta muestra costo, nombre, icono, rareza y descripcion breve. El costo se paga solo al comprarla desde el mercado. Tener una carta en mano no cuesta nada adicional, salvo efectos especiales como El Caotico."),
            ("dado_dorado", "RAREZAS Y PESO EN EL JUEGO", "Las comunes son baratas y corrigen poco. Las medias abren oportunidades mas claras. Las fuertes son caras y aparecen menos. Las de ataque molestan al rival, pero no destruyen una jugada ya conseguida."),
            ("habilidad_usada", "USAR CARTAS", "En tu turno puedes usar maximo 1 carta. Si la carta modifica dados, evaluacion o puntaje, la jugada se considera asistida. No puedes encadenar varias cartas para construir una jugada perfecta desde cero."),
            ("candado_activo", "CARTAS DESHABILITADAS", "Una carta puede estar apagada si no es la fase correcta, si ya usaste carta este turno, si estas en Ronda Clasica, si requiere dados y todavia no tiraste, o si el ataque ya no puede jugarse."),
            ("reciclaje", "COMPRAR, DESCARTAR Y RENOVAR", "En fase compra, click izquierdo sobre una carta del mercado la compra. Si tu mano esta llena, primero debes descartar una carta de tu mano. Click derecho sobre una carta del mercado la renueva por 1 moneda."),
            ("sabotaje", "CARTAS DE ATAQUE", "Los ataques se juegan antes de que el rival empiece su turno efectivo, nunca despues de que ya consiguio una jugada. Ademas, no se puede encadenar mas de un ataque sobre el mismo jugador en la misma ronda."),
        ] + [(key, card.name.upper(), card_detail(key, card)) for key, card in CARD_DEFS.items()]
    if tab == "PERSONAJES":
        return [
            ("matematico", "QUE SON LOS PERSONAJES", "Los personajes son estilos de juego. No son clases rotas ni reemplazan los dados: te dan una inclinacion tactica, como corregir mejor, defenderte, comprar distinto, presionar al rival o planificar."),
            ("cooldown", "COOLDOWN", "Las habilidades activas no siempre estan listas. El cooldown cuenta turnos propios jugados. Cuando la habilidad esta en cooldown, el boton aparece apagado y el panel muestra cuanto falta."),
            ("habilidad_usada", "HABILIDADES PASIVAS", "Algunos personajes no usan boton. Sus efectos se aplican automaticamente cuando corresponde: por ejemplo descuentos, mano mas grande, escudo inicial o cambios de limite de mano."),
            ("ambicioso", "VENTAJAS Y DESVENTAJAS", "Algunos personajes tienen una contra para mantener equilibrio. El Agresivo paga menos ataques pero tiene menos mano. El Coleccionista guarda mas cartas pero pierde la moneda por no usar carta."),
            ("tecnico", "ELEGIR PERSONAJE", "Si eres nuevo, El Matematico, El Defensivo o El Tecnico son faciles de entender. Si quieres riesgo, El Apostador o El Ambicioso tienen mas tension. Si quieres jugar con mercado, El Estratega o El Coleccionista brillan."),
        ] + [(character.key, character.name.upper(), character_detail(character)) for character in CHARACTERS]
    if tab == "EVENTOS":
        return [
            ("dorada", "CUANDO APARECEN", "Los eventos globales aparecen cada 3 rondas. Cambian una regla de toda la ronda para ambos jugadores. Cada 4 rondas se fuerza Ronda Clasica, donde se apagan cartas, habilidades y ataques."),
            ("clasica", "RONDA CLASICA", event_detail(CLASSIC_EVENT)),
            ("espejo_evento", "EVENTOS MANUALES", "Algunos eventos dan una accion que puedes activar con el boton USAR EVENTO. Por ejemplo, Ronda Espejo permite invertir un dado gratis una vez durante el turno."),
            ("caotica", "EVENTOS AUTOMATICOS", "Otros eventos se aplican solos. Ronda Caotica cambia un dado al final de la segunda tirada. Ronda Austera bloquea compras. Ronda Defensiva entrega escudos temporales."),
            ("apuestas", "EVENTOS DE RIESGO", "Eventos como Apuestas o Presion agregan decisiones antes de tirar. Pueden premiarte si cumples lo declarado, pero castigan o limitan si fallas. La idea es tension, no azar puro."),
        ] + [((event.key if event.key != "espejo" else "espejo_evento"), event.name.upper(), event_detail(event)) for event in ROUND_EVENTS]
    if tab == "CONTROLES":
        return [
            ("mano_estable", "DADOS CON MOUSE", "Click izquierdo sobre un dado lo retiene o lo libera. Click derecho sobre cualquier dado suelta todos los dados retenidos de una sola vez, ideal cuando quieres replantear la tirada completa."),
            ("tirada_extra", "TIRAR DADOS", "Presiona ESPACIO o el boton TIRAR DADOS. Si estas en el ultimo tiro, el boton lo indica. No puedes tirar si ya agotaste tiradas, si todos los dados estan retenidos o si debes declarar una categoria antes."),
            ("dado_maestro", "TECLADO DE DADOS", "Las teclas 1 a 5 alternan retencion de cada dado. Cuando una carta como Dado Maestro pide fijar valor, las teclas 1 a 6 eligen el numero final del dado seleccionado."),
            ("mano_estable", "SOLTAR TODOS", "La tecla L libera todos los dados retenidos. Es equivalente al click derecho sobre un dado. Si no hay dados retenidos, no cambia la jugada."),
            ("tecnico", "INFORMACION", "La tecla H abre o cierra este manual. Tambien puedes entrar desde el menu de pausa con el boton INFORMACION."),
            ("seguro", "PAUSA", "ESC abre o cierra el menu de pausa durante la partida. En pausa puedes continuar, abrir informacion, ajustar sonido, volver al menu o cerrar el juego."),
            ("descuento", "MERCADO", "En fase compra, click izquierdo compra una carta del mercado. Click derecho renueva esa carta por 1 moneda. Click sobre una carta de tu mano la descarta si necesitas espacio."),
            ("clasica", "PANTALLA Y REINICIO", "F11 alterna pantalla completa. En la pantalla final, R vuelve al menu para empezar una partida nueva."),
        ]
    if tab == "PLANILLA":
        return [
            ("correccion_minima", "COMO SE USA", "La planilla es obligatoria: al final de cada turno debes elegir una categoria vacia para anotar. Una vez usada, esa fila queda cerrada para el resto de la partida."),
            ("tecnico", "PREVIEW DE PUNTAJE", "Si una categoria esta disponible y ya tiraste dados, la planilla muestra entre parentesis el puntaje que obtendrias ahora. Si no hay jugada valida, muestra un guion gris en vez de llenar la tabla de ceros rojos."),
            ("carta_usada", "CATEGORIA ANOTADA", "Una categoria anotada muestra su valor fijo. No se puede cambiar salvo efectos especiales como Rescate, que puede recuperar una categoria tachada y dejarla vacia para otro turno."),
            ("penalizacion", "TACHADA", "Un 0 rojo significa que esa categoria fue tachada realmente. No es un preview. En modo Plus, tachar da monedas como compensacion para que una mala tirada no te deje fuera de partida."),
            ("candado_activo", "BLOQUEADA", "Si un rival usa Candado, una categoria puede quedar bloqueada solo durante tu proximo turno. La planilla lo marca para que no intentes anotarla por error."),
            ("bonus", "BONUS Y EXTRAS", "Algunos efectos agregan puntos extra, como Dado Dorado, Ronda Dorada, declaraciones o Duplicador. Esos puntos se suman al total respetando limites de balance."),
            ("comodin", "NATURAL VS ASISTIDA", "Natural significa que la jugada salio solo con dados. Asistida significa que se uso carta, habilidad o evento. En Plus, escalera, full, poker, generala y generala doble asistidas valen un poco menos."),
            ("dado_dorado", "TOTAL", "El total suma las categorias anotadas mas extras o penalizaciones. La partida termina cuando ambos jugadores completan toda la planilla."),
        ] + [(key, label.upper(), "Categoria numerica: suma solamente los dados que muestran ese numero." if key in NUMBER_CATEGORIES else "Categoria especial: necesita una combinacion concreta y puede tener puntaje natural, servido o asistido.") for key, label in CATEGORIES]
    return [
        ("dado_dorado", "MONEDAS", "Las fichas G+ llenas son monedas disponibles. Los contornos vacios muestran capacidad hasta el limite de 10. Si llegas al limite, las monedas nuevas se pierden."),
        ("escudo_activo", "ESCUDO ACTIVO", "Indica proteccion contra el proximo ataque rival. Puede venir de carta Escudo, personaje Defensivo o Ronda Defensiva. Al bloquear un ataque, se consume."),
        ("candado_activo", "CANDADO", "Indica que una categoria esta bloqueada por ataque. Solo afecta el turno actual del jugador atacado y no borra puntos ya anotados."),
        ("carta_usada", "CARTA USADA", "Significa que ya gastaste la carta permitida para este turno. Puedes seguir tirando o anotar, pero no puedes usar otra carta hasta tu siguiente turno."),
        ("habilidad_usada", "HABILIDAD USADA", "La habilidad activa del personaje ya fue usada este turno o no esta disponible. Las habilidades pasivas no requieren boton y se aplican solas."),
        ("cooldown", "COOLDOWN", "Indica que una habilidad necesita esperar. El contador se reduce con turnos propios. Cuando llega a listo, el boton vuelve a estar disponible si la fase lo permite."),
        ("bonus", "BONUS", "Representa puntos extra o recompensas positivas. Algunos bonus van al puntaje de la jugada y otros se acumulan como extras del jugador."),
        ("penalizacion", "PENALIZACION", "Representa perdida de puntos, riesgo fallido o restriccion. Se usa poco y en rojo para que sea claro que es un efecto negativo."),
        ("tirada_extra", "FASE TURNO", "Durante fase turno, los dados, el boton de tirar y la planilla son lo principal. Mercado y mano quedan visibles pero con menos protagonismo."),
        ("descuento", "FASE COMPRA", "Durante fase compra, el mercado y la mano suben de importancia. Puedes comprar, renovar, descartar o pasar. Los dados quedan en segundo plano."),
        ("clasica", "RONDA CLASICA", "Estado especial de ronda: sin cartas, habilidades ni ataques. Es Generala pura y sirve para que el modo Plus no pierda su base."),
        ("coleccionista", "MANO LLENA", "Si tu mano esta llena no puedes comprar. En fase compra puedes descartar una carta propia para hacer espacio antes de adquirir otra."),
    ]
