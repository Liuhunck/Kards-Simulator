from __future__ import annotations

from ....specs import AbilitySpec
from .base import NeutralInfantryBase


class RadioTeam(NeutralInfantryBase):
    name = "Radio Team"
    cost = 2
    acost = 2
    attack_value = 1
    health_value = 2
    abilities = (AbilitySpec("on_deploy_draw", params={"n": 1}),)
