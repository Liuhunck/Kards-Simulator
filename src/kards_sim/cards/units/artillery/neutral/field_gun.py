from __future__ import annotations

from .base import NeutralArtilleryBase


class FieldGun(NeutralArtilleryBase):
    name = "Field Gun"
    cost = 2
    acost = 1
    attack_value = 2
    health_value = 2
    abilities = ()
