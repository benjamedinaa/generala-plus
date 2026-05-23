import math
import random
from collections import Counter
from dataclasses import dataclass, field


CATEGORIES = [
    ("unos", "Unos"),
    ("doses", "Doses"),
    ("treses", "Treses"),
    ("cuatros", "Cuatros"),
    ("cincos", "Cincos"),
    ("seises", "Seises"),
    ("escalera", "Escalera"),
    ("full", "Full"),
    ("poker", "Poker"),
    ("generala", "Generala"),
    ("generala_doble", "Generala doble"),
]

NUMBER_CATEGORIES = {
    "unos": 1,
    "doses": 2,
    "treses": 3,
    "cuatros": 4,
    "cincos": 5,
    "seises": 6,
}

PLUS_STARTING_COINS = 1
PLUS_MAX_COINS = 10
PLUS_MARKET_SIZE = 3
PLUS_HAND_LIMIT = 3
PLUS_BONUS_CAP = 15
PLUS_ASSISTED_POINTS = {
    "escalera": 18,
    "full": 27,
    "poker": 36,
    "generala": 45,
    "generala_doble": 80,
}
PLUS_NATURAL_POINTS = {
    "escalera": 20,
    "full": 30,
    "poker": 40,
    "generala": 50,
    "generala_doble": 100,
}
PLUS_SERVED_POINTS = {
    "escalera": 25,
    "full": 35,
    "poker": 45,
    "generala": 60,
}
SPECIAL_CATEGORIES = {"escalera", "full", "poker", "generala", "generala_doble"}
ATTACK_CARDS = {"sabotaje", "candado", "robo", "intercambio", "mano_pesada", "presion", "veto_mercado", "mesa_fria"}


@dataclass(frozen=True)
class CardDef:
    key: str
    name: str
    cost: int
    tier: str
    text: str


@dataclass(frozen=True)
class CharacterDef:
    key: str
    name: str
    ability: str
    text: str
    cooldown: int = 1
    passive: bool = False
    once: bool = False


@dataclass(frozen=True)
class RoundEvent:
    key: str
    name: str
    text: str


@dataclass
class ScoreResult:
    points: int
    base_points: int
    bonus_points: int = 0
    natural: bool = True
    assisted: bool = False
    served: bool = False
    special: bool = False
    false_generala: bool = False
    tachada: bool = False


CARD_DEFS = {
    "ajuste_fino": CardDef("ajuste_fino", "Ajuste fino", 2, "comun", "+1/-1 a un dado."),
    "reintento": CardDef("reintento", "Reintento", 2, "comun", "Repite un dado."),
    "espejo": CardDef("espejo", "Espejo", 2, "comun", "Invierte un dado."),
    "seguro": CardDef("seguro", "Seguro", 2, "comun", "Piso 10 si venia mal."),
    "reciclaje": CardDef("reciclaje", "Reciclaje", 1, "comun", "Cambia por mercado."),
    "mano_estable": CardDef("mano_estable", "Mano estable", 2, "comun", "Evita un cambio forzado."),
    "correccion_minima": CardDef("correccion_minima", "Correccion minima", 2, "comun", "Completa escalera asistida."),
    "tirada_extra": CardDef("tirada_extra", "Tirada extra", 3, "media", "Agrega una cuarta tirada."),
    "copia": CardDef("copia", "Copia", 3, "media", "Copia un dado propio."),
    "comodin": CardDef("comodin", "Comodin", 5, "media", "Un dado vale cualquiera."),
    "escudo": CardDef("escudo", "Escudo", 2, "media", "Bloquea el proximo ataque."),
    "escalera_rota": CardDef("escalera_rota", "Escalera rota", 3, "media", "Escalera reducida: 15."),
    "ultima_oportunidad": CardDef("ultima_oportunidad", "Ultima oportunidad", 3, "media", "Repite no retenidos al final."),
    "dado_dorado": CardDef("dado_dorado", "Dado dorado", 5, "media", "+5 si participa."),
    "dado_maestro": CardDef("dado_maestro", "Dado maestro", 6, "fuerte", "Elige el valor de un dado."),
    "duplicador": CardDef("duplicador", "Duplicador", 6, "fuerte", "+50%, max +15."),
    "rescate": CardDef("rescate", "Rescate", 6, "fuerte", "Recupera una tachada."),
    "generala_falsa": CardDef("generala_falsa", "Generala falsa", 7, "fuerte", "4 iguales valen 35."),
    "no_cuenta": CardDef("no_cuenta", "No cuenta", 7, "fuerte", "Reinicia tu turno sin monedas."),
    "milagro_controlado": CardDef("milagro_controlado", "Milagro controlado", 7, "fuerte", "Asistida puntua natural."),
    "sabotaje": CardDef("sabotaje", "Sabotaje", 5, "media", "Rival repite un dado."),
    "candado": CardDef("candado", "Candado", 5, "media", "Bloquea una categoria."),
    "robo": CardDef("robo", "Robo", 5, "media", "Roba una carta rival."),
    "intercambio": CardDef("intercambio", "Intercambio", 6, "fuerte", "Rival repite; ganas 1."),
    "mano_pesada": CardDef("mano_pesada", "Mano pesada", 4, "media", "Rival tiene una tirada menos."),
    "presion": CardDef("presion", "Presion", 4, "media", "Rival declara categoria."),
    "foco_numerico": CardDef("foco_numerico", "Foco numerico", 2, "comun", "+3 si anotas numeros."),
    "vision_clara": CardDef("vision_clara", "Vision clara", 2, "comun", "Muestra mejor categoria."),
    "ancla": CardDef("ancla", "Ancla", 2, "comun", "Retiene todos los dados."),
    "apertura": CardDef("apertura", "Apertura", 2, "comun", "Suelta todos los dados."),
    "pulso_controlado": CardDef("pulso_controlado", "Pulso controlado", 3, "media", "Repite dados libres."),
    "dado_duplicador": CardDef("dado_duplicador", "Dado duplicador", 4, "media", "Un dado duplica numeros."),
    "veto_mercado": CardDef("veto_mercado", "Veto de mercado", 4, "media", "Rival no compra."),
    "mesa_fria": CardDef("mesa_fria", "Mesa fria", 4, "media", "Rival no gana monedas."),
}

DECK_SPEC = {
    "ajuste_fino": 5,
    "reintento": 5,
    "espejo": 4,
    "seguro": 4,
    "reciclaje": 4,
    "mano_estable": 3,
    "correccion_minima": 3,
    "tirada_extra": 3,
    "copia": 3,
    "comodin": 2,
    "escudo": 3,
    "escalera_rota": 2,
    "ultima_oportunidad": 2,
    "dado_dorado": 2,
    "dado_maestro": 1,
    "duplicador": 1,
    "rescate": 1,
    "generala_falsa": 1,
    "no_cuenta": 1,
    "milagro_controlado": 1,
    "sabotaje": 2,
    "candado": 2,
    "robo": 1,
    "intercambio": 1,
    "mano_pesada": 1,
    "presion": 1,
    "foco_numerico": 3,
    "vision_clara": 3,
    "ancla": 2,
    "apertura": 2,
    "pulso_controlado": 2,
    "dado_duplicador": 2,
    "veto_mercado": 1,
    "mesa_fria": 1,
}

CHARACTERS = [
    CharacterDef("matematico", "El Matematico", "Calculo preciso", "+1/-1 a un dado cada 4 turnos.", cooldown=4),
    CharacterDef("apostador", "El Apostador", "Declaracion arriesgada", "+8 si cumple, -5 si falla.", cooldown=2),
    CharacterDef("defensivo", "El Defensivo", "Guardia alta", "Empieza con Escudo y cancela un ataque.", passive=True, once=True),
    CharacterDef("estratega", "El Estratega", "Control del mercado", "Renueva gratis el mercado.", cooldown=3),
    CharacterDef("suertudo", "El Suertudo", "Buena fortuna", "Compra cara devuelve 1 moneda.", passive=True),
    CharacterDef("conservador", "El Conservador", "No arriesgar de mas", "Una vez evita tachar y anota 5.", once=True),
    CharacterDef("agresivo", "El Agresivo", "Juego sucio", "Ataques cuestan -1. Mano max 2.", passive=True),
    CharacterDef("caotico", "El Caotico", "Caos controlado", "Carta gratis al iniciar turno.", passive=True),
    CharacterDef("coleccionista", "El Coleccionista", "Mano amplia", "Mano max 4. Sin moneda por no usar carta.", passive=True),
    CharacterDef("precavido", "El Precavido", "Plan B", "Reroll de un dado tras tercera mala.", cooldown=3),
    CharacterDef("ambicioso", "El Ambicioso", "Todo o nada", "Duplica bonus y penalizacion.", cooldown=1),
    CharacterDef("tecnico", "El Tecnico", "Optimizacion", "Muestra la mejor categoria.", cooldown=1),
    CharacterDef("ilusionista", "El Ilusionista", "Reflejo privado", "Invierte un dado cada 3 turnos.", cooldown=3),
    CharacterDef("crupier", "El Crupier", "Corte de mazo", "Cambia una carta del mercado.", cooldown=3),
    CharacterDef("audaz", "El Audaz", "Impulso final", "Repite un dado desde la segunda tirada.", cooldown=3),
    CharacterDef("tesorero", "El Tesorero", "Caja chica", "Comunes cuestan -1. Empieza con +1 moneda.", passive=True),
]

CHARACTER_BY_KEY = {character.key: character for character in CHARACTERS}

ROUND_EVENTS = [
    RoundEvent("dorada", "Ronda dorada", "Primera jugada especial suma +5."),
    RoundEvent("espejo", "Ronda espejo", "Cada jugador invierte un dado gratis."),
    RoundEvent("austera", "Ronda austera", "No se compran cartas."),
    RoundEvent("caotica", "Ronda caotica", "Tras segunda tirada cambia un dado."),
    RoundEvent("defensiva", "Ronda defensiva", "Todos reciben escudo temporal."),
    RoundEvent("apuestas", "Ronda de apuestas", "Declarar da +10, fallar -6."),
    RoundEvent("descuento", "Ronda de descuento", "Primera compra cuesta -1."),
    RoundEvent("presion", "Ronda de presion", "Todos declaran antes de tirar."),
    RoundEvent("recuperacion", "Ronda de recuperacion", "Tachar da +2 monedas."),
]

EVENT_BY_KEY = {event.key: event for event in ROUND_EVENTS}
CLASSIC_EVENT = RoundEvent("clasica", "Ronda clasica", "Sin cartas, habilidades ni ataques.")


@dataclass
class Player:
    name: str
    sheet: dict = field(default_factory=lambda: {key: None for key, _ in CATEGORIES})
    character_key: str = "matematico"
    coins: int = PLUS_STARTING_COINS
    hand: list = field(default_factory=list)
    bonus_total: int = 0
    temp_shield: bool = False
    temp_shield_until_turn: int = None
    cancel_attack_used: bool = False
    attacked_round: int = 0
    pending_attack: dict = field(default_factory=dict)
    blocked_category: str = None
    turns_played: int = 0
    ability_last_turn: int = -999
    ability_once_used: bool = False
    no_tach_streak: int = 0
    full_count: int = 0
    previous_scored_assisted: bool = False
    generala_valid: bool = False
    round_points: dict = field(default_factory=dict)
    offered_market_cards: set = field(default_factory=set)
    market_blocked: bool = False

    @property
    def total(self):
        return sum(value for value in self.sheet.values() if value is not None) + self.bonus_total

    @property
    def complete(self):
        return all(value is not None for value in self.sheet.values())

    @property
    def character(self):
        return CHARACTER_BY_KEY[self.character_key]


def clamp_coins(value):
    return max(0, min(PLUS_MAX_COINS, value))


def add_coins(player, amount):
    if amount <= 0:
        return 0
    before = player.coins
    player.coins = clamp_coins(player.coins + amount)
    return player.coins - before


def build_deck():
    deck = []
    for key, copies in DECK_SPEC.items():
        deck.extend([key] * copies)
    random.shuffle(deck)
    return deck


def hand_limit(player):
    if player.character_key == "coleccionista":
        return 4
    if player.character_key == "agresivo":
        return 2
    return PLUS_HAND_LIMIT


def display_card_cost(card_key, player, event_key=None, discount_available=False):
    cost = CARD_DEFS[card_key].cost
    if player.character_key == "agresivo" and card_key in ATTACK_CARDS:
        cost -= 1
    if player.character_key == "tesorero" and CARD_DEFS[card_key].tier == "comun":
        cost = max(1, cost - 1)
    if event_key == "descuento" and discount_available:
        cost -= 1
    return max(0, cost)


def choose_round_event(round_number):
    if round_number % 4 == 0:
        return CLASSIC_EVENT
    if round_number % 3 == 0:
        return random.choice(ROUND_EVENTS)
    return None


def invert_die(value):
    return 7 - value


def has_four_consecutive(dice):
    values = set(dice)
    return any(set(range(start, start + 4)).issubset(values) for start in (1, 2, 3))


def is_straight(dice):
    values = set(dice)
    return values in ({1, 2, 3, 4, 5}, {2, 3, 4, 5, 6}, {1, 3, 4, 5, 6})


def is_full(dice):
    return sorted(Counter(dice).values()) == [2, 3]


def is_poker(dice):
    return 4 in Counter(dice).values()


def is_generala(dice):
    return len(set(dice)) == 1


def is_straight_with_wildcards(dice, wildcard_indexes):
    wildcards = len(wildcard_indexes)
    fixed = {value for index, value in enumerate(dice) if index not in wildcard_indexes}
    for straight in ({1, 2, 3, 4, 5}, {2, 3, 4, 5, 6}, {1, 3, 4, 5, 6}):
        if fixed.issubset(straight) and len(straight - fixed) <= wildcards:
            return True
    return False


def is_full_with_wildcards(dice, wildcard_indexes):
    if not wildcard_indexes:
        return is_full(dice)
    fixed = [value for index, value in enumerate(dice) if index not in wildcard_indexes]
    wildcards = len(wildcard_indexes)
    counts = Counter(fixed)
    for triple_value in range(1, 7):
        for pair_value in range(1, 7):
            if pair_value == triple_value:
                continue
            need_triple = max(0, 3 - counts[triple_value])
            need_pair = max(0, 2 - counts[pair_value])
            used_fixed = counts[triple_value] + counts[pair_value]
            if used_fixed == len(fixed) and need_triple + need_pair <= wildcards:
                return True
    return False


def is_poker_with_wildcards(dice, wildcard_indexes):
    if len(set(dice)) == 1:
        return False
    if not wildcard_indexes:
        return is_poker(dice)
    fixed = [value for index, value in enumerate(dice) if index not in wildcard_indexes]
    counts = Counter(fixed)
    wildcards = len(wildcard_indexes)
    for value in range(1, 7):
        fixed_matches = counts[value]
        if fixed_matches > 4:
            continue
        wildcards_needed = 4 - fixed_matches
        if wildcards_needed < 0 or wildcards_needed > wildcards:
            continue
        remaining_fixed = len(fixed) - fixed_matches
        remaining_wildcards = wildcards - wildcards_needed
        if remaining_fixed + remaining_wildcards == 1:
            return True
    return False


def is_generala_with_wildcards(dice, wildcard_indexes):
    if not wildcard_indexes:
        return is_generala(dice)
    fixed = [value for index, value in enumerate(dice) if index not in wildcard_indexes]
    counts = Counter(fixed)
    wildcards = len(wildcard_indexes)
    return any(counts[value] + wildcards >= 5 for value in range(1, 7))


def plus_combo_exists(key, dice, wildcard_indexes):
    if key == "escalera":
        return is_straight_with_wildcards(dice, wildcard_indexes)
    if key == "full":
        return is_full_with_wildcards(dice, wildcard_indexes)
    if key == "poker":
        return is_poker_with_wildcards(dice, wildcard_indexes)
    if key in ("generala", "generala_doble"):
        return is_generala_with_wildcards(dice, wildcard_indexes)
    return False


def golden_die_applies(key, dice, golden_indexes):
    if not golden_indexes:
        return False
    if key in NUMBER_CATEGORIES:
        value = NUMBER_CATEGORIES[key]
        return any(dice[index] == value for index in golden_indexes)
    return key in SPECIAL_CATEGORIES


def evaluate_plus_score(
    key,
    dice,
    rolls,
    player,
    assisted=False,
    wildcard_indexes=None,
    golden_indexes=None,
    duplicator_indexes=None,
    score_multiplier=False,
    score_overrides=None,
    force_natural=False,
    event_bonus=0,
    declaration_bonus=0,
):
    wildcard_indexes = wildcard_indexes or set()
    golden_indexes = golden_indexes or set()
    duplicator_indexes = duplicator_indexes or set()
    score_overrides = score_overrides or {}
    counts = Counter(dice)
    natural_for_score = force_natural or not assisted
    served = rolls == 1 and not assisted and not wildcard_indexes
    base_points = 0
    special = key in SPECIAL_CATEGORIES
    false_generala = False

    if key in NUMBER_CATEGORIES:
        value = NUMBER_CATEGORIES[key]
        base_points = value * counts[value]
        base_points += sum(value for index in duplicator_indexes if dice[index] == value)
    elif key == "escalera":
        if score_overrides.get("escalera_rota") and has_four_consecutive(dice):
            base_points = 15
        elif plus_combo_exists(key, dice, wildcard_indexes):
            if served:
                base_points = PLUS_SERVED_POINTS[key]
            else:
                base_points = PLUS_NATURAL_POINTS[key] if natural_for_score else PLUS_ASSISTED_POINTS[key]
    elif key == "full":
        if plus_combo_exists(key, dice, wildcard_indexes):
            if served:
                base_points = PLUS_SERVED_POINTS[key]
            else:
                base_points = PLUS_NATURAL_POINTS[key] if natural_for_score else PLUS_ASSISTED_POINTS[key]
    elif key == "poker":
        if plus_combo_exists(key, dice, wildcard_indexes):
            if served:
                base_points = PLUS_SERVED_POINTS[key]
            else:
                base_points = PLUS_NATURAL_POINTS[key] if natural_for_score else PLUS_ASSISTED_POINTS[key]
    elif key == "generala":
        if plus_combo_exists(key, dice, wildcard_indexes):
            if served:
                base_points = PLUS_SERVED_POINTS[key]
            else:
                base_points = PLUS_NATURAL_POINTS[key] if natural_for_score else PLUS_ASSISTED_POINTS[key]
        elif score_overrides.get("generala_falsa") and is_poker(dice):
            base_points = 35
            false_generala = True
    elif key == "generala_doble":
        if player.generala_valid and plus_combo_exists(key, dice, wildcard_indexes):
            base_points = PLUS_NATURAL_POINTS[key] if natural_for_score else PLUS_ASSISTED_POINTS[key]

    if score_overrides.get("seguro") and key != "generala_doble":
        if key in NUMBER_CATEGORIES and base_points < 10:
            base_points = 10
        elif base_points == 0:
            base_points = 10

    if score_overrides.get("conservador") and base_points == 0 and key != "generala_doble":
        base_points = 5

    bonus = 0
    if base_points > 0:
        if golden_die_applies(key, dice, golden_indexes):
            bonus += 5
        if score_overrides.get("foco_numerico") and key in NUMBER_CATEGORIES:
            bonus += 3
        if event_bonus:
            bonus += event_bonus
        if declaration_bonus:
            bonus += declaration_bonus
        if score_multiplier and key != "generala_doble":
            bonus += min(15, math.ceil(base_points * 0.5))
    bonus = min(PLUS_BONUS_CAP, bonus)
    points = base_points + bonus
    return ScoreResult(
        points=points,
        base_points=base_points,
        bonus_points=bonus,
        natural=natural_for_score and base_points > 0,
        assisted=(not natural_for_score) and base_points > 0,
        served=served and base_points > 0,
        special=special and base_points > 0,
        false_generala=false_generala,
        tachada=points == 0,
    )


def best_category_for_dice(dice, player, rolls, assisted=False):
    best_key = None
    best_points = -1
    for key, _ in CATEGORIES:
        if player.sheet[key] is not None:
            continue
        result = evaluate_plus_score(key, dice, rolls, player, assisted=assisted)
        if result.points > best_points:
            best_key = key
            best_points = result.points
    return best_key, max(0, best_points)


def score_category(key, dice, rolls, sheet):
    if rolls == 0:
        return 0
    counts = Counter(dice)
    if key in NUMBER_CATEGORIES:
        value = NUMBER_CATEGORIES[key]
        return value * counts[value]
    served = rolls == 1
    if key == "escalera":
        return 25 if served and is_straight(dice) else (20 if is_straight(dice) else 0)
    if key == "full":
        return 35 if served and is_full(dice) else (30 if is_full(dice) else 0)
    if key == "poker":
        return 45 if served and is_poker(dice) else (40 if is_poker(dice) else 0)
    if key == "generala":
        return 60 if served and is_generala(dice) else (50 if is_generala(dice) else 0)
    if key == "generala_doble":
        return 100 if sheet.get("generala") not in (None, 0) and is_generala(dice) else 0
    return 0


def category_name(key):
    return dict(CATEGORIES)[key]
