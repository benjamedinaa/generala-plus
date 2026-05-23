import io
import unittest

from generala_plus.core.actions import BUY_MARKET_CARD, RELEASE_ALL, ROLL_DICE, SCORE_CATEGORY, TOGGLE_HOLD, USE_CARD
from generala_plus.core.engine import GeneralaEngine
from generala_plus.net.commands import format_state, parse_command
from generala_plus.net.protocol import ACTION, Message, action_from_message, action_message
from generala_plus.net.wire import read_message, send_message


class OnlineModeTests(unittest.TestCase):
    def test_parse_basic_turn_commands(self):
        self.assertEqual(parse_command("tirar", 0).kind, ROLL_DICE)
        self.assertEqual(parse_command("roll", 0).kind, ROLL_DICE)

        hold = parse_command("hold 3", 1)
        self.assertEqual(hold.kind, TOGGLE_HOLD)
        self.assertEqual(hold.player_index, 1)
        self.assertEqual(hold.payload["index"], 2)

        self.assertEqual(parse_command("soltar", 0).kind, RELEASE_ALL)

    def test_parse_score_and_buy_commands(self):
        score = parse_command("anotar generala doble", 0)
        self.assertEqual(score.kind, SCORE_CATEGORY)
        self.assertEqual(score.payload["category"], "generala_doble")

        buy = parse_command("comprar 2", 0)
        self.assertEqual(buy.kind, BUY_MARKET_CARD)
        self.assertEqual(buy.payload["index"], 1)

        use = parse_command("usar 1 3 +", 0)
        self.assertEqual(use.kind, USE_CARD)
        self.assertEqual(use.payload["hand_index"], 0)
        self.assertEqual(use.payload["args"], ["3", "+"])

    def test_protocol_action_round_trip(self):
        action = parse_command("anotar full", 0)
        message = action_message(action)
        restored = action_from_message(Message.from_json(message.to_json()))
        self.assertEqual(message.type, ACTION)
        self.assertEqual(restored.kind, SCORE_CATEGORY)
        self.assertEqual(restored.payload["category"], "full")

    def test_wire_json_line_round_trip(self):
        buffer = io.StringIO()
        send_message(buffer, Message("info", {"text": "mesa lista"}))
        buffer.seek(0)
        restored = read_message(buffer)
        self.assertEqual(restored.type, "info")
        self.assertEqual(restored.payload["text"], "mesa lista")

    def test_online_state_hides_rival_hand(self):
        engine = GeneralaEngine.new_game(["Ana", "Bruno"], seed=4)
        engine.state.players[0].hand = ["ajuste_fino"]
        engine.state.players[1].hand = ["dado_maestro"]

        state_for_ana = engine.state.to_dict(viewer_index=0)
        rendered = format_state(state_for_ana, 0)

        self.assertIn("Ana", rendered)
        self.assertIn("Bruno", rendered)
        self.assertIn("Ajuste fino", rendered)
        self.assertNotIn("dado_maestro", rendered)
        self.assertIn("1 carta(s)", rendered)


if __name__ == "__main__":
    unittest.main()
