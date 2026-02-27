from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import Keyword, Nation, UnitClass
from ..unit import UnitCard

if TYPE_CHECKING:
    from ...events import Event, TriggerContext
    from ...state import GameState


class Flak88(UnitCard):
    """88毫米高射炮 — 伏击；对抗空军或坦克时，具有双倍攻击力。"""

    name = "88毫米高射炮"
    nation = Nation.GERMANY
    unit_class = UnitClass.ARTILLERY
    cost = 6
    acost = 2
    attack_value = 3
    health_value = 4
    keywords = frozenset({Keyword.AMBUSH})

    _attack_boosted: bool = False

    def _is_air_or_tank(self, state: GameState, iid: int) -> bool:
        card = state.card(iid)
        if not hasattr(card, "counts_as"):
            return False
        return (
            card.counts_as(UnitClass.FIGHTER)
            or card.counts_as(UnitClass.BOMBER)
            or card.counts_as(UnitClass.TANK)
        )

    def before_attack(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        assert ctx.self_iid is not None
        assert ctx.source is not None and ctx.target is not None
        opponent_iid = ctx.target if ctx.self_iid == ctx.source else ctx.source
        if self._is_air_or_tank(state, opponent_iid):
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
