from __future__ import annotations

from typing import TYPE_CHECKING

from .....types import CardType, UnitClass
from .....actions import PlayCard
from .base import GermanyTankBase

if TYPE_CHECKING:
    from .....state import GameState


class Tank35T(GermanyTankBase):
    name = "35(t)坦克"
    cost = 2
    acost = 1
    attack_value = 2
    health_value = 2
    abilities = ()

    def deploy(self, state: GameState, action: PlayCard) -> list:
        iid = action.card
        events = super().deploy(state, action)

        owner = state.get_instance(iid).owner
        has_friendly_infantry = any(
            other_iid != iid
            and state.get_instance(other_iid).owner == owner
            and state.get_card_for_instance(other_iid).card_type == CardType.UNIT
            and state.get_card_for_instance(other_iid).unit_class == UnitClass.INFANTRY
            for other_iid in state.all_board_unit_ids()
        )

        if has_friendly_infantry and self.acost is not None:
            self.acost = max(0, int(self.acost) - 1)

        return events
