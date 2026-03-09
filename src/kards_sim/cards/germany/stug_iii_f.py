from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import Keyword, Nation, UnitClass
from ..unit import UnitCard

if TYPE_CHECKING:
    from ...events import Event, TriggerContext
    from ...state import GameState


class StugIIIF(UnitCard):
    """三号突击炮F型 — 烟幕；对坦克攻击时攻击力翻倍。"""

    name = "三号突击炮F型"
    nation = Nation.GERMANY
    unit_class = UnitClass.TANK
    cost = 2
    acost = 1
    attack_value = 2
    health_value = 3
    keywords = frozenset({Keyword.SMOKESCREEN})
    description = "烟幕；对坦克攻击力翻倍"

    _attack_boosted: bool = False

    def before_attack(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        assert ctx.self_iid is not None
        assert ctx.source is not None and ctx.target is not None
        opponent_iid = ctx.target if ctx.self_iid == ctx.source else ctx.source
        opponent_card = state.card(opponent_iid)
        if hasattr(opponent_card, "counts_as") and opponent_card.counts_as(UnitClass.TANK):
            ci = state.inst(ctx.self_iid)
            ci.current_attack *= 2
            self._attack_boosted = True
        return []

    def after_attack(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        if self._attack_boosted:
            assert ctx.self_iid is not None
            ci = state.inst(ctx.self_iid)
            ci.current_attack //= 2
            self._attack_boosted = False
        return []
