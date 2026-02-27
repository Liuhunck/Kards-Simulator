from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque

from .actions import Advance, Attack, EndTurn, PlayCard
from .events import (
    BuffApplied,
    CardDrawn,
    CardPlayed,
    DamageDealt,
    Event,
    GameOver,
    HealApplied,
    Trigger,
    TriggerContext,
    TurnEnded,
    TurnStarted,
    UnitAdvanced,
    UnitDeployed,
    UnitDestroyed,
)
from .rules import RuleViolation, require
from .state import GameState
from .types import CardType, InstanceId, Keyword, Lane, PlayerId, UnitClass, Zone


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
    ci = state.inst(top)
    ci.zone = Zone.HAND
    return top


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _destroy_unit(state: GameState, unit: InstanceId) -> None:
    ci = state.inst(unit)
    if ci.zone != Zone.BOARD or ci.lane == Lane.NOT_ON_BOARD:
        return
    owner = ci.owner
    if ci.lane == Lane.FRONTLINE:
        if unit in state.frontline:
            state.frontline.remove(unit)
    else:
        if unit in state.supportline[owner]:
            state.supportline[owner].remove(unit)
    ci.zone = Zone.DISCARD
    ci.lane = Lane.NOT_ON_BOARD
    state.players[owner].discard.append(unit)


def _check_deaths(state: GameState) -> list[UnitDestroyed]:
    destroyed: list[UnitDestroyed] = []
    for iid, ci in list(state.instances.items()):
        if ci.zone == Zone.BOARD and ci.current_health <= 0:
            destroyed.append(UnitDestroyed(unit=iid))
    return destroyed


def _check_game_over(state: GameState) -> GameOver | None:
    for pid, p in state.players.items():
        hq = state.inst(p.hq_iid)
        if hq.current_health <= 0:
            winner = state.opponent(pid)
            state.game_over = True
            state.winner = winner
            return GameOver(winner=winner)
    return None


def _end_turn_bookkeeping(state: GameState) -> None:
    state.active_player = state.opponent(state.active_player)
    state.turn += 1
    p = state.players[state.active_player]
    p.max_credits = min(p.max_credits + 1, 12)
    p.credits = p.max_credits
    for iid in state.board_unit_iids():
        ci = state.inst(iid)
        if ci.owner == state.active_player and ci.zone == Zone.BOARD:
            ci.exhausted = False
            ci.attacks_this_turn = 0
            ci.ambush_available = True


# ---------------------------------------------------------------------------
# Deploy / advance / attack resolution
# ---------------------------------------------------------------------------

def _resolve_deploy_unit(state: GameState, action: PlayCard) -> list[Event]:
    """Deploy a unit from hand to supportline."""
    from .rules import can_deploy_unit, can_play_card

    iid = action.card
    can_play_card(state, action.player_id, iid)
    require(action.index is not None, "unit requires deployment index")
    assert action.index is not None
    can_deploy_unit(state, action.player_id, iid, action.index)

    ci = state.inst(iid)
    player = state.players[action.player_id]

    player.credits -= ci.card.cost
    player.hand.remove(iid)
    state.supportline[action.player_id].insert(action.index, iid)

    ci.zone = Zone.BOARD
    ci.lane = Lane.SUPPORTLINE
    ci.exhausted = not state.has_keyword(iid, Keyword.BLITZ)

    if state.has_keyword(iid, Keyword.SMOKESCREEN):
        ci.smokescreen_active = True

    return [
        CardPlayed(
            player_id=action.player_id,
            card=iid,
            target=action.target,
            target_player=(
                state.opponent(action.player_id) if action.target_hq else None
            ),
        ),
        UnitDeployed(
            player_id=action.player_id,
            unit=iid,
            position=action.index,
        ),
    ]


def _resolve_play_order(state: GameState, action: PlayCard) -> list[Event]:
    """Play an order card from hand (one-time effect, then discard)."""
    from .rules import can_play_card, require

    iid = action.card
    can_play_card(state, action.player_id, iid)

    if action.target is not None:
        target_card = state.card(action.target)
        target_ci = state.inst(action.target)
        if target_ci.owner != action.player_id and target_card.order_immune:
            require(False, "target is immune to enemy orders")

    ci = state.inst(iid)
    player = state.players[action.player_id]

    player.credits -= ci.card.cost
    player.hand.remove(iid)
    ci.zone = Zone.DISCARD
    ci.lane = Lane.NOT_ON_BOARD
    player.discard.append(iid)

    return [
        CardPlayed(
            player_id=action.player_id,
            card=iid,
            target=action.target,
            target_player=(
                state.opponent(action.player_id) if action.target_hq else None
            ),
        ),
    ]


def _resolve_play_countermeasure(state: GameState, action: PlayCard) -> list[Event]:
    """Set a countermeasure from hand."""
    from .rules import can_play_card

    iid = action.card
    can_play_card(state, action.player_id, iid)

    ci = state.inst(iid)
    player = state.players[action.player_id]

    player.credits -= ci.card.cost
    player.hand.remove(iid)
    player.countermeasures.append(iid)

    return [
        CardPlayed(
            player_id=action.player_id,
            card=iid,
        ),
    ]


def _resolve_advance(state: GameState, action: Advance) -> list[Event]:
    """Move a unit from supportline to frontline."""
    from .rules import can_advance_unit

    iid = action.card
    can_advance_unit(state, action.player_id, iid, action.index)

    ci = state.inst(iid)
    player = state.players[action.player_id]

    player.credits -= ci.operation_cost
    state.supportline[action.player_id].remove(iid)
    state.frontline.insert(action.index, iid)
    ci.lane = Lane.FRONTLINE

    if ci.smokescreen_active:
        ci.smokescreen_active = False

    return [
        UnitAdvanced(
            player_id=action.player_id,
            unit=iid,
            position=action.index,
        ),
    ]


def _resolve_attack(state: GameState, action: Attack) -> list[Event]:
    """Resolve combat between attacker and defender."""
    from .rules import can_attack

    iid = action.attacker
    can_attack(state, action.player_id, iid, action.defender)

    a_ci = state.inst(iid)
    state.players[action.player_id].credits -= a_ci.operation_cost
    a_ci.exhausted = True
    a_ci.attacks_this_turn += 1

    if a_ci.smokescreen_active:
        a_ci.smokescreen_active = False

    assert action.defender is not None
    d_ci = state.inst(action.defender)

    a_card = a_ci.card
    d_card = d_ci.card

    a_atk = a_ci.current_attack
    d_atk = d_ci.current_attack

    # Heavy Armor damage reduction (by level)
    effective_a_atk = a_atk
    if state.has_keyword(action.defender, Keyword.HEAVY_ARMOR):
        effective_a_atk = max(0, a_atk - d_card.heavy_armor)
    effective_d_atk = d_atk
    if state.has_keyword(iid, Keyword.HEAVY_ARMOR):
        effective_d_atk = max(0, d_atk - a_card.heavy_armor)

    def _has_retaliation() -> bool:
        if d_card.card_type == CardType.HEADQUARTERS:
            return False
        a_uc = getattr(a_card, "unit_class", None)
        d_uc = getattr(d_card, "unit_class", None)
        if a_uc == UnitClass.ARTILLERY:
            return False
        if a_uc == UnitClass.BOMBER and d_uc != UnitClass.FIGHTER:
            return False
        if d_uc == UnitClass.BOMBER:
            return False
        return True

    has_ambush = state.has_keyword(action.defender, Keyword.AMBUSH) and d_ci.ambush_available
    if has_ambush:
        d_ci.ambush_available = False

    out: list[Event] = []

    if has_ambush:
        out.append(
            DamageDealt(source=action.defender, target=iid, target_player=None, amount=effective_d_atk)
        )
        if effective_d_atk < a_ci.current_health:
            out.append(
                DamageDealt(source=iid, target=action.defender, target_player=None, amount=effective_a_atk)
            )
    elif _has_retaliation():
        out.append(
            DamageDealt(source=iid, target=action.defender, target_player=None, amount=effective_a_atk)
        )
        out.append(
            DamageDealt(source=action.defender, target=iid, target_player=None, amount=effective_d_atk)
        )
    else:
        if d_card.card_type == CardType.HEADQUARTERS:
            target_pid = d_ci.owner
            out.append(
                DamageDealt(source=iid, target=None, target_player=target_pid, amount=effective_a_atk)
            )
        else:
            out.append(
                DamageDealt(source=iid, target=action.defender, target_player=None, amount=effective_a_atk)
            )

    return out


# ---------------------------------------------------------------------------
# Trigger dispatch helpers
# ---------------------------------------------------------------------------

def _trigger_card(
    state: GameState, trigger: Trigger, ctx: TriggerContext, iid: InstanceId
) -> list[Event]:
    card = state.card(iid)
    ctx_with_self = TriggerContext(
        player_id=ctx.player_id,
        source=ctx.source,
        target=ctx.target,
        target_player=ctx.target_player,
        amount=ctx.amount,
        self_iid=iid,
    )
    return card.dispatch_trigger(state, trigger, ctx_with_self)


def _trigger_cards(
    state: GameState, trigger: Trigger, ctx: TriggerContext, iids: list[InstanceId]
) -> list[Event]:
    out: list[Event] = []
    for iid in dict.fromkeys(iids):
        out.extend(_trigger_card(state, trigger, ctx, iid))
    return out


def _trigger_all_board(
    state: GameState, trigger: Trigger, ctx: TriggerContext
) -> list[Event]:
    return _trigger_cards(state, trigger, ctx, state.board_all_iids())


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

class Resolver:
    def step(self, state: GameState, action) -> StepResult:
        if state.game_over:
            return StepResult(state=state, events=[], violation=RuleViolation("game is over"))

        events: list[Event] = []
        q: Deque[Event] = deque()

        try:
            if isinstance(action, PlayCard):
                card = state.card(action.card)
                if card.card_type == CardType.UNIT:
                    for ev in _resolve_deploy_unit(state, action):
                        q.append(ev)
                elif card.card_type == CardType.ORDER:
                    for ev in _resolve_play_order(state, action):
                        q.append(ev)
                elif card.card_type == CardType.COUNTERMEASURE:
                    for ev in _resolve_play_countermeasure(state, action):
                        q.append(ev)
                else:
                    raise RuleViolation(f"cannot play card type: {card.card_type}")

            elif isinstance(action, Advance):
                for ev in _resolve_advance(state, action):
                    q.append(ev)

            elif isinstance(action, Attack):
                ctx = TriggerContext(
                    player_id=action.player_id,
                    source=action.attacker,
                    target=action.defender,
                )
                q.extend(_trigger_cards(state, Trigger.BEFORE_ATTACK, ctx, [action.attacker]))
                if action.defender is not None:
                    q.extend(_trigger_cards(state, Trigger.BEFORE_ATTACK, ctx, [action.defender]))
                for ev in _resolve_attack(state, action):
                    q.append(ev)

            elif isinstance(action, EndTurn):
                require(action.player_id == state.active_player, "not your turn")
                q.append(TurnEnded(player_id=action.player_id))

            else:
                raise RuleViolation("unknown action type")

            # Process event queue
            while q:
                ev = q.popleft()
                events.append(ev)

                if isinstance(ev, UnitDeployed):
                    iid = ev.unit
                    ctx = TriggerContext(player_id=ev.player_id, source=iid)
                    q.extend(_trigger_card(state, Trigger.ON_DEPLOY, ctx, iid))
                    q.extend(_trigger_all_board(state, Trigger.ON_ANY_DEPLOY, ctx))

                elif isinstance(ev, CardPlayed):
                    iid = ev.card
                    ctx = TriggerContext(
                        player_id=ev.player_id,
                        source=iid,
                        target=ev.target,
                        target_player=ev.target_player,
                    )
                    q.extend(_trigger_card(state, Trigger.ON_PLAY, ctx, iid))
                    q.extend(_trigger_all_board(state, Trigger.ON_ANY_PLAY, ctx))

                elif isinstance(ev, UnitAdvanced):
                    iid = ev.unit
                    ctx = TriggerContext(player_id=ev.player_id, source=iid)
                    q.extend(_trigger_card(state, Trigger.ON_ADVANCE, ctx, iid))

                elif isinstance(ev, DamageDealt):
                    target_iid = ev.target
                    if target_iid is None and ev.target_player is not None:
                        target_iid = state.players[ev.target_player].hq_iid

                    ctx = TriggerContext(
                        player_id=state.active_player,
                        source=ev.source,
                        target=target_iid,
                        amount=ev.amount,
                    )

                    if ev.source is not None:
                        q.extend(_trigger_card(state, Trigger.BEFORE_DEAL_DAMAGE, ctx, ev.source))
                    if target_iid is not None:
                        q.extend(_trigger_card(state, Trigger.BEFORE_TAKE_DAMAGE, ctx, target_iid))

                    # Apply damage
                    actual_amount = ev.amount
                    if target_iid is not None and state.has_keyword(target_iid, Keyword.RESISTANCE):
                        card = state.card(target_iid)
                        if ev.source is not None and state.card(ev.source).card_type == CardType.ORDER:
                            actual_amount = max(0, actual_amount - 1)

                    if ev.target is not None:
                        ci = state.inst(ev.target)
                        ci.current_health -= actual_amount
                        if state.has_keyword(ev.target, Keyword.MOBILIZE):
                            ci.mobilize_active = False
                    elif ev.target_player is not None:
                        hq_iid = state.players[ev.target_player].hq_iid
                        state.inst(hq_iid).current_health -= actual_amount

                    if ev.source is not None:
                        q.extend(_trigger_card(state, Trigger.AFTER_DEAL_DAMAGE, ctx, ev.source))
                    if target_iid is not None:
                        q.extend(_trigger_card(state, Trigger.AFTER_TAKE_DAMAGE, ctx, target_iid))

                    for d_ev in _check_deaths(state):
                        q.append(d_ev)

                    game_over = _check_game_over(state)
                    if game_over is not None:
                        q.append(game_over)

                elif isinstance(ev, BuffApplied):
                    ci = state.inst(ev.target)
                    ci.current_attack += ev.attack_delta
                    ci.current_health += ev.health_delta

                elif isinstance(ev, HealApplied):
                    ci = state.inst(ev.target)
                    max_hp = getattr(ci.card, "health_value", None)
                    ci.current_health += ev.amount
                    if max_hp is not None:
                        ci.current_health = min(ci.current_health, max_hp)

                elif isinstance(ev, UnitDestroyed):
                    ctx = TriggerContext(
                        player_id=state.active_player,
                        source=None,
                        target=ev.unit,
                    )
                    q.extend(_trigger_card(state, Trigger.ON_DESTROY, ctx, ev.unit))
                    _destroy_unit(state, ev.unit)
                    q.extend(_trigger_all_board(state, Trigger.ON_ANY_DESTROY, ctx))

                elif isinstance(ev, TurnEnded):
                    ctx = TriggerContext(player_id=ev.player_id)
                    q.extend(_trigger_all_board(state, Trigger.TURN_END, ctx))
                    _end_turn_bookkeeping(state)

                    # Mobilize: +1/+1 for units with active mobilize at turn start
                    for iid in state.board_unit_iids():
                        ci = state.inst(iid)
                        if (
                            ci.owner == state.active_player
                            and ci.mobilize_active
                            and state.has_keyword(iid, Keyword.MOBILIZE)
                        ):
                            q.append(BuffApplied(source=iid, target=iid, attack_delta=1, health_delta=1))

                    # Draw card for new active player
                    drawn = enqueue_draw(state, state.active_player)
                    if drawn is not None:
                        q.append(CardDrawn(player_id=state.active_player, card=drawn))

                    q.append(TurnStarted(player_id=state.active_player))

                elif isinstance(ev, TurnStarted):
                    ctx = TriggerContext(player_id=ev.player_id)
                    q.extend(_trigger_all_board(state, Trigger.TURN_START, ctx))

                elif isinstance(ev, GameOver):
                    pass

                # After-attack triggers
                if isinstance(action, Attack) and ev == events[-1]:
                    a_ctx = TriggerContext(
                        player_id=action.player_id,
                        source=action.attacker,
                        target=action.defender,
                    )
                    after_evs = _trigger_cards(
                        state, Trigger.AFTER_ATTACK, a_ctx,
                        [action.attacker] + ([action.defender] if action.defender else []),
                    )
                    for ae in after_evs:
                        q.append(ae)

            return StepResult(state=state, events=events)

        except RuleViolation as e:
            return StepResult(state=state, events=events, violation=e)
