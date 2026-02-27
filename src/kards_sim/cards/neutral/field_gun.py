from __future__ import annotations

from ...types import Nation, UnitClass
from ..unit import UnitCard


class FieldGun(UnitCard):
    name = "野战炮"
    nation = Nation.NEUTRAL
    unit_class = UnitClass.ARTILLERY
    cost = 2
    acost = 1
    attack_value = 2
    health_value = 2
