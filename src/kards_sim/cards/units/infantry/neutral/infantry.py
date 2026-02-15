from __future__ import annotations

from .base import NeutralInfantryBase


class Infantry(NeutralInfantryBase):
    name = "Infantry"
    cost = 1
    acost = 1
    attack_value = 1
    health_value = 1
    abilities = ()
