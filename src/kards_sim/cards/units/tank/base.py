from __future__ import annotations

from ....types import UnitClass
from ..base import UnitCardBase


class TankBase(UnitCardBase):
    unit_class = UnitClass.TANK
