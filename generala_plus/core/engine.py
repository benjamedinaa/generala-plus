import random

from ..rules import (
    ATTACK_CARDS,
    CARD_DEFS,
    CHARACTER_BY_KEY,
    CATEGORIES,
    NUMBER_CATEGORIES,
    PLUS_MARKET_SIZE,
    SPECIAL_CATEGORIES,
    add_coins,
    best_category_for_dice,
    build_deck,
    category_name,
    choose_round_event,
    display_card_cost,
    evaluate_plus_score,
    hand_limit,
    invert_die,
    is_straight,
    score_category as classic_score_category,
)
from ..settings import DICE_COUNT, MAX_ROLLS
from .actions import (
    BUY_MARKET_CARD,
    DISCARD_HAND_CARD,
    PASS_BUY,
    RELEASE_ALL,
    RENEW_MARKET_CARD,
    ROLL_DICE,
    SCORE_CATEGORY,
    TOGGLE_HOLD,
    USE_ABILITY,
    USE_CARD,
    USE_EVENT,
)
from .state import GameState, PlayerState


class InvalidAction(ValueError):
    pass


class GeneralaEngine:
    """Pygame-free game controller for future online/server play.

    This does not replace the local UI yet. It gives the project a serializable,
    testable, authoritative core that can gradually absorb the current local
    flow before sockets are introduced.
    """

    def __init__(self, state, seed=None):
        self.state = state
        self.random = random.Random(seed)

    @classmethod
    def new_game(cls, names, plus_mode=True, character_keys=None, seed=None):
        character_keys = character_keys or ["matematico"] * len(names)
        players = [
            PlayerState(name=name, character_key=character_keys[index % len(character_keys)])
            for index, name in enumerate(names)
        ]
        state = GameState(players=players, plus_mode=plus_mode, deck=build_deck(), max_rolls=MAX_ROLLS)
        engine = cls(state, seed=seed)
        engine.random.shuffle(state.deck)
        if plus_mode:
            engine.fill_market_for_active_player(record_offer=True)
            engine.begin_turn(grant_start_coin=True)
        return engine

    def apply(self, action):
        self._assert_actor(action.player_index)
        if action.kind == ROLL_DICE:
            return self.roll_dice()
        if action.kind == TOGGLE_HOLD:
            return self.toggle_hold(int(action.payload["index"]))
        if action.kind == RELEASE_ALL:
            return self.release_all()
        if action.kind == SCORE_CATEGORY:
            return self.score_category(str(action.payload["category"]))
        if action.kind == BUY_MARKET_CARD:
            return self.buy_market_card(int(action.payload["index"]))
        if action.kind == RENEW_MARKET_CARD:
            return self.renew_market_card(int(action.payload["index"]))
        if action.kind == DISCARD_HAND_CARD:
            return self.discard_hand_card(int(action.payload["index"]))
        if action.kind == PASS_BUY:
            return self.end_buy_phase()
        if action.kind == USE_CARD:
            return self.use_card(int(action.payload["hand_index"]), list(action.payload.get("args", [])))
        if action.kind == USE_ABILITY:
            return self.use_ability(list(action.payload.get("args", [])))
        if action.kind == USE_EVENT:
            return self.use_event(list(action.payload.get("args", [])))
        raise InvalidAction(f"Accion no soportada por el motor base: {action.kind}")

    def _assert_actor(self, player_index):
        if player_index != self.state.active_player_index:
            raise InvalidAction("No es el turno de ese jugador.")

    def _draw_card(self, exclude=None):
        exclude = set(exclude or ())
        if not self.state.deck:
            self.state.deck = self.state.discard[:]
            self.state.discard.clear()
            self.random.shuffle(self.state.deck)
        allowed = [index for index, card_key in enumerate(self.state.deck) if card_key not in exclude]
        if not allowed:
            self.state.deck = build_deck()
            self.random.shuffle(self.state.deck)
            allowed = [index for index, card_key in enumerate(self.state.deck) if card_key not in exclude]
        if not allowed:
            allowed = list(range(len(self.state.deck)))
        return self.state.deck.pop(self.random.choice(allowed))

    def fill_market_for_active_player(self, record_offer=False):
        if not self.state.plus_mode:
            return
        player = self.state.active_player
        clean_market = []
        seen = set()
        for card_key in self.state.market:
            if card_key in seen or card_key in player.offered_market_cards:
                self.state.discard.append(card_key)
            else:
                clean_market.append(card_key)
                seen.add(card_key)
        self.state.market = clean_market
        while len(self.state.market) < PLUS_MARKET_SIZE:
            exclude = set(self.state.market) | set(player.offered_market_cards)
            self.state.market.append(self._draw_card(exclude))
        if record_offer:
            player.offered_market_cards.update(self.state.market)

    def start_plus_round_if_needed(self):
        state = self.state
        if not state.plus_mode:
            return
        round_number = state.round_number
        if state.active_event_round == round_number:
            return
        for player in state.players:
            if player.temp_shield and player.temp_shield_until_turn is None:
                player.temp_shield = False
        event = choose_round_event(round_number)
        state.active_event_key = event.key if event else None
        state.active_event_round = round_number
        state.golden_bonus_used_round = 0
        state.discount_buyers.clear()
        state.round_scores.setdefault(round_number, {})
        if event and event.key == "defensiva":
            for player in state.players:
                player.temp_shield = True
                player.temp_shield_until_turn = None

    def begin_turn(self, grant_start_coin=True):
        state = self.state
        if not state.plus_mode:
            return
        self.start_plus_round_if_needed()
        state.used_card_this_turn = False
        state.used_ability_this_turn = False
        state.assisted_turn = False
        state.event_action_used = False
        state.no_coins_this_turn = False
        state.declarations.clear()
        state.pending_turn_attack.clear()
        state.wildcard_indexes.clear()
        state.golden_indexes.clear()
        state.duplicator_indexes.clear()
        state.score_multiplier = False
        state.force_natural_score = False
        state.score_overrides.clear()
        player = state.active_player
        if player.temp_shield and player.temp_shield_until_turn is not None and state.turn >= player.temp_shield_until_turn:
            player.temp_shield = False
            player.temp_shield_until_turn = None
        player.turns_played += 1
        attack = dict(player.pending_attack)
        player.pending_attack.clear()
        player.blocked_category = None
        player.market_blocked = False
        state.max_rolls = MAX_ROLLS
        if attack.get("type") == "mano_pesada":
            state.max_rolls = max(1, MAX_ROLLS - 1)
        elif attack.get("type") == "presion":
            state.declarations.append({"source": "presion_ataque", "category": None, "bonus": 0, "penalty": 0, "coin": 0, "no_coins_on_fail": True})
        elif attack.get("type") == "candado":
            player.blocked_category = attack.get("category")
        elif attack.get("type") == "veto_mercado":
            player.market_blocked = True
        elif attack.get("type") == "mesa_fria":
            state.no_coins_this_turn = True
        elif attack:
            state.pending_turn_attack = attack
        if state.active_event_key == "presion":
            state.declarations.append({"source": "presion_evento", "category": None, "bonus": 0, "penalty": 0, "coin": 1, "no_coins_on_fail": False})
        if player.character_key == "caotico" and len(player.hand) < hand_limit(player):
            player.hand.append(self._draw_card())
        if grant_start_coin and player.coins <= 4 and not state.no_coins_this_turn:
            add_coins(player, 1)
        self.fill_market_for_active_player(record_offer=True)
        state.message = f"Turno de {player.name}."

    def roll_dice(self):
        if self.state.phase != "turn":
            raise InvalidAction("Solo se puede tirar en fase de turno.")
        if self._needs_forced_declaration():
            raise InvalidAction("Primero hay que declarar categoria.")
        if self.state.rolls >= self.state.max_rolls:
            raise InvalidAction("No quedan tiradas.")
        if all(self.state.held):
            raise InvalidAction("Todos los dados estan retenidos.")
        if self.state.rolls == 0:
            self.state.dice = [self.random.randint(1, 6) for _ in range(DICE_COUNT)]
        else:
            self.state.dice = [
                value if held else self.random.randint(1, 6)
                for value, held in zip(self.state.dice, self.state.held)
            ]
        self.state.rolls += 1
        self.apply_plus_after_roll()
        self.state.message = "Dados tirados."
        return self.state

    def toggle_hold(self, index):
        if self.state.rolls == 0:
            raise InvalidAction("Primero hay que tirar.")
        if not 0 <= index < DICE_COUNT:
            raise InvalidAction("Indice de dado invalido.")
        self.state.held[index] = not self.state.held[index]
        self.state.message = "Dado retenido." if self.state.held[index] else "Dado liberado."
        return self.state

    def release_all(self):
        self.state.held = [False] * DICE_COUNT
        self.state.message = "Todos los dados liberados."
        return self.state

    def score_category(self, category):
        player = self.state.active_player
        if self.state.phase != "turn":
            raise InvalidAction("No se puede anotar fuera del turno.")
        if self.state.rolls == 0:
            if self.state.plus_mode and self._needs_forced_declaration():
                return self.set_forced_declaration(category)
            raise InvalidAction("Primero hay que tirar.")
        if player.sheet.get(category) is not None:
            raise InvalidAction("Categoria ya usada.")
        if self.state.plus_mode:
            if self._needs_forced_declaration():
                raise InvalidAction("Primero hay que declarar categoria.")
            if player.blocked_category == category:
                raise InvalidAction(f"Candado activo: no podes anotar {category_name(category)}.")
            declaration_bonus, penalty, extra_coins, no_coins_fail = self.resolve_declarations(category)
            event_bonus = 0
            if self.state.active_event_key == "dorada" and self.state.golden_bonus_used_round != self.state.round_number and category in SPECIAL_CATEGORIES:
                event_bonus = 5
                self.state.assisted_turn = True
            result = evaluate_plus_score(
                category,
                self.state.dice,
                self.state.rolls,
                player,
                assisted=self.state.assisted_turn,
                wildcard_indexes=self.state.wildcard_indexes,
                golden_indexes=self.state.golden_indexes,
                duplicator_indexes=self.state.duplicator_indexes,
                score_multiplier=self.state.score_multiplier,
                score_overrides=self.state.score_overrides,
                force_natural=self.state.force_natural_score,
                event_bonus=event_bonus,
                declaration_bonus=declaration_bonus,
            )
            points = result.points
            if event_bonus and result.special:
                self.state.golden_bonus_used_round = self.state.round_number
            if no_coins_fail:
                self.state.no_coins_this_turn = True
            if penalty:
                player.bonus_total -= penalty
            if category == "generala" and result.base_points > 0 and not result.false_generala:
                player.generala_valid = True
        else:
            points = classic_score_category(category, self.state.dice, self.state.rolls, player.sheet)
        player.sheet[category] = points
        self.state.message = f"{category}: {points} puntos."
        if self.state.plus_mode:
            self.award_plus_rewards(player, category, result, extra_coins)
            self.state.round_scores.setdefault(self.state.round_number, {})[player.name] = points
        if self.state.complete:
            self.state.phase = "end"
            return self.state
        if self.state.plus_mode:
            self.state.phase = "buy"
        else:
            self.end_buy_phase()
        return self.state

    def use_card(self, hand_index, args):
        state = self.state
        player = state.active_player
        if not state.plus_mode:
            raise InvalidAction("Las cartas solo existen en modo Plus.")
        if state.phase != "turn":
            raise InvalidAction("Las cartas tacticas se usan durante el turno.")
        if state.used_card_this_turn:
            raise InvalidAction("Ya usaste una carta este turno.")
        if not 0 <= hand_index < len(player.hand):
            raise InvalidAction("Carta de mano invalida.")

        card_key = player.hand[hand_index]
        if self.state.active_event_key == "clasica":
            raise InvalidAction("Ronda clasica: no se pueden usar cartas.")
        pre_roll_allowed = {"escudo", "rescate", "reciclaje", "tirada_extra", "no_cuenta", "vision_clara"} | ATTACK_CARDS
        if state.rolls == 0 and card_key not in pre_roll_allowed:
            raise InvalidAction("Primero hay que tirar los dados.")
        if card_key in ATTACK_CARDS:
            self._apply_attack_card(hand_index, card_key, args)
            return state
        if card_key == "reciclaje":
            market_index = int(args[0]) if args else 0
            if not 0 <= market_index < len(state.market):
                raise InvalidAction("Carta de mercado invalida.")
            old_card = player.hand.pop(hand_index)
            player.hand.append(state.market.pop(market_index))
            state.discard.append(old_card)
            self.fill_market_for_active_player(record_offer=True)
            state.used_card_this_turn = True
            state.assisted_turn = True
            state.message = "Reciclaje cambio una carta por el mercado."
            return state
        self._apply_card_effect(card_key, args)
        player.hand.pop(hand_index)
        state.discard.append(card_key)
        state.used_card_this_turn = True
        state.assisted_turn = True
        state.message = f"{CARD_DEFS[card_key].name} usada."
        return state

    def _die_arg(self, args, position=0):
        if len(args) <= position:
            raise InvalidAction("Falta indicar dado del 1 al 5.")
        index = int(args[position]) - 1
        if not 0 <= index < DICE_COUNT:
            raise InvalidAction("Dado invalido. Usa numeros del 1 al 5.")
        return index

    def _value_arg(self, args, position=0):
        if len(args) <= position:
            raise InvalidAction("Falta indicar valor del 1 al 6.")
        value = int(args[position])
        if not 1 <= value <= 6:
            raise InvalidAction("Valor invalido. Usa numeros del 1 al 6.")
        return value

    def _apply_card_effect(self, card_key, args):
        state = self.state

        if card_key == "ajuste_fino":
            index = self._die_arg(args, 0)
            direction = str(args[1]) if len(args) > 1 else "+"
            delta = -1 if direction in {"-", "-1", "bajar", "abajo"} else 1
            state.dice[index] = max(1, min(6, state.dice[index] + delta))
            return
        if card_key == "reintento":
            state.dice[self._die_arg(args, 0)] = self.random.randint(1, 6)
            return
        if card_key == "espejo":
            index = self._die_arg(args, 0)
            state.dice[index] = 7 - state.dice[index]
            return
        if card_key == "tirada_extra":
            state.max_rolls = max(state.max_rolls, state.rolls + 1, 4)
            return
        if card_key == "copia":
            source = self._die_arg(args, 0)
            target = self._die_arg(args, 1)
            if source == target:
                raise InvalidAction("Origen y destino deben ser dados distintos.")
            state.dice[target] = state.dice[source]
            return
        if card_key == "comodin":
            state.wildcard_indexes.add(self._die_arg(args, 0))
            return
        if card_key == "mano_estable":
            state.score_overrides["mano_estable"] = True
            return
        if card_key == "correccion_minima":
            if not self.apply_minimal_straight_correction():
                raise InvalidAction("No estas a un solo ajuste de una escalera.")
            state.score_overrides["correccion_minima"] = True
            return
        if card_key == "escudo":
            state.active_player.temp_shield = True
            state.active_player.temp_shield_until_turn = state.turn + len(state.players)
            return
        if card_key == "dado_maestro":
            index = self._die_arg(args, 0)
            state.dice[index] = self._value_arg(args, 1)
            return
        if card_key == "duplicador":
            state.score_multiplier = True
            return
        if card_key == "seguro":
            state.score_overrides["seguro"] = True
            return
        if card_key == "escalera_rota":
            state.score_overrides["escalera_rota"] = True
            return
        if card_key == "generala_falsa":
            state.score_overrides["generala_falsa"] = True
            return
        if card_key == "milagro_controlado":
            state.force_natural_score = True
            return
        if card_key == "rescate":
            category = str(args[0]) if args else ""
            if category not in dict(CATEGORIES):
                raise InvalidAction("Categoria invalida.")
            if state.active_player.sheet.get(category) != 0:
                raise InvalidAction("Rescate necesita una categoria tachada.")
            state.active_player.sheet[category] = None
            return
        if card_key == "no_cuenta":
            state.dice = [1, 2, 3, 4, 5]
            state.held = [False] * DICE_COUNT
            state.rolls = 0
            state.max_rolls = MAX_ROLLS
            state.no_coins_this_turn = True
            return
        if card_key == "dado_dorado":
            state.golden_indexes.add(self._die_arg(args, 0))
            return
        if card_key == "dado_duplicador":
            state.duplicator_indexes.add(self._die_arg(args, 0))
            return
        if card_key == "foco_numerico":
            state.score_overrides["foco_numerico"] = True
            return
        if card_key == "ancla":
            state.held = [True] * DICE_COUNT
            return
        if card_key == "apertura":
            state.held = [False] * DICE_COUNT
            return
        if card_key == "vision_clara":
            best_key, points = best_category_for_dice(state.dice, state.active_player, state.rolls, assisted=state.assisted_turn)
            state.message = f"Vision clara: {category_name(best_key)} por {points}."
            return
        if card_key in {"pulso_controlado", "ultima_oportunidad"}:
            for index, held in enumerate(state.held):
                if not held:
                    state.dice[index] = self.random.randint(1, 6)
            return

        raise InvalidAction(f"La carta {CARD_DEFS[card_key].name} todavia no esta disponible en online basico.")

    def _apply_attack_card(self, hand_index, card_key, args):
        state = self.state
        attacker = state.active_player
        target = state.players[(state.active_player_index + 1) % len(state.players)]
        if state.rolls > 0:
            raise InvalidAction("Los ataques solo se juegan antes de tirar.")
        if target.attacked_round == state.round_number:
            raise InvalidAction(f"{target.name} ya fue atacado en esta ronda.")
        if self.target_blocks_attack(target):
            target.attacked_round = state.round_number
            consumed = attacker.hand.pop(hand_index)
            state.discard.append(consumed)
            state.used_card_this_turn = True
            state.message = f"{target.name} bloqueo el ataque."
            return
        if card_key == "candado":
            category = str(args[0]) if args else ""
            if category not in dict(CATEGORIES):
                raise InvalidAction("Candado necesita una categoria.")
            target.pending_attack = {"type": "candado", "category": category}
        elif card_key == "robo":
            if target.hand:
                stolen = target.hand.pop(self.random.randrange(len(target.hand)))
                if len(attacker.hand) <= hand_index:
                    attacker.hand.append(stolen)
                elif len(attacker.hand) < hand_limit(attacker):
                    attacker.hand.append(stolen)
                else:
                    state.discard.append(stolen)
            state.message = f"Robo usado contra {target.name}."
        elif card_key == "intercambio":
            target.pending_attack = {"type": "intercambio"}
            add_coins(attacker, 1)
        else:
            target.pending_attack = {"type": card_key}
        target.attacked_round = state.round_number
        consumed = attacker.hand.pop(hand_index)
        state.discard.append(consumed)
        state.used_card_this_turn = True
        state.assisted_turn = True
        state.message = f"{CARD_DEFS[card_key].name} preparado contra {target.name}."

    def target_blocks_attack(self, target):
        if target.temp_shield:
            target.temp_shield = False
            target.temp_shield_until_turn = None
            return True
        if target.character_key == "defensivo" and not target.cancel_attack_used:
            target.cancel_attack_used = True
            return True
        return False

    def apply_minimal_straight_correction(self):
        for index, value in enumerate(self.state.dice):
            for delta in (-1, 1):
                new_value = value + delta
                if not 1 <= new_value <= 6:
                    continue
                candidate = self.state.dice[:]
                candidate[index] = new_value
                if is_straight(candidate):
                    self.state.dice = candidate
                    return True
        return False

    def apply_plus_after_roll(self):
        state = self.state
        if not state.plus_mode:
            return
        if state.rolls == 1 and state.pending_turn_attack:
            index = self.random.randrange(DICE_COUNT)
            state.dice[index] = self.random.randint(1, 6)
            state.pending_turn_attack.clear()
        if state.active_event_key == "caotica" and state.rolls == 2 and not state.score_overrides.get("caos_done"):
            state.score_overrides["caos_done"] = True
            if state.score_overrides.get("mano_estable"):
                return
            index = self.random.randrange(DICE_COUNT)
            old_value = state.dice[index]
            choices = [value for value in range(1, 7) if value != old_value]
            state.dice[index] = self.random.choice(choices)
            state.assisted_turn = True

    def _needs_forced_declaration(self):
        return any(item.get("category") is None for item in self.state.declarations)

    def set_forced_declaration(self, category):
        if category not in dict(CATEGORIES):
            raise InvalidAction("Categoria invalida.")
        for declaration in self.state.declarations:
            if declaration.get("category") is None:
                declaration["category"] = category
                self.state.message = f"Declaraste {category_name(category)}."
                return self.state
        raise InvalidAction("No hay declaracion pendiente.")

    def resolve_declarations(self, category):
        bonus = 0
        penalty = 0
        extra_coins = 0
        no_coins_fail = False
        for declaration in self.state.declarations:
            declared = declaration.get("category")
            if not declared:
                continue
            if declared == category:
                bonus += declaration.get("bonus", 0)
                extra_coins += declaration.get("coin", 0)
            else:
                penalty += declaration.get("penalty", 0)
                if declaration.get("no_coins_on_fail"):
                    no_coins_fail = True
        return bonus, penalty, extra_coins, no_coins_fail

    def award_plus_rewards(self, player, category, result, extra_coins):
        if self.state.no_coins_this_turn:
            player.previous_scored_assisted = result.assisted
            return
        earned = 0
        if result.tachada:
            earned += 2 if self.state.active_event_key == "recuperacion" else 1
            player.no_tach_streak = 0
        else:
            player.no_tach_streak += 1
            if category in NUMBER_CATEGORIES and result.points >= 15:
                earned += 1
            elif result.special:
                earned += 2 if category in ("generala", "generala_doble") and not result.false_generala else 1
        if not self.state.used_card_this_turn and player.character_key != "coleccionista" and result.points > 0 and player.coins <= 6:
            earned += 1
        if category == "full" and result.points > 0:
            player.full_count += 1
            if player.full_count == 2:
                earned += 2
        if result.natural and player.previous_scored_assisted:
            earned += 1
        earned = min(3, earned + extra_coins)
        add_coins(player, earned)
        player.previous_scored_assisted = result.assisted or (self.state.assisted_turn and result.base_points > 0)

    def use_ability(self, args):
        state = self.state
        player = state.active_player
        if not state.plus_mode:
            raise InvalidAction("Las habilidades solo existen en modo Plus.")
        if state.phase != "turn":
            raise InvalidAction("Las habilidades se usan durante el turno.")
        if state.active_event_key == "clasica":
            raise InvalidAction("Ronda clasica: no se pueden usar habilidades.")
        if state.used_ability_this_turn:
            raise InvalidAction("Ya usaste una habilidad este turno.")
        character = CHARACTER_BY_KEY[player.character_key]
        if character.passive:
            raise InvalidAction("Ese personaje tiene habilidad pasiva.")
        if character.once and player.ability_once_used:
            raise InvalidAction("Esa habilidad ya se uso.")
        if player.turns_played - player.ability_last_turn < character.cooldown:
            raise InvalidAction("La habilidad esta en cooldown.")
        key = character.key
        if key in {"matematico", "precavido", "ilusionista", "audaz"} and state.rolls == 0:
            raise InvalidAction("Primero hay que tirar.")
        if key == "apostador" and state.rolls != 0:
            raise InvalidAction("El Apostador declara antes de tirar.")
        player.ability_last_turn = player.turns_played
        state.used_ability_this_turn = True
        if key == "matematico":
            index = self._die_arg(args, 0)
            direction = str(args[1]) if len(args) > 1 else "+"
            state.dice[index] = max(1, min(6, state.dice[index] + (-1 if direction in {"-", "-1"} else 1)))
            state.assisted_turn = True
        elif key == "apostador":
            category = str(args[0]) if args else ""
            if category not in dict(CATEGORIES):
                raise InvalidAction("Declaracion invalida.")
            bonus = 10 if state.active_event_key == "apuestas" else 8
            penalty = 6 if state.active_event_key == "apuestas" else 5
            state.declarations.append({"source": "apostador", "category": category, "bonus": bonus, "penalty": penalty, "coin": 0, "no_coins_on_fail": False})
        elif key == "estratega":
            state.discard.extend(state.market)
            state.market = []
            self.fill_market_for_active_player(record_offer=True)
        elif key == "conservador":
            player.ability_once_used = True
            state.score_overrides["conservador"] = True
            state.assisted_turn = True
        elif key in {"precavido", "audaz"}:
            state.dice[self._die_arg(args, 0)] = self.random.randint(1, 6)
            state.assisted_turn = True
        elif key == "ambicioso":
            state.score_overrides["ambicioso"] = True
            state.message = "Todo o nada activo para la proxima declaracion."
        elif key == "tecnico":
            best_key, points = best_category_for_dice(state.dice, player, state.rolls, assisted=state.assisted_turn)
            state.message = f"Optimizacion: {category_name(best_key)} por {points}."
        elif key == "ilusionista":
            index = self._die_arg(args, 0)
            state.dice[index] = invert_die(state.dice[index])
            state.assisted_turn = True
        elif key == "crupier":
            if state.market:
                state.discard.append(state.market.pop(0))
                self.fill_market_for_active_player(record_offer=True)
        else:
            state.message = f"{character.name}: habilidad aplicada."
        return state

    def use_event(self, args):
        if self.state.active_event_key != "espejo":
            raise InvalidAction("Este evento no tiene accion manual.")
        if self.state.event_action_used:
            raise InvalidAction("La accion del evento ya se uso.")
        if self.state.rolls == 0:
            raise InvalidAction("Primero hay que tirar.")
        index = self._die_arg(args, 0)
        self.state.dice[index] = invert_die(self.state.dice[index])
        self.state.event_action_used = True
        self.state.assisted_turn = True
        self.state.message = "Ronda espejo: dado invertido."
        return self.state

    def buy_market_card(self, index):
        state = self.state
        player = state.active_player
        if state.phase != "buy":
            raise InvalidAction("Solo se compra en fase de compra.")
        if state.active_event_key == "austera":
            raise InvalidAction("Ronda austera: no se puede comprar.")
        if player.market_blocked:
            player.market_blocked = False
            raise InvalidAction("Veto de mercado: no podes comprar este turno.")
        if not 0 <= index < len(state.market):
            raise InvalidAction("Carta de mercado invalida.")
        if len(player.hand) >= hand_limit(player):
            raise InvalidAction("Mano llena.")
        card_key = state.market[index]
        discount_available = state.active_event_key == "descuento" and state.active_player_index not in state.discount_buyers
        cost = display_card_cost(card_key, player, state.active_event_key, discount_available)
        if player.coins < cost:
            raise InvalidAction("Monedas insuficientes.")
        player.coins -= cost
        player.hand.append(card_key)
        if state.active_event_key == "descuento":
            state.discount_buyers.add(state.active_player_index)
        if player.character_key == "suertudo" and CARD_DEFS[card_key].cost >= 4:
            add_coins(player, 1)
        state.market.pop(index)
        self.fill_market_for_active_player(record_offer=True)
        state.message = f"{CARD_DEFS[card_key].name} comprada."
        return self.end_buy_phase()

    def renew_market_card(self, index):
        state = self.state
        player = state.active_player
        if state.phase != "buy":
            raise InvalidAction("Solo se renueva en fase de compra.")
        if state.active_event_key == "austera":
            raise InvalidAction("Ronda austera: no se puede comprar ni renovar.")
        if not 0 <= index < len(state.market):
            raise InvalidAction("Carta de mercado invalida.")
        if player.coins < 1:
            raise InvalidAction("Renovar cuesta 1 moneda.")
        player.coins -= 1
        state.discard.append(state.market.pop(index))
        self.fill_market_for_active_player(record_offer=True)
        state.message = "Mercado renovado."
        return state

    def discard_hand_card(self, index):
        state = self.state
        player = state.active_player
        if state.phase != "buy":
            raise InvalidAction("Solo se descarta en fase de compra.")
        if not 0 <= index < len(player.hand):
            raise InvalidAction("Carta de mano invalida.")
        state.discard.append(player.hand.pop(index))
        state.message = "Carta descartada."
        return state

    def end_buy_phase(self):
        self.state.turn += 1
        self.state.phase = "turn"
        self.state.dice = [1, 2, 3, 4, 5]
        self.state.held = [False] * DICE_COUNT
        self.state.rolls = 0
        self.state.max_rolls = MAX_ROLLS
        self.state.assisted_turn = False
        self.state.used_card_this_turn = False
        self.state.wildcard_indexes.clear()
        self.state.golden_indexes.clear()
        self.state.duplicator_indexes.clear()
        self.state.score_multiplier = False
        self.state.force_natural_score = False
        self.state.score_overrides.clear()
        self.state.declarations.clear()
        self.state.pending_turn_attack.clear()
        self.state.no_coins_this_turn = False
        self.state.event_action_used = False
        self.state.used_ability_this_turn = False
        if self.state.complete:
            self.state.phase = "end"
            self.state.message = "Partida finalizada."
            return self.state
        if self.state.plus_mode:
            self.begin_turn(grant_start_coin=True)
        self.state.message = f"Turno de {self.state.active_player.name}."
        return self.state
