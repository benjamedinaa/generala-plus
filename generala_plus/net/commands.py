from ..core.actions import BUY_MARKET_CARD, PASS_BUY, RELEASE_ALL, ROLL_DICE, SCORE_CATEGORY, TOGGLE_HOLD, Action


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


HELP_TEXT = """Comandos online basicos:
  tirar / roll                 tirar dados
  hold 1..5                    retener/liberar dado
  soltar / release             soltar todos
  anotar <categoria>           anotar categoria
  comprar 1..3                 comprar carta del mercado
  pasar                        pasar fase de compra
  estado                       volver a mostrar estado
  ayuda                        mostrar ayuda
  salir                        cerrar cliente

Categorias: unos, doses, treses, cuatros, cincos, seises, escalera, full, poker, generala, doble.
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
        "Jugadores:",
    ]
    for index, player in enumerate(state["players"]):
        marker = " <- vos" if index == viewer_index else ""
        hand = player["hand"] if isinstance(player["hand"], list) else f"{player['hand']['count']} carta(s)"
        lines.append(f"  {index + 1}. {player['name']}: {player['total']} pts, {player['coins']} monedas, mano: {hand}{marker}")
    lines.append("")
    lines.append("Mercado:")
    for index, card_key in enumerate(state.get("market", []), start=1):
        lines.append(f"  {index}. {card_key}")
    lines.append("")
    lines.append(f"Tu mano: {you['hand']}")
    lines.append("=" * 64)
    return "\n".join(lines)
