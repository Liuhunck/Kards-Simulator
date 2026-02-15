from __future__ import annotations

from .base import NeutralFighterBase


class Fighter(NeutralFighterBase):
    name = "Fighter"
    cost = 2
    acost = 1
    attack_value = 2
    health_value = 2
    abilities = ()
