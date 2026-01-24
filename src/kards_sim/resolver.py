from __future__ import annotations

from dataclasses import dataclass
from typing import Deque
from collections import deque

from .actions import Attack, EndTurn, PlayCard, Advance
from .abilities.registry import AbilityRegistry, default_registry
from .events import (
    CardPlayed,
    DamageDealt,
    Event,
    TurnEnded,
    TurnStarted,
    UnitDeployed,
    UnitDestroyed,
)
from .rules import (
    RuleViolation,
    can_attack,
    can_deploy_unit,
    can_play_card,
    can_advance_unit,
    require,
)
from .state import GameState
from .types import CardType, InstanceId, Lane, PlayerId, UnitClass, Zone


@dataclass(slots=True)
class StepResult:
    state: GameState
    events: list[Event]
    violation: RuleViolation | None = None


def enqueue_draw(state: GameState, pid: PlayerId) -> InstanceId | None:
    player = state.players[pid]
    if not player.deck:
        return None
    top = player.deck.pop(0)
    player.hand.append(top)
    inst = state.get_instance(top)
    inst.zone = Zone.HAND
    inst.pos = None
    return top


def _destroy_unit(state: GameState, unit: InstanceId) -> None:
    inst = state.get_instance(unit)
    if inst.zone != Zone.BOARD or inst.lane is None:
        return
    owner = inst.owner
    lane = inst.lane
    if lane == Lane.FRONTLINE:
        state.frontline.remove(unit)
    else:
        state.supportline[owner].remove(unit)
    inst.zone = Zone.DISCARD
    inst.lane = None
    state.players[owner].discard.append(unit)


def _apply_damage_to_unit(state: GameState, unit: InstanceId, amount: int) -> None:
    inst = state.get_instance(unit)
    require(inst.zone == Zone.BOARD, "damage target not on board")
    inst.damage_taken += amount


def _check_deaths(state: GameState) -> list[UnitDestroyed]:
    destroyed: list[UnitDestroyed] = []
    for iid, inst in list(state.instances.items()):
        if inst.zone == Zone.BOARD and inst.is_dead:
            destroyed.append(UnitDestroyed(unit=iid))
    return destroyed


def _end_turn_bookkeeping(state: GameState) -> None:
    # Switch active player
    state.active_player = state.other(state.active_player)
    state.turn += 1
    # Refresh credits and units
    p = state.players[state.active_player]
    ### TODO: check if max_credits < 12
    p.max_credits = min(p.max_credits + 1, 12)
    p.credits = p.max_credits
    for iid in state.all_board_unit_ids():
        inst = state.get_instance(iid)
        if inst.owner == state.active_player and inst.zone == Zone.BOARD:
            inst.exhausted = False


class Resolver:
    def __init__(self, registry: AbilityRegistry | None = None) -> None:
        self.registry = registry or default_registry()
        self._bound_abilities: dict[int, list] = {}

    def _get_bound(self, state: GameState, iid: InstanceId):
        key = int(iid)
        if key not in self._bound_abilities:
            defn = state.get_def(state.get_instance(iid).def_id)
            self._bound_abilities[key] = self.registry.instantiate_for_card(key, defn)
        return self._bound_abilities[key]

    def step(self, state: GameState, action) -> StepResult:
        events: list[Event] = []
        q: Deque[Event] = deque()

        try:
            # Translate action -> initial event(s)
            if isinstance(action, PlayCard):
                can_play_card(state, action.player_id, action.card)
                inst = state.get_instance(action.card)
                defn = state.get_def(inst.def_id)
                player = state.players[action.player_id]
                q.append(
                    CardPlayed(
                        player_id=action.player_id,
                        card=action.card,
                        target=action.target,
                        target_player=(
                            state.other(action.player_id) if action.target_hq else None
                        ),
                    )
                )

                if defn.card_type == CardType.UNIT:
                    require(action.index is not None, "unit requires index")
                    assert action.index is not None
                    can_deploy_unit(state, action.player_id, action.card, action.index)

                    player.credits -= defn.cost
                    player.hand.remove(action.card)
                    state.supportline[action.player_id].insert(
                        action.index, action.card
                    )

                    inst.cost = defn.acost
                    inst.zone = Zone.BOARD
                    inst.lane = Lane.SUPPORTLINE
                    inst.exhausted = True

                    q.append(
                        UnitDeployed(
                            player_id=action.player_id,
                            unit=action.card,
                            pos=action.index,
                        )
                    )
                else:
                    # Move order to discard
                    inst.lane = None
                    inst.zone = Zone.DISCARD
                    player.credits -= defn.cost
                    player.discard.append(action.card)
                    player.hand.remove(action.card)

            elif isinstance(action, Advance):
                can_advance_unit(state, action.player_id, action.card, action.index)
                inst = state.get_instance(action.card)
                # Move unit from supportline to frontline
                assert inst.cost is not None
                state.players[action.player_id].credits -= inst.cost
                state.supportline[action.player_id].remove(action.card)
                state.frontline.insert(action.index, action.card)
                inst.lane = Lane.FRONTLINE

            elif isinstance(action, Attack):
                can_attack(
                    state,
                    action.player_id,
                    action.attacker,
                    action.defender,
                )
                a = state.get_instance(action.attacker)
                a.exhausted = True

                assert action.defender is not None
                d = state.get_instance(action.defender)

                a_def = state.get_def(a.def_id)
                d_def = state.get_def(d.def_id)

                def has_retaliatory_damage() -> bool:
                    if d_def.card_type == CardType.BASE:
                        return False
                    if a_def.unit_class == UnitClass.ARTILLERY:
                        return False
                    if (
                        a_def.unit_class == UnitClass.BOMBER
                        and d_def.unit_class != UnitClass.FIGHTER
                    ):
                        return False
                    if d_def.unit_class == UnitClass.BOMBER:
                        return False
                    return True

                # Keyword check: ambush on the defender means defender strikes first.
                has_ambush = any(
                    spec.ability_id.lower() == "ambush" for spec in d_def.abilities
                )

                assert a.current_health is not None
                assert d.current_health is not None
                assert a.attack is not None
                if has_ambush:
                    assert d.attack is not None
                    q.append(
                        DamageDealt(
                            source=action.defender,
                            target=action.attacker,
                            amount=d.attack,
                        )
                    )
                    if d.attack < a.current_health:
                        q.append(
                            DamageDealt(
                                source=action.attacker,
                                target=action.defender,
                                amount=a.attack,
                            )
                        )
                elif has_retaliatory_damage():
                    q.append(
                        DamageDealt(
                            source=action.attacker,
                            target=action.defender,
                            amount=a.attack,
                        )
                    )
                    assert d.attack is not None
                    q.append(
                        DamageDealt(
                            source=action.defender,
                            target=action.attacker,
                            amount=d.attack,
                        )
                    )
                else:
                    q.append(
                        DamageDealt(
                            source=action.attacker,
                            target=action.defender,
                            amount=a.attack,
                        )
                    )

            elif isinstance(action, EndTurn):
                require(action.player_id == state.active_player, "not your turn")
                q.append(TurnEnded(player_id=action.player_id))
            else:
                raise RuleViolation("unknown action")

            # Resolve queue
            while q:
                ev = q.popleft()
                events.append(ev)

                # Apply event to state
                if isinstance(ev, DamageDealt):
                    if ev.target is not None:
                        _apply_damage_to_unit(state, ev.target, ev.amount)

                    for d_ev in _check_deaths(state):
                        q.append(d_ev)

                elif isinstance(ev, UnitDestroyed):
                    _destroy_unit(state, ev.unit)

                elif isinstance(ev, TurnEnded):
                    _end_turn_bookkeeping(state)
                    q.append(TurnStarted(player_id=state.active_player))

                # Trigger abilities bound to source cards on board/discard etc.
                # (We keep it simple: only abilities on the relevant card instance listen.)
                # This is enough to start adding KARDS timing rules incrementally.
                # Trigger abilities that belong to the source card of this event (when applicable).
                # This keeps early prototype performance reasonable and avoids accidental triggers.
                source_candidates: list[int] = []
                if hasattr(ev, "card"):
                    source_candidates.append(int(getattr(ev, "card")))
                if hasattr(ev, "unit"):
                    source_candidates.append(int(getattr(ev, "unit")))
                if hasattr(ev, "source") and getattr(ev, "source") is not None:
                    source_candidates.append(int(getattr(ev, "source")))

                for key in dict.fromkeys(source_candidates):
                    if key <= 0:
                        continue
                    try:
                        bound = self._get_bound(state, InstanceId(key))
                    except KeyError:
                        continue
                    for ab in bound:
                        if ab.trigger(state, ev):
                            for new_ev in ab.handler(state, ev):
                                q.append(new_ev)

            return StepResult(state=state, events=events)

        except RuleViolation as e:
            return StepResult(state=state, events=events, violation=e)
