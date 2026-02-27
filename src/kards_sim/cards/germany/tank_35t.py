from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import Nation, UnitClass
from ..unit import UnitCard

if TYPE_CHECKING:
    from ...events import Event, TriggerContext
    from ...state import GameState


class Tank35T(UnitCard):
    """35(t)坦克 — 部署时若场上有友方步兵，行动费用减少1。"""

    name = "35(t)坦克"
    nation = Nation.GERMANY
    unit_class = UnitClass.TANK
    cost = 2
    acost = 1
    attack_value = 2
    health_value = 2

    def on_deploy(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        assert ctx.source is not None
        ci = state.inst(ctx.source)
        has_friendly_infantry = any(
            iid != ctx.source
            and state.inst(iid).owner == ci.owner
            and hasattr(state.card(iid), "counts_as")
            and state.card(iid).counts_as(UnitClass.INFANTRY)
            for iid in state.board_unit_iids()
        )
        if has_friendly_infantry:
            ci.operation_cost = max(0, ci.operation_cost - 1)
        return []
