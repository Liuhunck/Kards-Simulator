from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import Nation, UnitClass
from ..unit import UnitCard

if TYPE_CHECKING:
    from ...events import Event, TriggerContext
    from ...state import GameState


class RadioTeam(UnitCard):
    """无线电小队 — 部署时抽1张牌。"""

    name = "无线电小队"
    nation = Nation.NEUTRAL
    unit_class = UnitClass.INFANTRY
    cost = 2
    acost = 2
    attack_value = 1
    health_value = 2

    def on_deploy(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        from ...events import CardDrawn
        from ...resolver import enqueue_draw

        assert ctx.player_id is not None
        events: list[Event] = []
        drawn = enqueue_draw(state, ctx.player_id)
        if drawn is not None:
            events.append(CardDrawn(player_id=ctx.player_id, card=drawn))
        return events
