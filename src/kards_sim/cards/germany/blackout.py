from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import InstanceId, Nation, PlayerId, UnitClass
from ..order import OrderCard

if TYPE_CHECKING:
    from ...events import Event, TriggerContext
    from ...state import GameState


class Blackout(OrderCard):
    """灯火管制 — 压制1个敌方空军，抽1张牌。"""

    name = "灯火管制"
    nation = Nation.GERMANY
    cost = 1
    description = "压制1个敌方空军，抽1张牌"

    def validate_target(
        self, state: GameState, player_id: PlayerId, target: InstanceId | None
    ) -> str | None:
        if target is None:
            return "must specify an enemy air unit as target"
        ci = state.inst(target)
        if ci.owner == player_id:
            return "target must be an enemy unit"
        card = state.card(target)
        if not hasattr(card, "counts_as"):
            return "target must be an air unit (fighter/bomber)"
        if not (card.counts_as(UnitClass.FIGHTER) or card.counts_as(UnitClass.BOMBER)):
            return "target must be an air unit (fighter/bomber)"
        return None

    def on_play(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        from ...events import CardDrawn
        from ...resolver import enqueue_draw

        assert ctx.player_id is not None and ctx.target is not None

        target_ci = state.inst(ctx.target)
        target_ci.suppressed = True
        target_ci.suppressed_until_turn = state.turn + 1

        events: list[Event] = []
        drawn = enqueue_draw(state, ctx.player_id)
        if drawn is not None:
            events.append(CardDrawn(player_id=ctx.player_id, card=drawn))
        return events
