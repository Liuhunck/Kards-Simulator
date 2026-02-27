from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import Nation, UnitClass
from ..unit import UnitCard

if TYPE_CHECKING:
    from ...events import Event, TriggerContext
    from ...state import GameState


class FiatG50(UnitCard):
    """菲亚特G.50 — 造成伤害时，使友方总部恢复同等防御力。"""

    name = "菲亚特G.50"
    nation = Nation.ITALY
    unit_class = UnitClass.FIGHTER
    cost = 2
    acost = 2
    attack_value = 2
    health_value = 3

    def after_deal_damage(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        from ...events import HealApplied

        assert ctx.source is not None and ctx.amount is not None
        owner = state.inst(ctx.source).owner
        hq_iid = state.players[owner].hq_iid
        if ctx.amount > 0:
            return [HealApplied(source=ctx.source, target=hq_iid, amount=ctx.amount)]
        return []
