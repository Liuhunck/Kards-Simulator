from __future__ import annotations

from ..types import CardType, UnitClass
from .base import CardBase


class UnitCard(CardBase):
    """Base class for all military unit cards.

    Subclasses must set ``cost``, ``acost``, ``unit_class``,
    ``attack_value``, and ``health_value`` as class attributes.

    Deployment, advancement, and combat logic is handled by the
    resolver — not by the card class.  Card-specific abilities are
    added by overriding the trigger hooks inherited from ``CardBase``
    (e.g. ``on_deploy``, ``on_destroy``).
    """

    card_type = CardType.UNIT

    cost: int
    acost: int
    unit_class: UnitClass
    attack_value: int
    health_value: int

    def counts_as(self, uc: UnitClass) -> bool:
        """Return True if this unit should be treated as the given class.

        Override in subclasses that count as multiple unit types
        (e.g. an infantry that also counts as a tank).
        """
        return uc == self.unit_class
