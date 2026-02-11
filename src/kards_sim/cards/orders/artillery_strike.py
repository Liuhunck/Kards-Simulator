from __future__ import annotations

from ..definitions import AbilitySpec, CardDefinition
from ..orders.base import OrderCardBase
from ...types import CardType


class ArtilleryStrike(OrderCardBase):
    definition = CardDefinition(
        def_id="ORDER_DMG_2",
        name="Artillery Strike",
        card_type=CardType.ORDER,
        cost=2,
        abilities=(AbilitySpec("on_play_deal_damage", params={"amount": 2}),),
    )
