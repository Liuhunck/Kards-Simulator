from __future__ import annotations

from ...types import Nation
from ..headquarters import HeadquartersCard


class GermanyHeadquarters(HeadquartersCard):
    name = "Germany Headquarters"
    nation = Nation.GERMANY
    health_value = 20
