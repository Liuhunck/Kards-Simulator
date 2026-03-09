from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import Nation, UnitClass
from ..unit import UnitCard

if TYPE_CHECKING:
    from ...events import Event, TriggerContext
    from ...state import GameState


class FiatCR42(UnitCard):
    """菲亚特C.R.42 — 部署时若友方单位数量大于敌方，获得+1攻击力。"""

    name = "菲亚特C.R.42"
    nation = Nation.ITALY
    unit_class = UnitClass.FIGHTER
    cost = 1
    acost = 1
    attack_value = 1
    health_value = 2
    description = "部署时若友方多于敌方，+1攻"

    def on_deploy(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        from ...events import BuffApplied

        assert ctx.source is not None and ctx.player_id is not None
        friendly_count = len(state.friendly_board_iids(ctx.player_id))
        enemy_count = len(state.enemy_board_iids(ctx.player_id))

        if friendly_count > enemy_count:
            return [BuffApplied(source=ctx.source, target=ctx.source, attack_delta=1)]
        return []
