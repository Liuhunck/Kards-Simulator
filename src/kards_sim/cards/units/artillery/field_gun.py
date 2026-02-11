from __future__ import annotations

from ...definitions import CardDefinition
from ..base import UnitCardBase
from ....types import CardType, UnitClass


class FieldGun(UnitCardBase):
    definition = CardDefinition(
        def_id="UNIT_ARTY_2",
        name="Field Gun",
        card_type=CardType.UNIT,
        cost=2,
        acost=1,
        unit_class=UnitClass.ARTILLERY,
        attack=2,
        health=2,
        abilities=(),
    )
