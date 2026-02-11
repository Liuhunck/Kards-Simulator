from __future__ import annotations

from ...definitions import AbilitySpec, CardDefinition
from ..base import UnitCardBase
from ....types import CardType, UnitClass


class RadioTeam(UnitCardBase):
    definition = CardDefinition(
        def_id="UNIT_DRAW_2",
        name="Radio Team",
        card_type=CardType.UNIT,
        cost=2,
        acost=2,
        unit_class=UnitClass.INFANTRY,
        attack=1,
        health=2,
        abilities=(AbilitySpec("on_deploy_draw", params={"n": 1}),),
    )
