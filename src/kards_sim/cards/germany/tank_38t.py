from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import Nation, UnitClass
from ..unit import UnitCard

if TYPE_CHECKING:
    from ...events import Event, TriggerContext
    from ...state import GameState


class Tank38T(UnitCard):
    """38(t)坦克 — 部署时抽1张牌。"""

    name = "38(t)坦克"
    nation = Nation.GERMANY
    unit_class = UnitClass.TANK
    cost = 3
    acost = 1
    attack_value = 2
    health_value = 3
    description = "部署时抽1张牌"

    def on_deploy(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        from ...events import CardDrawn
        from ...resolver import enqueue_draw

        assert ctx.player_id is not None
        events: list[Event] = []
        drawn = enqueue_draw(state, ctx.player_id)
        if drawn is not None:
            events.append(CardDrawn(player_id=ctx.player_id, card=drawn))
        return events
