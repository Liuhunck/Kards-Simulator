from __future__ import annotations

from dataclasses import dataclass

from .state import GameState
from .types import CardType, InstanceId, Keyword, Lane, PlayerId, UnitClass, Zone


@dataclass(frozen=True, slots=True)
class RuleViolation(Exception):
    reason: str

    def __str__(self) -> str:  # pragma: no cover
        return self.reason


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuleViolation(reason)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def can_play_card(state: GameState, pid: PlayerId, iid: InstanceId) -> None:
    player = state.players[pid]
    require(pid == state.active_player, "not your turn")
    require(iid in player.hand, "card not in hand")
    ci = state.inst(iid)
    require(ci.owner == pid, "not your card")
    card = ci.card
    cost = getattr(card, "cost", None)
    require(cost is not None, "card missing cost")
    require(player.credits >= int(cost), "not enough credits")


def can_deploy_unit(
    state: GameState, pid: PlayerId, iid: InstanceId, pos: int
) -> None:
    card = state.card(iid)
    require(card.card_type == CardType.UNIT, "not a unit")
    require(
        len(state.supportline[pid]) < state.config.columns,
        "supportline is full",
    )
    require(
        0 <= pos <= len(state.supportline[pid]),
        "index out of supportline range",
    )


def can_advance_unit(
    state: GameState, pid: PlayerId, iid: InstanceId, pos: int
) -> None:
    ci = state.inst(iid)
    require(ci.owner == pid, "not your unit")
    require(ci.zone == Zone.BOARD, "unit not on board")
    require(ci.lane == Lane.SUPPORTLINE, "unit not in supportline")
    require(not ci.exhausted, "unit exhausted")
    require(state.card_type_of(iid) == CardType.UNIT, "not a unit")
    require(
        state.frontline_owner() != state.opponent(pid),
        "cannot advance when enemy controls frontline",
    )
    require(
        len(state.frontline) < state.config.columns,
        "frontline is full",
    )
    require(0 <= pos <= len(state.frontline), "index out of frontline range")
    require(
        state.players[pid].credits >= ci.operation_cost,
        "not enough credits",
    )
    require(iid in state.supportline[pid], "unit not in your supportline")
    require(ci.current_health > 0, "unit dead")


def can_attack(
    state: GameState,
    pid: PlayerId,
    attacker: InstanceId,
    defender: InstanceId | None,
) -> None:
    require(pid == state.active_player, "not your turn")
    a = state.inst(attacker)
    require(a.owner == pid, "not your unit")
    require(a.zone == Zone.BOARD, "attacker not on board")
    require(a.lane != Lane.NOT_ON_BOARD, "attacker missing lane")
    require(not a.exhausted, "attacker exhausted")
    require(state.card_type_of(attacker) == CardType.UNIT, "attacker not a unit")
    require(a.current_health > 0, "attacker dead")

    a_card = state.card(attacker)
    a_uc = getattr(a_card, "unit_class", None)
    require(a_uc is not None, "attacker missing unit_class")

    # Fury allows two attacks per turn; otherwise only one
    max_attacks = 2 if state.has_keyword(attacker, Keyword.FURY) else 1
    require(a.attacks_this_turn < max_attacks, "unit has already attacked")

    require(
        state.players[pid].credits >= a.operation_cost,
        "not enough credits for attack",
    )

    require(defender is not None, "missing defender")
    assert defender is not None
    d = state.inst(defender)
    require(d.owner == state.opponent(pid), "defender must be enemy")
    require(d.zone == Zone.BOARD, "defender not on board")
    require(d.lane != Lane.NOT_ON_BOARD, "defender missing lane")

    # Smokescreen: cannot attack a unit with active smokescreen
    if state.has_keyword(defender, Keyword.SMOKESCREEN) and d.smokescreen_active:
        d_card = state.card(defender)
        if d_card.card_type != CardType.HEADQUARTERS:
            require(False, "target has smokescreen")

    # Adjacency rules
    _check_adjacency(state, a.lane, d.lane, a_uc, attacker)

    # Guard protection
    _check_guard(state, pid, defender, d.lane, a_uc)

    # Fighter protection for bombers
    _check_fighter_protection(state, pid, defender, d.lane, a_uc)


def _check_adjacency(
    state: GameState,
    a_lane: Lane,
    d_lane: Lane,
    a_uc: UnitClass,
    attacker: InstanceId,
) -> None:
    """Ground units (infantry, tanks) can only attack adjacent lanes.
    Artillery, fighters, bombers have no lane restriction.
    """
    if a_uc in (UnitClass.INFANTRY, UnitClass.TANK):
        if state.has_keyword(attacker, Keyword.LONG_RANGE):
            return
        adjacent = (
            (a_lane == Lane.SUPPORTLINE and d_lane == Lane.FRONTLINE)
            or (a_lane == Lane.FRONTLINE and d_lane == Lane.SUPPORTLINE)
            or (a_lane == Lane.FRONTLINE and d_lane == Lane.FRONTLINE)
        )
        require(adjacent, f"{a_uc.value} can only attack adjacent lanes")


def _check_guard(
    state: GameState,
    pid: PlayerId,
    defender: InstanceId,
    d_lane: Lane,
    a_uc: UnitClass,
) -> None:
    """Guard units protect adjacent non-guard units.
    Bombers and artillery ignore guard.
    """
    if a_uc in (UnitClass.BOMBER, UnitClass.ARTILLERY):
        return

    if state.has_keyword(defender, Keyword.GUARD):
        return

    def _has_adjacent_guard(lane_list: list[InstanceId], target: InstanceId) -> bool:
        if target not in lane_list:
            return False
        idx = lane_list.index(target)
        for neighbor_idx in (idx - 1, idx + 1):
            if 0 <= neighbor_idx < len(lane_list):
                neighbor = lane_list[neighbor_idx]
                if state.has_keyword(neighbor, Keyword.GUARD) and state.inst(neighbor).current_health > 0:
                    return True
        return False

    opponent = state.opponent(pid)
    if d_lane == Lane.FRONTLINE:
        require(
            not _has_adjacent_guard(state.frontline, defender),
            "must attack guard unit first",
        )
    elif d_lane == Lane.SUPPORTLINE:
        require(
            not _has_adjacent_guard(state.supportline[opponent], defender),
            "must attack guard unit first",
        )


def _check_fighter_protection(
    state: GameState,
    pid: PlayerId,
    defender: InstanceId,
    d_lane: Lane,
    a_uc: UnitClass,
) -> None:
    """Bombers must target fighters first if any are alive in the same lane."""
    if a_uc != UnitClass.BOMBER:
        return

    d_card = state.card(defender)
    if getattr(d_card, "unit_class", None) == UnitClass.FIGHTER:
        return

    opponent = state.opponent(pid)
    lane_list = (
        state.frontline if d_lane == Lane.FRONTLINE else state.supportline[opponent]
    )
    for iid in lane_list:
        ci = state.inst(iid)
        card = ci.card
        if (
            getattr(card, "unit_class", None) == UnitClass.FIGHTER
            and ci.current_health > 0
        ):
            require(False, "must attack fighter unit first")
