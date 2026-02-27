from __future__ import annotations

from ...types import Nation, UnitClass
from ..unit import UnitCard


class Bomber(UnitCard):
    name = "轰炸机"
    nation = Nation.NEUTRAL
    unit_class = UnitClass.BOMBER
    cost = 4
    acost = 2
    attack_value = 4
    health_value = 3
