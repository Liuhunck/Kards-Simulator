from __future__ import annotations

from ...definitions import CardDefinition
from ..base import UnitCardBase
from ....types import CardType, UnitClass


class Bomber(UnitCardBase):
    definition = CardDefinition(
        def_id="UNIT_BOMBER_4",
        name="Bomber",
        card_type=CardType.UNIT,
        cost=4,
        acost=2,
        unit_class=UnitClass.BOMBER,
        attack=4,
        health=3,
        abilities=(),
    )
