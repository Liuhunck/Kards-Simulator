from __future__ import annotations

from ...types import Nation, UnitClass
from ..unit import UnitCard


class Infantry(UnitCard):
    name = "步兵"
    nation = Nation.NEUTRAL
    unit_class = UnitClass.INFANTRY
    cost = 1
    acost = 1
    attack_value = 1
    health_value = 1
