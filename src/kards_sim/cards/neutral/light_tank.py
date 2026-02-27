from __future__ import annotations

from ...types import Nation, UnitClass
from ..unit import UnitCard


class LightTank(UnitCard):
    name = "轻型坦克"
    nation = Nation.NEUTRAL
    unit_class = UnitClass.TANK
    cost = 3
    acost = 2
    attack_value = 3
    health_value = 3
