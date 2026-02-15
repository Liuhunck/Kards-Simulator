from __future__ import annotations

from .....types import Nation
from ..base import BomberBase


class NeutralBomberBase(BomberBase):
    nation = Nation.NEUTRAL
