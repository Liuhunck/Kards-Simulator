from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import Nation
from ..order import OrderCard

if TYPE_CHECKING:
    from ...events import Event, TriggerContext
    from ...state import GameState


class EagleClaw(OrderCard):
    """鹰爪 — 对敌方支援线所有单位造成2点伤害。"""

    name = "鹰爪"
    nation = Nation.GERMANY
    cost = 3
    description = "对敌方支援线所有单位造成2点伤害"

    def on_play(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        from ...events import DamageDealt

        assert ctx.player_id is not None
        enemy = state.opponent(ctx.player_id)
        events: list[Event] = []
        for iid in list(state.supportline[enemy]):
            if state.card(iid).card_type.value == "headquarters":
                continue
            events.append(
                DamageDealt(source=ctx.source, target=iid, target_player=None, amount=2)
            )
        return events
