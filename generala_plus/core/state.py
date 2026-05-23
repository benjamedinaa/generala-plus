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
    market_blocked: bool = False

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
            "temp_shield": self.temp_shield,
            "temp_shield_until_turn": self.temp_shield_until_turn,
            "cancel_attack_used": self.cancel_attack_used,
            "attacked_round": self.attacked_round,
            "pending_attack": dict(self.pending_attack),
            "blocked_category": self.blocked_category,
            "turns_played": self.turns_played,
            "ability_last_turn": self.ability_last_turn,
            "ability_once_used": self.ability_once_used,
            "no_tach_streak": self.no_tach_streak,
            "full_count": self.full_count,
            "previous_scored_assisted": self.previous_scored_assisted,
            "market_blocked": self.market_blocked,
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
            temp_shield=bool(data.get("temp_shield", False)),
            temp_shield_until_turn=data.get("temp_shield_until_turn"),
            cancel_attack_used=bool(data.get("cancel_attack_used", False)),
            attacked_round=int(data.get("attacked_round", 0)),
            pending_attack=dict(data.get("pending_attack", {})),
            blocked_category=data.get("blocked_category"),
            turns_played=int(data.get("turns_played", 0)),
            ability_last_turn=int(data.get("ability_last_turn", -999)),
            ability_once_used=bool(data.get("ability_once_used", False)),
            no_tach_streak=int(data.get("no_tach_streak", 0)),
            full_count=int(data.get("full_count", 0)),
            previous_scored_assisted=bool(data.get("previous_scored_assisted", False)),
            market_blocked=bool(data.get("market_blocked", False)),
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
    active_event_round: int = 0
    message: str = "Partida lista."
    assisted_turn: bool = False
    used_card_this_turn: bool = False
    used_ability_this_turn: bool = False
    event_action_used: bool = False
    no_coins_this_turn: bool = False
    declarations: list = field(default_factory=list)
    pending_turn_attack: dict = field(default_factory=dict)
    golden_bonus_used_round: int = 0
    discount_buyers: set = field(default_factory=set)
    round_scores: dict = field(default_factory=dict)
    wildcard_indexes: set = field(default_factory=set)
    golden_indexes: set = field(default_factory=set)
    duplicator_indexes: set = field(default_factory=set)
    score_multiplier: bool = False
    force_natural_score: bool = False
    score_overrides: dict = field(default_factory=dict)
    history: list = field(default_factory=list)
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
            "active_event_round": self.active_event_round,
            "message": self.message,
            "assisted_turn": self.assisted_turn,
            "used_card_this_turn": self.used_card_this_turn,
            "used_ability_this_turn": self.used_ability_this_turn,
            "event_action_used": self.event_action_used,
            "no_coins_this_turn": self.no_coins_this_turn,
            "declarations": [dict(item) for item in self.declarations],
            "pending_turn_attack": dict(self.pending_turn_attack),
            "golden_bonus_used_round": self.golden_bonus_used_round,
            "discount_buyers": sorted(self.discount_buyers),
            "round_scores": {str(key): dict(value) for key, value in self.round_scores.items()},
            "wildcard_indexes": sorted(self.wildcard_indexes),
            "golden_indexes": sorted(self.golden_indexes),
            "duplicator_indexes": sorted(self.duplicator_indexes),
            "score_multiplier": self.score_multiplier,
            "force_natural_score": self.force_natural_score,
            "score_overrides": dict(self.score_overrides),
            "history": list(self.history[-10:]),
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
            active_event_round=int(data.get("active_event_round", 0)),
            message=str(data.get("message", "Partida lista.")),
            assisted_turn=bool(data.get("assisted_turn", False)),
            used_card_this_turn=bool(data.get("used_card_this_turn", False)),
            used_ability_this_turn=bool(data.get("used_ability_this_turn", False)),
            event_action_used=bool(data.get("event_action_used", False)),
            no_coins_this_turn=bool(data.get("no_coins_this_turn", False)),
            declarations=[dict(item) for item in data.get("declarations", [])],
            pending_turn_attack=dict(data.get("pending_turn_attack", {})),
            golden_bonus_used_round=int(data.get("golden_bonus_used_round", 0)),
            discount_buyers=set(data.get("discount_buyers", [])),
            round_scores={int(key): dict(value) for key, value in data.get("round_scores", {}).items()},
            wildcard_indexes=set(data.get("wildcard_indexes", [])),
            golden_indexes=set(data.get("golden_indexes", [])),
            duplicator_indexes=set(data.get("duplicator_indexes", [])),
            score_multiplier=bool(data.get("score_multiplier", False)),
            force_natural_score=bool(data.get("force_natural_score", False)),
            score_overrides=dict(data.get("score_overrides", {})),
            history=list(data.get("history", [])),
            schema_version=int(data.get("schema_version", 1)),
        )
