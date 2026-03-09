from __future__ import annotations

from ...types import Nation, UnitClass
from ..unit import UnitCard


class Regiment980(UnitCard):
    """第980国民掷弹兵团 — 德国步兵，高血量肉盾。"""

    name = "第980国民掷弹兵团"
    nation = Nation.GERMANY
    unit_class = UnitClass.INFANTRY
    cost = 3
    acost = 1
    attack_value = 3
    health_value = 6
