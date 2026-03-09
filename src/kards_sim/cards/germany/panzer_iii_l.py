from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import Keyword, Nation, UnitClass
from ..unit import UnitCard

if TYPE_CHECKING:
    from ...events import Event, TriggerContext
    from ...state import GameState


class PanzerIIIL(UnitCard):
    """三号坦克L型 — 友方单位每有一种非坦克类型，具有+1攻击力。"""

    name = "三号坦克L型"
    nation = Nation.GERMANY
    unit_class = UnitClass.TANK
    cost = 3
    acost = 2
    attack_value = 3
    health_value = 5
    keywords = frozenset({Keyword.BLITZ})
    description = "闪击；友方每有一种非坦克类型+1攻"

    _type_bonus: int = 0

    def _calc_bonus(self, state: GameState, my_iid: int) -> int:
        owner = state.inst(my_iid).owner
        types_seen: set[UnitClass] = set()
        for iid in state.friendly_board_iids(owner):
            if iid == my_iid:
                continue
            card = state.card(iid)
            if hasattr(card, "unit_class") and not card.counts_as(UnitClass.TANK):
                types_seen.add(card.unit_class)
        return len(types_seen)

    def _refresh_bonus(self, state: GameState, my_iid: int) -> None:
        new_bonus = self._calc_bonus(state, my_iid)
        delta = new_bonus - self._type_bonus
        if delta != 0:
            ci = state.inst(my_iid)
            ci.current_attack += delta
            self._type_bonus = new_bonus

    def on_deploy(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        assert ctx.self_iid is not None
        self._type_bonus = 0
        self._refresh_bonus(state, ctx.self_iid)
        return []

    def on_any_deploy(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        assert ctx.self_iid is not None
        if ctx.source == ctx.self_iid:
            return []
        self._refresh_bonus(state, ctx.self_iid)
        return []

    def on_any_destroy(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        assert ctx.self_iid is not None
        if ctx.source == ctx.self_iid:
            return []
        self._refresh_bonus(state, ctx.self_iid)
        return []
