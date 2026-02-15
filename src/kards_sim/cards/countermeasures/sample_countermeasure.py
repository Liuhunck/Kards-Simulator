from __future__ import annotations

from ..countermeasures.base import CountermeasureCardBase
from ...types import CardType, Nation


class SampleCountermeasure(CountermeasureCardBase):
    name = "Countermeasure (Sample)"
    card_type = CardType.COUNTERMEASURE
    nation = Nation.NEUTRAL
    cost = 1
    abilities = ()
