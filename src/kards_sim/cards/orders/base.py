from __future__ import annotations

from typing import TYPE_CHECKING

from ...actions import PlayCard
from ...events import CardPlayed
from ...rules import can_play_card
from ...types import Zone
from ..base import CardBase

if TYPE_CHECKING:
    from ...state import GameState


class OrderCardBase(CardBase):
    """Shared behavior for order cards."""

    def play(self, state: GameState, action: PlayCard) -> list:
        can_play_card(state, action.player_id, action.card)

        inst = state.get_instance(action.card)
        player = state.players[action.player_id]

        inst.lane = None
        inst.zone = Zone.DISCARD
        player.credits -= self.definition.cost
        player.discard.append(action.card)
        player.hand.remove(action.card)

        return [
            CardPlayed(
                player_id=action.player_id,
                card=action.card,
                target=action.target,
                target_player=(
                    state.other(action.player_id) if action.target_hq else None
                ),
            )
        ]
