from __future__ import annotations

from dataclasses import dataclass

from .state import GameState
from .types import BoardPos, CardType, InstanceId, Lane, PlayerId, UnitClass, Zone


@dataclass(frozen=True, slots=True)
class RuleViolation(Exception):
    reason: str

    def __str__(self) -> str:  # pragma: no cover
        return self.reason


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuleViolation(reason)


def can_play_card(state: GameState, pid: PlayerId, iid: InstanceId) -> None:
    player = state.players[pid]
    require(pid == state.active_player, "not your turn")
    require(iid in player.hand, "card not in hand")
    inst = state.get_instance(iid)
    require(inst.owner == pid, "not your card")
    defn = state.get_def(inst.def_id)
    require(player.credits >= defn.cost, "not enough credits")


def can_deploy_unit(state: GameState, pid: PlayerId, iid: InstanceId, pos: int) -> None:
    inst = state.get_instance(iid)
    defn = state.get_def(inst.def_id)
    require(defn.card_type == CardType.UNIT, "not a unit")
    require(len(state.supportline[pid]) < state.config.columns, "supportline is full")
    require(
        0 <= pos <= len(state.supportline[pid]),
        "index out of supportline range",
    )


def can_advance_unit(
    state: GameState, pid: PlayerId, iid: InstanceId, pos: int
) -> None:
    inst = state.get_instance(iid)
    require(inst.owner == pid, "not your unit")
    require(inst.zone == Zone.BOARD, "unit not on board")
    require(inst.lane == Lane.SUPPORTLINE, "unit not in supportline")
    require(not inst.exhausted, "unit exhausted")
    require(state.card_type_of(iid) == CardType.UNIT, "not a unit")
    require(
        state.frontline_owner() != state.other(pid),
        "cannot advance when enemy controls frontline",
    )
    require(
        len(state.frontline) < state.config.columns,
        "frontline is full",
    )
    require(
        0 <= pos <= len(state.frontline),
        "index out of frontline range",
    )
    if inst.cost is not None:
        require(state.players[pid].credits >= inst.cost, "not enough credits")
    require(state.supportline[pid].count(iid) == 1, "unit not in your supportline")
    require(inst.current_health is not None and inst.current_health > 0, "unit dead")


def can_attack(
    state: GameState,
    pid: PlayerId,
    attacker: InstanceId,
    defender: InstanceId | None,
) -> None:
    require(pid == state.active_player, "not your turn")
    a = state.get_instance(attacker)
    require(a.owner == pid, "not your unit")
    require(a.zone == Zone.BOARD, "attacker not on board")
    require(a.lane is not None, "attacker missing lane")
    # require(a.pos is not None, "attacker missing board pos")
    require(not a.exhausted, "attacker exhausted")
    require(state.card_type_of(attacker) == CardType.UNIT, "attacker not a unit")
    require(a.current_health is not None and a.current_health > 0, "attacker dead")

    attacker_def = state.get_def(a.def_id)
    require(attacker_def.card_type == CardType.UNIT, "attacker not a unit")
    require(attacker_def.unit_class is not None, "attacker missing unit_class")

    require(defender is not None, "missing defender")
    assert defender is not None
    d = state.get_instance(defender)
    require(d.owner == state.other(pid), "defender must be enemy")
    require(d.zone == Zone.BOARD, "defender not on board")
    require(d.lane is not None, "defender missing lane")

    def is_adjacent_lane(
        state: GameState, lane_a: Lane | None, lane_b: Lane | None
    ) -> bool:
        if lane_a == Lane.SUPPORTLINE:
            return lane_b == Lane.FRONTLINE
        elif lane_a == Lane.FRONTLINE:
            return lane_b == Lane.SUPPORTLINE
        return False

    def is_guard_unit(state: GameState, iid: InstanceId) -> bool:
        inst = state.get_instance(iid)
        defn = state.get_def(inst.def_id)
        return defn.abilities is not None and "GUARD" in defn.abilities

    def no_guard_protected(state: GameState, defender: InstanceId) -> bool:
        if d.lane == Lane.FRONTLINE:
            idx = state.frontline.index(defender)
            if (idx > 0 and is_guard_unit(state, state.frontline[idx - 1])) or (
                idx < len(state.frontline) - 1
                and is_guard_unit(state, state.frontline[idx + 1])
            ):
                return False
        elif d.lane == Lane.SUPPORTLINE:
            idx = state.supportline[state.other(pid)].index(defender)
            if (
                idx > 0
                and is_guard_unit(state, state.supportline[state.other(pid)][idx - 1])
            ) or (
                idx < len(state.supportline[state.other(pid)]) - 1
                and is_guard_unit(state, state.supportline[state.other(pid)][idx + 1])
            ):
                return False
        return True

    def no_fighter_protected(state: GameState, defender: InstanceId) -> bool:
        for iid in state.frontline if d.lane == Lane.FRONTLINE else state.supportline[
            state.other(pid)
        ]:
            inst = state.get_instance(iid)
            defn = state.get_def(inst.def_id)
            if (
                defn.unit_class == UnitClass.FIGHTER
                and inst.current_health is not None
                and inst.current_health > 0
            ):
                return False
        return True

    uc = attacker_def.unit_class

    if uc == UnitClass.INFANTRY:
        require(
            is_adjacent_lane(state, a.lane, d.lane),
            "infantry can only attack adjacent lanes",
        )
        require(no_guard_protected(state, defender), "must attack guard unit first")
    elif uc == UnitClass.TANK:
        require(
            is_adjacent_lane(state, a.lane, d.lane),
            "tank can only attack adjacent lanes",
        )
        require(no_guard_protected(state, defender), "must attack guard unit first")
    elif uc == UnitClass.ARTILLERY:
        pass
    elif uc == UnitClass.FIGHTER:
        require(no_guard_protected(state, defender), "must attack guard unit first")
    elif uc == UnitClass.BOMBER:
        require(no_guard_protected(state, defender), "must attack guard unit first")
        require(no_fighter_protected(state, defender), "must attack fighter unit first")
