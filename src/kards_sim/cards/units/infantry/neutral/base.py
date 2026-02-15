from __future__ import annotations

from .....types import Nation
from ..base import InfantryBase


class NeutralInfantryBase(InfantryBase):
    nation = Nation.NEUTRAL
