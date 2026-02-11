from __future__ import annotations

from ..definitions import CardDefinition
from ..bases.base import BaseCardBase
from ...types import CardType


class Headquarters(BaseCardBase):
    definition = CardDefinition(
        def_id="BASE",
        name="Headquarters",
        card_type=CardType.BASE,
        cost=0,
    )
