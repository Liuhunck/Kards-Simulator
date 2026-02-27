from __future__ import annotations

from ...types import Nation
from ..headquarters import HeadquartersCard


class SovietHeadquarters(HeadquartersCard):
    name = "Soviet Headquarters"
    nation = Nation.SOVIET
    health_value = 20
