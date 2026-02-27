from __future__ import annotations

from ...types import Nation
from ..headquarters import HeadquartersCard


class UsaHeadquarters(HeadquartersCard):
    name = "USA Headquarters"
    nation = Nation.USA
    health_value = 20
