from __future__ import annotations

from dataclasses import dataclass
from typing import Deque
from collections import deque

from .actions import Attack, EndTurn, PlayCard, Advance
from .cards.abilities.registry import AbilityRegistry, default_registry
from .events import (
    DamageDealt,
    Event,
    Trigger,
    TriggerContext,
    TurnEnded,
    TurnStarted,
    UnitDestroyed,
)
from .rules import RuleViolation, require
from .state import GameState
from .types import InstanceId, Lane, PlayerId, Zone


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
    inst.lane = Lane.NOT_ON_BOARD
    state.players[owner].discard.append(unit)


def _apply_damage_to_unit(state: GameState, unit: InstanceId, amount: int) -> None:
    inst = state.get_instance(unit)
    require(inst.zone == Zone.BOARD, "damage target not on board")
    state.apply_damage(unit, amount)


def _apply_damage_to_player(state: GameState, pid: PlayerId, amount: int) -> None:
    base_iid = state.players[pid].base_card_id
    _apply_damage_to_unit(state, base_iid, amount)


def _check_deaths(state: GameState) -> list[UnitDestroyed]:
    destroyed: list[UnitDestroyed] = []
    for iid, inst in list(state.instances.items()):
        if inst.zone == Zone.BOARD and state.is_dead(iid):
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
            card_cls = state.get_card_for_instance(iid).__class__
            self._bound_abilities[key] = self.registry.instantiate_for_card(
                key, card_cls
            )
        return self._bound_abilities[key]

    def _trigger_cards(
        self,
        state: GameState,
        trigger: Trigger,
        ctx: TriggerContext,
        iids: list[InstanceId],
    ) -> list[Event]:
        out: list[Event] = []
        for iid in dict.fromkeys(iids):
            card = state.get_card_for_instance(iid)
            for ev in card.trigger(state, trigger, ctx):
                out.append(ev)
        return out

    def _trigger_all_board(
        self, state: GameState, trigger: Trigger, ctx: TriggerContext
    ) -> list[Event]:
        return self._trigger_cards(state, trigger, ctx, state.all_board_card_ids())

    def step(self, state: GameState, action) -> StepResult:
        events: list[Event] = []
        q: Deque[Event] = deque()

        try:
            # Translate action -> initial event(s)
            if isinstance(action, PlayCard):
                card = state.get_card_for_instance(action.card)
                for ev in card.deploy(state, action):
                    q.append(ev)

            elif isinstance(action, Advance):
                card = state.get_card_for_instance(action.card)
                for ev in card.advance(state, action):
                    q.append(ev)

            elif isinstance(action, Attack):
                ctx = TriggerContext(
                    player_id=action.player_id,
                    source=action.attacker,
                    target=action.defender,
                )
                for ev in self._trigger_cards(
                    state,
                    Trigger.BEFORE_ATTACK,
                    ctx,
                    [action.attacker, action.defender],
                ):
                    q.append(ev)
                card = state.get_card_for_instance(action.attacker)
                for ev in card.attack(state, action):
                    q.append(ev)
                for ev in self._trigger_cards(
                    state, Trigger.AFTER_ATTACK, ctx, [action.attacker, action.defender]
                ):
                    q.append(ev)

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
                    target_iid = ev.target
                    if target_iid is None and ev.target_player is not None:
                        target_iid = state.players[ev.target_player].base_card_id
                    ctx = TriggerContext(
                        player_id=state.active_player,
                        source=ev.source,
                        target=target_iid,
                        amount=ev.amount,
                    )
                    if ev.source is not None:
                        for t_ev in self._trigger_cards(
                            state, Trigger.BEFORE_DEAL_DAMAGE, ctx, [ev.source]
                        ):
                            q.append(t_ev)
                    if target_iid is not None:
                        for t_ev in self._trigger_cards(
                            state, Trigger.BEFORE_TAKE_DAMAGE, ctx, [target_iid]
                        ):
                            q.append(t_ev)
                    if ev.target is not None:
                        _apply_damage_to_unit(state, ev.target, ev.amount)
                    elif ev.target_player is not None:
                        _apply_damage_to_player(state, ev.target_player, ev.amount)

                    if ev.source is not None:
                        for t_ev in self._trigger_cards(
                            state, Trigger.AFTER_DEAL_DAMAGE, ctx, [ev.source]
                        ):
                            q.append(t_ev)
                    if target_iid is not None:
                        for t_ev in self._trigger_cards(
                            state, Trigger.AFTER_TAKE_DAMAGE, ctx, [target_iid]
                        ):
                            q.append(t_ev)

                    for d_ev in _check_deaths(state):
                        q.append(d_ev)

                elif isinstance(ev, UnitDestroyed):
                    ctx = TriggerContext(
                        player_id=state.active_player,
                        source=None,
                        target=ev.unit,
                    )
                    for t_ev in self._trigger_cards(
                        state, Trigger.ON_DEATH, ctx, [ev.unit]
                    ):
                        q.append(t_ev)
                    _destroy_unit(state, ev.unit)
                    for t_ev in self._trigger_cards(
                        state, Trigger.AFTER_DEATH, ctx, [ev.unit]
                    ):
                        q.append(t_ev)

                elif isinstance(ev, TurnEnded):
                    ctx = TriggerContext(player_id=ev.player_id)
                    for t_ev in self._trigger_all_board(state, Trigger.TURN_END, ctx):
                        q.append(t_ev)
                    _end_turn_bookkeeping(state)
                    q.append(TurnStarted(player_id=state.active_player))

                elif isinstance(ev, TurnStarted):
                    ctx = TriggerContext(player_id=ev.player_id)
                    for t_ev in self._trigger_all_board(state, Trigger.TURN_START, ctx):
                        q.append(t_ev)

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
