from __future__ import annotations

from ...definitions import CardDefinition
from ..base import UnitCardBase
from ....types import CardType, UnitClass


class LightTank(UnitCardBase):
    definition = CardDefinition(
        def_id="UNIT_TANK_3",
        name="Light Tank",
        card_type=CardType.UNIT,
        cost=3,
        acost=2,
        unit_class=UnitClass.TANK,
        attack=3,
        health=3,
        abilities=(),
    )
