from __future__ import annotations

from .base import NeutralTankBase


class LightTank(NeutralTankBase):
    name = "Light Tank"
    cost = 3
    acost = 2
    attack_value = 3
    health_value = 3
    abilities = ()
