"""KARDS simulator (engine-first).

This package intentionally keeps UI out of the core engine.
"""

from .engine import Engine
from .state import GameState

__all__ = ["Engine", "GameState"]
