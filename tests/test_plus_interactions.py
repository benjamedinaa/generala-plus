import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from generala_plus.pygame_app import Generala
from generala_plus.rules import CATEGORIES


class PlusInteractionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def make_app(self):
        app = Generala()
        app.start_game()
        return app

    def test_right_click_on_die_releases_all_held_dice(self):
        app = self.make_app()
        app.rolls = 1
        app.held = [True, False, True, False, True]
        rect = app.die_rect(0)
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 3, "pos": rect.center})

        app.handle_event(event)

        self.assertEqual(app.held, [False] * 5)

    def test_buy_market_card_adds_to_hand_and_advances_turn(self):
        app = self.make_app()
        player = app.current_player()
        player.coins = 10
        player.hand.clear()
        app.market = ["ajuste_fino", "tirada_extra", "dado_maestro"]
        app.phase = "buy"
        starting_turn = app.turn

        app.buy_market_card(0)
        app.update(1.0)

        self.assertIn("ajuste_fino", player.hand)
        self.assertEqual(app.turn, starting_turn + 1)
        self.assertEqual(app.phase, "turn")
        self.assertEqual(len(app.market), 3)

    def test_market_has_no_duplicates_and_remembers_player_offers(self):
        app = self.make_app()
        player = app.current_player()
        player.offered_market_cards.update({"ajuste_fino", "reintento", "espejo"})
        app.market = ["ajuste_fino", "copia", "copia"]
        app.deck = ["ajuste_fino", "reintento", "tirada_extra", "dado_maestro", "pulso_controlado", "vision_clara"]

        app.prepare_market_for_player(player, record_offer=True)

        self.assertEqual(len(app.market), 3)
        self.assertEqual(len(set(app.market)), 3)
        self.assertTrue(set(app.market).isdisjoint({"ajuste_fino", "reintento", "espejo"}))
        self.assertTrue(set(app.market).issubset(player.offered_market_cards))

    def test_attack_card_sets_pending_attack_before_rival_turn(self):
        app = self.make_app()
        attacker = app.current_player()
        target = app.opponent_player()
        attacker.hand = ["mano_pesada"]
        app.rolls = 0

        app.activate_card(0)

        self.assertTrue(app.card_used_this_turn)
        self.assertEqual(target.pending_attack.get("type"), "mano_pesada")
        self.assertEqual(attacker.hand, [])

    def test_smoke_draws_main_screens_and_help_tabs(self):
        app = self.make_app()
        app.draw()

        app.rolls = 2
        app.dice = [6, 6, 6, 2, 5]
        app.held = [True, True, True, False, False]
        app.players[0].hand = ["ajuste_fino", "dado_maestro", "sabotaje"]
        app.market = ["tirada_extra", "dado_dorado", "candado"]
        app.mouse_pos = app.market_card_rects()[1].center
        app.draw()

        app.phase = "buy"
        app.mouse_pos = app.market_card_rects()[0].center
        app.draw()

        app.paused = True
        app.mouse_pos = app.pause_info_button.rect.center
        app.draw()
        app.show_sound_settings = True
        app.mouse_pos = app.pause_sfx_up_button.rect.center
        app.draw()
        app.paused = False

        app.show_help = True
        for tab in app.info_scroll:
            app.info_tab = tab
            app.info_scroll[tab] = 120
            app.draw()
        app.show_help = False

        for player in app.players:
            for key, _ in CATEGORIES:
                player.sheet[key] = 0
        app.state = "end"
        app.draw()


if __name__ == "__main__":
    unittest.main()
