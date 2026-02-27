from __future__ import annotations

from ..types import CardType
from .base import CardBase


class CountermeasureCard(CardBase):
    """Base class for countermeasure cards.

    Countermeasures are hidden traps set from hand.  When activated,
    they can cancel or react to enemy actions.  Implement the
    specific behaviour by overriding ``on_play``.
    """

    card_type = CardType.COUNTERMEASURE
    cost: int

    # The trigger condition that activates this countermeasure.
    # Subclasses can override ``should_trigger`` to define when
    # the countermeasure fires during the opponent's turn.
    def should_trigger(self, state: "GameState", ctx: "TriggerContext") -> bool:  # type: ignore[name-defined]
        return False
