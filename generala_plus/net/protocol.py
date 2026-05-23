import json
from dataclasses import dataclass, field

from ..core.actions import Action


HELLO = "hello"
CREATE_ROOM = "create_room"
JOIN_ROOM = "join_room"
PLAYER_READY = "player_ready"
ACTION = "action"
STATE = "state"
ERROR = "error"
PING = "ping"
PONG = "pong"
WELCOME = "welcome"
INFO = "info"


@dataclass
class Message:
    type: str
    payload: dict = field(default_factory=dict)

    def to_dict(self):
        return {"type": self.type, "payload": dict(self.payload)}

    def to_json(self):
        return json.dumps(self.to_dict(), separators=(",", ":"), ensure_ascii=True)

    @classmethod
    def from_dict(cls, data):
        return cls(type=str(data["type"]), payload=dict(data.get("payload", {})))

    @classmethod
    def from_json(cls, raw):
        return cls.from_dict(json.loads(raw))


def action_message(action):
    return Message(ACTION, {"action": action.to_dict()})


def action_from_message(message):
    if message.type != ACTION:
        raise ValueError("El mensaje no contiene una accion.")
    return Action.from_dict(message.payload["action"])
