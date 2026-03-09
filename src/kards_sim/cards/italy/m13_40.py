from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import Nation, UnitClass
from ..unit import UnitCard

if TYPE_CHECKING:
    from ...events import Event, TriggerContext
    from ...state import GameState


class M1340(UnitCard):
    """M13/40 — 部署时若场上有友方步兵，获得闪击（立即可行动）。"""

    name = "M13/40"
    nation = Nation.ITALY
    unit_class = UnitClass.TANK
    cost = 3
    acost = 1
    attack_value = 3
    health_value = 4
    description = "部署时若有友方步兵，获得闪击"

    def on_deploy(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        assert ctx.source is not None and ctx.player_id is not None
        ci = state.inst(ctx.source)
        has_friendly_infantry = any(
            iid != ctx.source
            and state.inst(iid).owner == ctx.player_id
            and hasattr(state.card(iid), "counts_as")
            and state.card(iid).counts_as(UnitClass.INFANTRY)
            for iid in state.board_unit_iids()
        )
        if has_friendly_infantry:
            ci.exhausted = False
        return []
