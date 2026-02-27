from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import Nation
from ..order import OrderCard

if TYPE_CHECKING:
    from ...events import Event, TriggerContext
    from ...state import GameState


class ArtilleryStrike(OrderCard):
    """炮火打击 — 对一个目标单位或敌方总部造成2点伤害。"""

    name = "炮火打击"
    nation = Nation.NEUTRAL
    cost = 2

    def on_play(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        from ...events import DamageDealt

        events: list[Event] = []
        if ctx.target is not None or ctx.target_player is not None:
            events.append(
                DamageDealt(
                    source=ctx.source,
                    target=ctx.target,
                    target_player=ctx.target_player,
                    amount=2,
                )
            )
        return events
