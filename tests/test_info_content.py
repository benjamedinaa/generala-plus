import unittest

from generala_plus.info_content import (
    CHARACTER_SHORT_TEXT,
    INFO_TABS,
    card_detail,
    character_detail,
    event_detail,
    info_items,
)
from generala_plus.rules import CARD_DEFS, CHARACTERS, CLASSIC_EVENT, ROUND_EVENTS


class InfoContentTest(unittest.TestCase):
    def test_every_card_character_and_event_has_detailed_info(self):
        for key, card in CARD_DEFS.items():
            detail = card_detail(key, card)
            self.assertIn("Costo:", detail)
            self.assertGreater(len(detail), 80)

        for character in CHARACTERS:
            self.assertIn(character.key, CHARACTER_SHORT_TEXT)
            detail = character_detail(character)
            self.assertIn(character.ability, detail)
            self.assertGreater(len(detail), 80)

        for event in [CLASSIC_EVENT, *ROUND_EVENTS]:
            detail = event_detail(event)
            self.assertIn(event.text.split()[0], detail)
            self.assertGreater(len(detail), 35)

    def test_info_tabs_are_populated(self):
        self.assertEqual(
            INFO_TABS,
            ["CLASICO", "PLUS", "CARTAS", "PERSONAJES", "EVENTOS", "CONTROLES", "PLANILLA", "ESTADOS"],
        )
        for tab in INFO_TABS:
            items = info_items(tab)
            self.assertGreater(len(items), 0)
            for icon_key, heading, detail in items:
                self.assertIsInstance(icon_key, str)
                self.assertIsInstance(heading, str)
                self.assertIsInstance(detail, str)
                self.assertTrue(heading.strip())
                self.assertTrue(detail.strip())


if __name__ == "__main__":
    unittest.main()
