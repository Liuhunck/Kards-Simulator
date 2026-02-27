from __future__ import annotations

from ...types import Nation
from ..countermeasure import CountermeasureCard


class SampleCountermeasure(CountermeasureCard):
    name = "示例反制"
    nation = Nation.NEUTRAL
    cost = 1
