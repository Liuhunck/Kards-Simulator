from __future__ import annotations

from ...types import Nation, UnitClass
from ..unit import UnitCard


class Regiment432(UnitCard):
    name = "第432步兵团"
    nation = Nation.GERMANY
    unit_class = UnitClass.INFANTRY
    cost = 1
    acost = 1
    attack_value = 1
    health_value = 4
