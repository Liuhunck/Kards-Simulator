from __future__ import annotations

from ...types import Nation, UnitClass
from ..unit import UnitCard


class Fighter(UnitCard):
    name = "战斗机"
    nation = Nation.NEUTRAL
    unit_class = UnitClass.FIGHTER
    cost = 2
    acost = 1
    attack_value = 2
    health_value = 2
