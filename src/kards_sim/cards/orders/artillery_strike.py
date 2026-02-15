from __future__ import annotations

from ..specs import AbilitySpec
from ..orders.base import OrderCardBase
from ...types import CardType, Nation


class ArtilleryStrike(OrderCardBase):
    name = "Artillery Strike"
    card_type = CardType.ORDER
    nation = Nation.NEUTRAL
    cost = 2
    abilities = (AbilitySpec("on_play_deal_damage", params={"amount": 2}),)
