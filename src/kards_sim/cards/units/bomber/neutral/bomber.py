from __future__ import annotations

from .base import NeutralBomberBase


class Bomber(NeutralBomberBase):
    name = "Bomber"
    cost = 4
    acost = 2
    attack_value = 4
    health_value = 3
    abilities = ()
