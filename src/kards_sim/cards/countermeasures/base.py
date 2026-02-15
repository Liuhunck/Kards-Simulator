from __future__ import annotations

from typing import TYPE_CHECKING

from ...actions import PlayCard
from ...events import CardPlayed
from ...rules import can_play_card, require
from ...types import Zone
from ..base import CardBase

if TYPE_CHECKING:
    from ...state import GameState


class CountermeasureCardBase(CardBase):
    """Shared behavior for countermeasure cards."""

    cost: int

    def deploy(self, state: GameState, action: PlayCard) -> list:
        iid = action.card
        can_play_card(state, action.player_id, iid)

        inst = state.get_instance(iid)
        player = state.players[action.player_id]
        require(
            getattr(self, "cost", None) is not None,
            "countermeasure missing cost",
        )

        inst.lane = None
        inst.zone = Zone.DISCARD
        player.credits -= int(self.cost)
        player.discard.append(iid)
        player.hand.remove(iid)

        return [
            CardPlayed(
                player_id=action.player_id,
                card=iid,
                target=action.target,
                target_player=(
                    state.other(action.player_id) if action.target_hq else None
                ),
            )
        ]
