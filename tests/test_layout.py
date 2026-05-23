import unittest

import pygame

from generala_plus.rules import PLUS_HAND_LIMIT, PLUS_MARKET_SIZE
from generala_plus.settings import (
    DIE_SIZE,
    DIE_GAP,
    DICE_TOP,
    HAND_CARD_H,
    HAND_CARD_W,
    LEFT_PANEL,
    MARKET_CARD_H,
    MARKET_CARD_W,
    PLAY_BANNER_RECT,
    RIGHT_PANEL,
    SCORE_SHEET_RECT,
)


class LayoutTest(unittest.TestCase):
    def test_banner_dice_and_actions_have_air(self):
        banner = pygame.Rect(PLAY_BANNER_RECT)
        dice = pygame.Rect(376, DICE_TOP, DIE_SIZE * 5 + DIE_GAP * 4, DIE_SIZE)
        roll = pygame.Rect(500, 340, 280, 56)
        secondary = pygame.Rect(397, 412, 486, 42)
        score = pygame.Rect(SCORE_SHEET_RECT)

        self.assertGreaterEqual(dice.top - banner.bottom, 14)
        self.assertGreaterEqual(roll.top - dice.bottom, 24)
        self.assertGreaterEqual(secondary.top - roll.bottom, 16)
        self.assertGreaterEqual(score.top - secondary.bottom, 26)

    def test_market_cards_fit_right_panel(self):
        panel = pygame.Rect(RIGHT_PANEL)
        cards = [
            pygame.Rect(995, 326 + index * 106, MARKET_CARD_W, MARKET_CARD_H)
            for index in range(PLUS_MARKET_SIZE)
        ]

        for card in cards:
            self.assertTrue(panel.contains(card))
        self.assertGreaterEqual(cards[1].top - cards[0].bottom, 12)
        self.assertGreaterEqual(cards[2].top - cards[1].bottom, 12)
        self.assertGreaterEqual(pygame.Rect(1000, 646, 220, 38).top - cards[-1].bottom, 10)

    def test_default_hand_cards_fit_left_panel(self):
        panel = pygame.Rect(LEFT_PANEL)
        x = LEFT_PANEL[0] + (LEFT_PANEL[2] - HAND_CARD_W) // 2
        cards = [
            pygame.Rect(x, 370 + index * (HAND_CARD_H + 9), HAND_CARD_W, HAND_CARD_H)
            for index in range(PLUS_HAND_LIMIT)
        ]

        for card in cards:
            self.assertTrue(panel.contains(card))
        self.assertGreaterEqual(cards[1].top - cards[0].bottom, 9)
        self.assertGreaterEqual(cards[2].top - cards[1].bottom, 9)


if __name__ == "__main__":
    unittest.main()
