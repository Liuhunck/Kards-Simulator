from __future__ import annotations

from ...types import Nation
from ..headquarters import HeadquartersCard


class BritainHeadquarters(HeadquartersCard):
    name = "Britain Headquarters"
    nation = Nation.BRITAIN
    health_value = 20
