from __future__ import annotations

from ...types import Nation, UnitClass
from ..unit import UnitCard


class PantherG(UnitCard):
    """豹式坦克G型 — 重甲1；无法被敌方指令指向。"""

    name = "豹式坦克G型"
    nation = Nation.GERMANY
    unit_class = UnitClass.TANK
    cost = 5
    acost = 3
    attack_value = 6
    health_value = 5
    heavy_armor = 1
    order_immune = True
