from __future__ import annotations

from .....types import Nation
from ..base import TankBase


class NeutralTankBase(TankBase):
    nation = Nation.NEUTRAL
