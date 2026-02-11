from __future__ import annotations

from ...definitions import CardDefinition
from ..base import UnitCardBase
from ....types import CardType, UnitClass


class Fighter(UnitCardBase):
    definition = CardDefinition(
        def_id="UNIT_FIGHTER_2",
        name="Fighter",
        card_type=CardType.UNIT,
        cost=2,
        acost=1,
        unit_class=UnitClass.FIGHTER,
        attack=2,
        health=2,
        abilities=(),
    )
