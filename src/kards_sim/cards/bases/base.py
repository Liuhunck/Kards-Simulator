from __future__ import annotations

from ..base import CardBase
from ...types import CardType


class BaseCardBase(CardBase):
    """Shared behavior for base cards (HQ)."""

    card_type = CardType.BASE
    health_value: int = 20
