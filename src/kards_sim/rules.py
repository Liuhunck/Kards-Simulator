from __future__ import annotations

from dataclasses import dataclass

from .state import GameState
from .types import BoardPos, CardType, InstanceId, Lane, PlayerId, Zone


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


def can_attack(
    state: GameState,
    pid: PlayerId,
    attacker: InstanceId,
    defender: InstanceId | None,
    defender_hq: bool,
) -> None:
    require(pid == state.active_player, "not your turn")
    a = state.get_instance(attacker)
    require(a.owner == pid, "not your unit")
    require(a.zone == Zone.BOARD, "attacker not on board")
    require(a.pos is not None, "attacker missing board pos")
    require(not a.exhausted, "attacker exhausted")
    require(state.card_type_of(attacker) == CardType.UNIT, "attacker not a unit")
    require(a.current_health is not None and a.current_health > 0, "attacker dead")

    # Faithful KARDS combat rules have nuances; this is a conservative first-pass:
    # - Default target is opposing unit in same column.
    # - HQ can only be attacked from FRONTLINE when opposing slot is empty.
    if defender_hq:
        require(a.lane == Lane.FRONTLINE, "only frontline units can attack HQ")
        # In KARDS, HQ is typically protected by enemy frontline units.
        # With compacted slots (no fixed columns), we model this as: cannot attack HQ
        # while the opponent has any unit on the frontline.
        opp = state.other(pid)
        require(
            all(
                (iid is None) or (state.get_instance(iid).owner != opp)
                for iid in state.frontline
            ),
            "cannot attack HQ while enemy controls frontline",
        )
        return

    require(defender is not None, "missing defender")
    assert defender is not None
    d = state.get_instance(defender)
    require(d.owner == state.other(pid), "defender must be enemy")
    require(d.zone == Zone.BOARD, "defender not on board")
    require(d.pos is not None, "defender missing board pos")
    # Compacting layout: no fixed columns for combat; targeting is by instance id.
