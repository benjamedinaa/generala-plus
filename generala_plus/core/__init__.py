"""Core game state and action layer.

This package is intentionally independent from Pygame. It is the foundation
for future online play, tests, replays, and server-side validation.
"""

from .actions import Action
from .engine import GeneralaEngine
from .state import GameState, PlayerState

__all__ = ["Action", "GameState", "PlayerState", "GeneralaEngine"]
