from __future__ import annotations

from ...types import Nation, UnitClass
from ..unit import UnitCard


class Regiment1(UnitCard):
    name = "第1步兵团"
    nation = Nation.GERMANY
    unit_class = UnitClass.INFANTRY
    cost = 1
    acost = 0
    attack_value = 1
    health_value = 2
