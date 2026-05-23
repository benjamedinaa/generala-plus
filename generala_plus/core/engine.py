import random

from ..rules import (
    CARD_DEFS,
    PLUS_MARKET_SIZE,
    add_coins,
    build_deck,
    display_card_cost,
    evaluate_plus_score,
    hand_limit,
    score_category as classic_score_category,
)
from ..settings import DICE_COUNT, MAX_ROLLS
from .actions import BUY_MARKET_CARD, PASS_BUY, RELEASE_ALL, ROLL_DICE, SCORE_CATEGORY, TOGGLE_HOLD
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
        if action.kind == PASS_BUY:
            return self.end_buy_phase()
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

    def roll_dice(self):
        if self.state.phase != "turn":
            raise InvalidAction("Solo se puede tirar en fase de turno.")
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
            raise InvalidAction("Primero hay que tirar.")
        if player.sheet.get(category) is not None:
            raise InvalidAction("Categoria ya usada.")
        if self.state.plus_mode:
            result = evaluate_plus_score(category, self.state.dice, self.state.rolls, player, assisted=self.state.assisted_turn)
            points = result.points
            if category == "generala" and result.base_points > 0 and not result.false_generala:
                player.generala_valid = True
        else:
            points = classic_score_category(category, self.state.dice, self.state.rolls, player.sheet)
        player.sheet[category] = points
        self.state.message = f"{category}: {points} puntos."
        if self.state.complete:
            self.state.phase = "end"
            return self.state
        if self.state.plus_mode:
            self.state.phase = "buy"
        else:
            self.end_buy_phase()
        return self.state

    def buy_market_card(self, index):
        state = self.state
        player = state.active_player
        if state.phase != "buy":
            raise InvalidAction("Solo se compra en fase de compra.")
        if not 0 <= index < len(state.market):
            raise InvalidAction("Carta de mercado invalida.")
        if len(player.hand) >= hand_limit(player):
            raise InvalidAction("Mano llena.")
        card_key = state.market[index]
        cost = display_card_cost(card_key, player, state.active_event_key)
        if player.coins < cost:
            raise InvalidAction("Monedas insuficientes.")
        player.coins -= cost
        player.hand.append(card_key)
        state.market.pop(index)
        self.fill_market_for_active_player(record_offer=True)
        state.message = f"{CARD_DEFS[card_key].name} comprada."
        return self.end_buy_phase()

    def end_buy_phase(self):
        self.state.turn += 1
        self.state.phase = "turn"
        self.state.dice = [1, 2, 3, 4, 5]
        self.state.held = [False] * DICE_COUNT
        self.state.rolls = 0
        self.state.assisted_turn = False
        if self.state.complete:
            self.state.phase = "end"
            self.state.message = "Partida finalizada."
            return self.state
        if self.state.plus_mode:
            add_coins(self.state.active_player, 1)
            self.fill_market_for_active_player(record_offer=True)
        self.state.message = f"Turno de {self.state.active_player.name}."
        return self.state
