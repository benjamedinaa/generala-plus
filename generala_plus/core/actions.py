from dataclasses import dataclass, field


ROLL_DICE = "roll_dice"
TOGGLE_HOLD = "toggle_hold"
RELEASE_ALL = "release_all"
SCORE_CATEGORY = "score_category"
BUY_MARKET_CARD = "buy_market_card"
PASS_BUY = "pass_buy"
USE_CARD = "use_card"
USE_ABILITY = "use_ability"
USE_EVENT = "use_event"
RENEW_MARKET_CARD = "renew_market_card"
DISCARD_HAND_CARD = "discard_hand_card"


@dataclass
class Action:
    """Serializable player intent.

    Online clients should send actions, not mutated game state. A future server
    can validate and apply these same actions with an authoritative engine.
    """

    kind: str
    player_index: int
    payload: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "kind": self.kind,
            "player_index": self.player_index,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            kind=str(data["kind"]),
            player_index=int(data["player_index"]),
            payload=dict(data.get("payload", {})),
        )
