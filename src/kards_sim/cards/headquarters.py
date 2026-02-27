from __future__ import annotations

from ..types import CardType
from .base import CardBase


class HeadquartersCard(CardBase):
    """Base class for all headquarters (HQ) cards.

    Each player's HQ sits in their supportline and has health but no attack.
    Reducing the enemy HQ to 0 wins the game.
    """

    card_type = CardType.HEADQUARTERS
    health_value: int = 20
