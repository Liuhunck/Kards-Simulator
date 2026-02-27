from __future__ import annotations

from ...types import Nation
from ..headquarters import HeadquartersCard


class JapanHeadquarters(HeadquartersCard):
    name = "Japan Headquarters"
    nation = Nation.JAPAN
    health_value = 20
