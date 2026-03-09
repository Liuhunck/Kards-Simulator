from __future__ import annotations

from typing import TYPE_CHECKING

from ..types import CardType, InstanceId, PlayerId
from .base import CardBase

if TYPE_CHECKING:
    from ..state import GameState


class OrderCard(CardBase):
    """Base class for order cards.

    Orders are played from hand, apply a one-time effect, and are then
    discarded.  The effect is implemented by overriding ``on_play``.
    """

    card_type = CardType.ORDER
    cost: int

    def validate_target(
        self,
        state: GameState,
        player_id: PlayerId,
        target: InstanceId | None,
    ) -> str | None:
        """Return an error message if *target* is invalid, else None."""
        return None
