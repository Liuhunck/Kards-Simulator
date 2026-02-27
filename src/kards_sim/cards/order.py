from __future__ import annotations

from ..types import CardType
from .base import CardBase


class OrderCard(CardBase):
    """Base class for order cards.

    Orders are played from hand, apply a one-time effect, and are then
    discarded.  The effect is implemented by overriding ``on_play``.
    """

    card_type = CardType.ORDER
    cost: int
