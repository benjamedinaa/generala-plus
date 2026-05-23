from ..core.actions import BUY_MARKET_CARD, DISCARD_HAND_CARD, PASS_BUY, RELEASE_ALL, RENEW_MARKET_CARD, ROLL_DICE, SCORE_CATEGORY, TOGGLE_HOLD, USE_ABILITY, USE_CARD, USE_EVENT, Action
from ..rules import CARD_DEFS, CATEGORIES, category_name


CATEGORY_ALIASES = {
    "1": "unos",
    "unos": "unos",
    "2": "doses",
    "doses": "doses",
    "dos": "doses",
    "3": "treses",
    "treses": "treses",
    "tres": "treses",
    "4": "cuatros",
    "cuatros": "cuatros",
    "cuatro": "cuatros",
    "5": "cincos",
    "cincos": "cincos",
    "cinco": "cincos",
    "6": "seises",
    "seises": "seises",
    "seis": "seises",
    "escalera": "escalera",
    "full": "full",
    "poker": "poker",
    "generala": "generala",
    "doble": "generala_doble",
    "generala_doble": "generala_doble",
    "generala doble": "generala_doble",
}


HELP_TEXT = """Comandos online:
  tirar / roll                 tirar dados
  hold 1..5                    retener/liberar dado
  soltar / release             soltar todos
  anotar <categoria>           anotar categoria
  comprar 1..3                 comprar carta del mercado
  renovar 1..3                 renovar una carta del mercado por 1 moneda
  descartar 1..4               descartar carta de tu mano en fase compra
  usar <carta> [args]           usar carta de tu mano
  habilidad [args]              usar habilidad del personaje
  evento [dado]                 usar accion manual del evento, si existe
  pasar                        pasar fase de compra
  estado                       volver a mostrar estado
  ayuda                        mostrar ayuda
  salir                        cerrar cliente

Categorias: unos, doses, treses, cuatros, cincos, seises, escalera, full, poker, generala, doble.

Cartas online principales:
  usar 1 3 +                   Ajuste fino: carta 1, dado 3, subir
  usar 1 3 -                   Ajuste fino: carta 1, dado 3, bajar
  usar 2 5                     Reintento/Espejo/Comodin/Dado dorado: dado 5
  usar 1 2 6                   Dado maestro: dado 2 pasa a 6
  usar 2 1 4                   Copia: copia dado 1 sobre dado 4
  usar 3                       Tirada extra, Duplicador, Seguro, Ancla, Apertura
  usar 1 full                  Rescate/Candado: categoria objetivo
  habilidad 2 +                Matematico: dado 2 sube
  evento 4                     Ronda espejo: invierte dado 4
"""


def parse_command(text, player_index):
    raw = " ".join(text.strip().lower().split())
    if not raw:
        return None
    parts = raw.split()
    verb = parts[0]
    if verb in {"tirar", "roll", "r"}:
        return Action(ROLL_DICE, player_index)
    if verb in {"hold", "retener", "dado"}:
        if len(parts) < 2:
            raise ValueError("Indica un dado del 1 al 5.")
        index = int(parts[1]) - 1
        return Action(TOGGLE_HOLD, player_index, {"index": index})
    if verb in {"soltar", "release", "liberar"}:
        return Action(RELEASE_ALL, player_index)
    if verb in {"anotar", "score", "marcar"}:
        if len(parts) < 2:
            raise ValueError("Indica una categoria.")
        category = CATEGORY_ALIASES.get(" ".join(parts[1:]))
        if not category:
            raise ValueError("Categoria desconocida.")
        return Action(SCORE_CATEGORY, player_index, {"category": category})
    if verb in {"comprar", "buy"}:
        if len(parts) < 2:
            raise ValueError("Indica una carta del mercado: 1, 2 o 3.")
        index = int(parts[1]) - 1
        return Action(BUY_MARKET_CARD, player_index, {"index": index})
    if verb in {"renovar", "renew"}:
        if len(parts) < 2:
            raise ValueError("Indica una carta del mercado: 1, 2 o 3.")
        index = int(parts[1]) - 1
        return Action(RENEW_MARKET_CARD, player_index, {"index": index})
    if verb in {"descartar", "discard"}:
        if len(parts) < 2:
            raise ValueError("Indica una carta de tu mano.")
        index = int(parts[1]) - 1
        return Action(DISCARD_HAND_CARD, player_index, {"index": index})
    if verb in {"usar", "use", "carta"}:
        if len(parts) < 2:
            raise ValueError("Indica una carta de tu mano: 1, 2 o 3.")
        index = int(parts[1]) - 1
        return Action(USE_CARD, player_index, {"hand_index": index, "args": parts[2:]})
    if verb in {"habilidad", "ability"}:
        return Action(USE_ABILITY, player_index, {"args": parts[1:]})
    if verb in {"evento", "event"}:
        return Action(USE_EVENT, player_index, {"args": parts[1:]})
    if verb in {"pasar", "pass"}:
        return Action(PASS_BUY, player_index)
    return None


def format_state(state, viewer_index):
    active = state["active_player_index"]
    you = state["players"][viewer_index]
    lines = [
        "",
        "=" * 64,
        f"Ronda {state['round_number']} | Fase: {state['phase']} | Turno: {state['players'][active]['name']}",
        f"Mensaje: {state['message']}",
        f"Dados: {' '.join(str(v) for v in state['dice'])}   Retenidos: {' '.join('X' if h else '-' for h in state['held'])}   Tiradas: {state['rolls']}/{state['max_rolls']}",
        "",
    ]
    if state["phase"] == "end":
        winner = max(state["players"], key=lambda player: player["total"])
        lines.append(f"GANADOR: {winner['name']} con {winner['total']} puntos")
        lines.append("")
    lines.append("Jugadores:")
    for index, player in enumerate(state["players"]):
        marker = " <- vos" if index == viewer_index else ""
        hand = format_cards(player["hand"]) if isinstance(player["hand"], list) else f"{player['hand']['count']} carta(s)"
        lines.append(f"  {index + 1}. {player['name']}: {player['total']} pts, {player['coins']} monedas, mano: {hand}{marker}")
    lines.append("")
    lines.append("Mercado:")
    for index, card_key in enumerate(state.get("market", []), start=1):
        lines.append(f"  {index}. {format_card(card_key)}")
    lines.append("")
    lines.append(f"Tu mano: {format_cards(you['hand'])}")
    lines.append("")
    lines.append("Planilla:")
    for key, _ in CATEGORIES:
        cells = []
        for player in state["players"]:
            value = player["sheet"].get(key)
            cells.append("-" if value is None else str(value))
        lines.append(f"  {category_name(key):15} {cells[0]:>4} | {cells[1]:>4}")
    lines.append("=" * 64)
    return "\n".join(lines)


def format_card(card_key):
    card = CARD_DEFS.get(card_key)
    if not card:
        return str(card_key)
    return f"{card.name} [{card.tier}, {card.cost} monedas] - {card.text}"


def format_cards(cards):
    if not cards:
        return "(sin cartas)"
    names = []
    for index, card_key in enumerate(cards, start=1):
        card = CARD_DEFS.get(card_key)
        names.append(f"{index}. {card.name if card else card_key}")
    return ", ".join(names)
