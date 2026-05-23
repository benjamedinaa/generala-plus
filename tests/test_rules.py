import unittest

from generala_plus.rules import (
    CLASSIC_EVENT,
    CARD_DEFS,
    DECK_SPEC,
    PLUS_MAX_COINS,
    PLUS_STARTING_COINS,
    Player,
    add_coins,
    choose_round_event,
    display_card_cost,
    evaluate_plus_score,
    hand_limit,
    score_category,
)


class RulesTest(unittest.TestCase):
    def test_assisted_scores_are_lower_than_natural_scores(self):
        player = Player("Ana")

        natural = evaluate_plus_score("poker", [5, 5, 5, 5, 2], 3, player)
        assisted = evaluate_plus_score("poker", [5, 5, 5, 5, 2], 3, player, assisted=True)

        self.assertEqual(natural.points, 40)
        self.assertEqual(assisted.points, 36)
        self.assertTrue(natural.natural)
        self.assertTrue(assisted.assisted)

    def test_served_only_counts_without_assistance(self):
        player = Player("Ana")

        served = evaluate_plus_score("generala", [6, 6, 6, 6, 6], 1, player)
        assisted = evaluate_plus_score("generala", [6, 6, 6, 6, 6], 1, player, assisted=True)

        self.assertEqual(served.points, 60)
        self.assertTrue(served.served)
        self.assertEqual(assisted.points, 45)
        self.assertFalse(assisted.served)

    def test_generala_falsa_does_not_enable_double_generala(self):
        player = Player("Bruno")

        false_generala = evaluate_plus_score(
            "generala",
            [4, 4, 4, 4, 2],
            3,
            player,
            score_overrides={"generala_falsa": True},
        )
        player.sheet["generala"] = false_generala.points
        player.generala_valid = False

        double = evaluate_plus_score("generala_doble", [4, 4, 4, 4, 4], 3, player)

        self.assertEqual(false_generala.points, 35)
        self.assertTrue(false_generala.false_generala)
        self.assertEqual(double.points, 0)

    def test_real_generala_enables_double_generala(self):
        player = Player("Bruno")
        player.sheet["generala"] = 50
        player.generala_valid = True

        double = evaluate_plus_score("generala_doble", [4, 4, 4, 4, 4], 3, player)

        self.assertEqual(double.points, 100)

    def test_five_equal_dice_do_not_count_as_poker_or_full(self):
        player = Player("Ana")

        poker = evaluate_plus_score("poker", [6, 6, 6, 6, 6], 3, player)
        full = evaluate_plus_score("full", [6, 6, 6, 6, 6], 3, player)
        classic_poker = score_category("poker", [6, 6, 6, 6, 6], 3, player.sheet)

        self.assertEqual(poker.points, 0)
        self.assertEqual(full.points, 0)
        self.assertEqual(classic_poker, 0)

    def test_wildcard_generala_does_not_downgrade_to_poker(self):
        player = Player("Ana")

        poker = evaluate_plus_score("poker", [6, 6, 6, 6, 6], 3, player, assisted=True, wildcard_indexes={4})
        generala = evaluate_plus_score("generala", [6, 6, 6, 6, 6], 3, player, assisted=True, wildcard_indexes={4})

        self.assertEqual(poker.points, 0)
        self.assertEqual(generala.points, 45)

    def test_coin_limit_and_hand_limit_personalities(self):
        normal = Player("Normal")
        collector = Player("Coleccionista", character_key="coleccionista")
        aggressive = Player("Agresivo", character_key="agresivo")

        normal.coins = 9
        earned = add_coins(normal, 5)

        self.assertEqual(earned, 1)
        self.assertEqual(normal.coins, PLUS_MAX_COINS)
        self.assertEqual(hand_limit(normal), 3)
        self.assertEqual(hand_limit(collector), 4)
        self.assertEqual(hand_limit(aggressive), 2)
        self.assertEqual(Player("Nuevo").coins, PLUS_STARTING_COINS)

    def test_plus_economy_is_tighter_for_power_cards(self):
        self.assertEqual(PLUS_STARTING_COINS, 1)
        self.assertGreaterEqual(CARD_DEFS["dado_maestro"].cost, 6)
        self.assertGreaterEqual(CARD_DEFS["generala_falsa"].cost, 7)
        self.assertGreaterEqual(CARD_DEFS["sabotaje"].cost, 5)

    def test_aggressive_attack_discount_and_round_schedule(self):
        player = Player("Agresivo", character_key="agresivo")

        self.assertEqual(display_card_cost("sabotaje", player), CARD_DEFS["sabotaje"].cost - 1)
        self.assertIsNone(choose_round_event(1))
        self.assertEqual(choose_round_event(4), CLASSIC_EVENT)

    def test_deck_contains_more_common_than_strong_cards(self):
        common = sum(copies for key, copies in DECK_SPEC.items() if CARD_DEFS[key].tier == "comun")
        medium = sum(copies for key, copies in DECK_SPEC.items() if CARD_DEFS[key].tier == "media")
        strong = sum(copies for key, copies in DECK_SPEC.items() if CARD_DEFS[key].tier == "fuerte")

        self.assertGreater(common, medium)
        self.assertGreater(medium, strong)


if __name__ == "__main__":
    unittest.main()
