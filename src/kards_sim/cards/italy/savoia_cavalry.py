from __future__ import annotations

from ...types import Keyword, Nation, UnitClass
from ..unit import UnitCard


class SavoiaCavalry(UnitCard):
    """萨沃亚骑兵团 — 拥有闪击，同时也算作坦克。"""

    name = "萨沃亚骑兵团"
    nation = Nation.ITALY
    unit_class = UnitClass.INFANTRY
    cost = 1
    acost = 1
    attack_value = 1
    health_value = 1
    keywords = frozenset({Keyword.BLITZ})
    description = "闪击；同时算作坦克"

    def counts_as(self, uc: UnitClass) -> bool:
        return uc in (UnitClass.INFANTRY, UnitClass.TANK)
