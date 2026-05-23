from dataclasses import dataclass, field

from ..rules import CATEGORIES, PLUS_STARTING_COINS


def fresh_sheet():
    return {key: None for key, _ in CATEGORIES}


@dataclass
class PlayerState:
    name: str
    character_key: str = "matematico"
    sheet: dict = field(default_factory=fresh_sheet)
    coins: int = PLUS_STARTING_COINS
    hand: list = field(default_factory=list)
    offered_market_cards: set = field(default_factory=set)
    bonus_total: int = 0
    generala_valid: bool = False

    @property
    def total(self):
        return sum(value for value in self.sheet.values() if value is not None) + self.bonus_total

    @property
    def complete(self):
        return all(value is not None for value in self.sheet.values())

    def to_dict(self, reveal_hand=True):
        return {
            "name": self.name,
            "character_key": self.character_key,
            "sheet": dict(self.sheet),
            "coins": self.coins,
            "hand": list(self.hand) if reveal_hand else {"count": len(self.hand)},
            "offered_market_cards": sorted(self.offered_market_cards),
            "bonus_total": self.bonus_total,
            "generala_valid": self.generala_valid,
            "total": self.total,
            "complete": self.complete,
        }

    @classmethod
    def from_dict(cls, data):
        hand = data.get("hand", [])
        if isinstance(hand, dict):
            hand = []
        return cls(
            name=str(data["name"]),
            character_key=str(data.get("character_key", "matematico")),
            sheet={key: data.get("sheet", {}).get(key) for key, _ in CATEGORIES},
            coins=int(data.get("coins", PLUS_STARTING_COINS)),
            hand=list(hand),
            offered_market_cards=set(data.get("offered_market_cards", [])),
            bonus_total=int(data.get("bonus_total", 0)),
            generala_valid=bool(data.get("generala_valid", False)),
        )


@dataclass
class GameState:
    players: list
    plus_mode: bool = True
    turn: int = 0
    phase: str = "turn"
    dice: list = field(default_factory=lambda: [1, 2, 3, 4, 5])
    held: list = field(default_factory=lambda: [False] * 5)
    rolls: int = 0
    max_rolls: int = 3
    deck: list = field(default_factory=list)
    market: list = field(default_factory=list)
    discard: list = field(default_factory=list)
    active_event_key: str = None
    message: str = "Partida lista."
    assisted_turn: bool = False
    schema_version: int = 1

    @property
    def active_player_index(self):
        return self.turn % len(self.players)

    @property
    def round_number(self):
        return self.turn // len(self.players) + 1

    @property
    def active_player(self):
        return self.players[self.active_player_index]

    @property
    def complete(self):
        return all(player.complete for player in self.players)

    def to_dict(self, viewer_index=None):
        return {
            "schema_version": self.schema_version,
            "plus_mode": self.plus_mode,
            "turn": self.turn,
            "phase": self.phase,
            "dice": list(self.dice),
            "held": list(self.held),
            "rolls": self.rolls,
            "max_rolls": self.max_rolls,
            "deck_count": len(self.deck),
            "market": list(self.market),
            "discard_count": len(self.discard),
            "active_event_key": self.active_event_key,
            "message": self.message,
            "assisted_turn": self.assisted_turn,
            "round_number": self.round_number,
            "active_player_index": self.active_player_index,
            "players": [
                player.to_dict(reveal_hand=viewer_index is None or index == viewer_index)
                for index, player in enumerate(self.players)
            ],
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            players=[PlayerState.from_dict(player) for player in data["players"]],
            plus_mode=bool(data.get("plus_mode", True)),
            turn=int(data.get("turn", 0)),
            phase=str(data.get("phase", "turn")),
            dice=list(data.get("dice", [1, 2, 3, 4, 5])),
            held=list(data.get("held", [False] * 5)),
            rolls=int(data.get("rolls", 0)),
            max_rolls=int(data.get("max_rolls", 3)),
            deck=list(data.get("deck", [])),
            market=list(data.get("market", [])),
            discard=list(data.get("discard", [])),
            active_event_key=data.get("active_event_key"),
            message=str(data.get("message", "Partida lista.")),
            assisted_turn=bool(data.get("assisted_turn", False)),
            schema_version=int(data.get("schema_version", 1)),
        )
