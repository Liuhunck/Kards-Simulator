from __future__ import annotations

from ...types import Nation, UnitClass
from ..unit import UnitCard


class Bf109E(UnitCard):
    """Bf109E — 德国标准战斗机。"""

    name = "Bf109E"
    nation = Nation.GERMANY
    unit_class = UnitClass.FIGHTER
    cost = 3
    acost = 2
    attack_value = 3
    health_value = 4
