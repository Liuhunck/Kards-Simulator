from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import InstanceId, Nation, PlayerId, UnitClass
from ..order import OrderCard

if TYPE_CHECKING:
    from ...events import Event, TriggerContext
    from ...state import GameState


class CoordinatedOps(OrderCard):
    """协同作战 — 友方单位每有一种单位类型，使1个友方坦克获得+1/+1。"""

    name = "协同作战"
    nation = Nation.GERMANY
    cost = 1
    description = "友方每有一种单位类型，使目标友方坦克+1/+1"

    def validate_target(
        self, state: GameState, player_id: PlayerId, target: InstanceId | None
    ) -> str | None:
        if target is None:
            return "must specify a friendly tank as target"
        ci = state.inst(target)
        if ci.owner != player_id:
            return "target must be a friendly unit"
        card = state.card(target)
        if not (hasattr(card, "counts_as") and card.counts_as(UnitClass.TANK)):
            return "target must be a tank"
        return None

    def on_play(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        from ...events import BuffApplied

        assert ctx.player_id is not None and ctx.target is not None
        types_seen: set[UnitClass] = set()
        for iid in state.friendly_board_iids(ctx.player_id):
            card = state.card(iid)
            if hasattr(card, "unit_class"):
                types_seen.add(card.unit_class)

        n = len(types_seen)
        if n > 0:
            return [BuffApplied(source=ctx.source, target=ctx.target, attack_delta=n, health_delta=n)]
        return []
