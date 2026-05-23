import unittest

from generala_plus.core import Action, GameState, GeneralaEngine
from generala_plus.core.actions import BUY_MARKET_CARD, RELEASE_ALL, ROLL_DICE, SCORE_CATEGORY, TOGGLE_HOLD
from generala_plus.net.protocol import Message, action_from_message, action_message


class CoreEngineTest(unittest.TestCase):
    def test_state_serializes_and_hides_opponent_hand(self):
        engine = GeneralaEngine.new_game(["Ana", "Bruno"], seed=7)
        engine.state.players[0].hand = ["ajuste_fino"]
        engine.state.players[1].hand = ["dado_maestro", "escudo"]

        public = engine.state.to_dict(viewer_index=0)
        restored = GameState.from_dict(engine.state.to_dict())

        self.assertEqual(public["players"][0]["hand"], ["ajuste_fino"])
        self.assertEqual(public["players"][1]["hand"], {"count": 2})
        self.assertEqual(restored.players[0].name, "Ana")
        self.assertEqual(restored.market, engine.state.market)

    def test_actions_advance_basic_turn_flow(self):
        engine = GeneralaEngine.new_game(["Ana", "Bruno"], seed=3)

        engine.apply(Action(ROLL_DICE, 0))
        self.assertEqual(engine.state.rolls, 1)

        engine.apply(Action(TOGGLE_HOLD, 0, {"index": 0}))
        self.assertTrue(engine.state.held[0])

        engine.apply(Action(RELEASE_ALL, 0))
        self.assertFalse(any(engine.state.held))

        engine.state.dice = [1, 1, 2, 3, 4]
        engine.apply(Action(SCORE_CATEGORY, 0, {"category": "unos"}))
        self.assertEqual(engine.state.phase, "buy")

    def test_market_is_unique_for_active_player(self):
        engine = GeneralaEngine.new_game(["Ana", "Bruno"], seed=9)
        player = engine.state.active_player
        player.offered_market_cards.update({"ajuste_fino", "reintento", "espejo"})
        engine.state.market = ["ajuste_fino", "copia", "copia"]
        engine.state.deck = ["ajuste_fino", "reintento", "vision_clara", "dado_maestro", "pulso_controlado"]

        engine.fill_market_for_active_player(record_offer=True)

        self.assertEqual(len(engine.state.market), 3)
        self.assertEqual(len(set(engine.state.market)), 3)
        self.assertTrue(set(engine.state.market).isdisjoint({"ajuste_fino", "reintento", "espejo"}))

    def test_buy_action_is_authoritative(self):
        engine = GeneralaEngine.new_game(["Ana", "Bruno"], seed=11)
        player = engine.state.active_player
        player.coins = 10
        engine.state.phase = "buy"
        card = engine.state.market[0]

        engine.apply(Action(BUY_MARKET_CARD, 0, {"index": 0}))

        self.assertIn(card, player.hand)
        self.assertEqual(engine.state.active_player_index, 1)
        self.assertEqual(engine.state.phase, "turn")

    def test_protocol_roundtrip(self):
        original = Action(ROLL_DICE, 1, {"example": True})
        message = action_message(original)
        restored_message = Message.from_json(message.to_json())
        restored_action = action_from_message(restored_message)

        self.assertEqual(restored_action.to_dict(), original.to_dict())


if __name__ == "__main__":
    unittest.main()
