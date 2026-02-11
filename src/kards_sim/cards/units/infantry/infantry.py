from __future__ import annotations

from ...definitions import CardDefinition
from ..base import UnitCardBase
from ....types import CardType, UnitClass


class Infantry(UnitCardBase):
    definition = CardDefinition(
        def_id="UNIT_INF_1",
        name="Infantry",
        card_type=CardType.UNIT,
        cost=1,
        acost=1,
        unit_class=UnitClass.INFANTRY,
        attack=1,
        health=1,
        abilities=(),
    )
