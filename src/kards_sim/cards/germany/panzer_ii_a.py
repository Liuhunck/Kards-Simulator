from __future__ import annotations

from ...types import Keyword, Nation, UnitClass
from ..unit import UnitCard


class PanzerIIA(UnitCard):
    """二号坦克A型 — 闪击、烟幕。"""

    name = "二号坦克A型"
    nation = Nation.GERMANY
    unit_class = UnitClass.TANK
    cost = 1
    acost = 1
    attack_value = 1
    health_value = 3
    keywords = frozenset({Keyword.BLITZ, Keyword.SMOKESCREEN})
    description = "闪击；烟幕"
