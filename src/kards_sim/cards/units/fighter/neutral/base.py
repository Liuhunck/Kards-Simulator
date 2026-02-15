from __future__ import annotations

from .....types import Nation
from ..base import FighterBase


class NeutralFighterBase(FighterBase):
    nation = Nation.NEUTRAL
