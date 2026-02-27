from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .types import InstanceId, PlayerId


# ---------------------------------------------------------------------------
# Trigger enum – every moment in the game where card abilities can fire
# ---------------------------------------------------------------------------

class Trigger(str, Enum):
    # Turn lifecycle
    TURN_START = "turn_start"
    TURN_END = "turn_end"

    # Deployment / play
    ON_DEPLOY = "on_deploy"
    ON_PLAY = "on_play"
    ON_ANY_DEPLOY = "on_any_deploy"
    ON_ANY_PLAY = "on_any_play"

    # Movement
    ON_ADVANCE = "on_advance"
    ON_RETREAT = "on_retreat"

    # Combat
    BEFORE_ATTACK = "before_attack"
    AFTER_ATTACK = "after_attack"

    # Damage
    BEFORE_DEAL_DAMAGE = "before_deal_damage"
    AFTER_DEAL_DAMAGE = "after_deal_damage"
    BEFORE_TAKE_DAMAGE = "before_take_damage"
    AFTER_TAKE_DAMAGE = "after_take_damage"

    # Destruction
    ON_DESTROY = "on_destroy"
    ON_ANY_DESTROY = "on_any_destroy"

    # Buff / debuff
    ON_BUFF = "on_buff"
    ON_HEAL = "on_heal"


# ---------------------------------------------------------------------------
# Trigger context – passed to every ability hook
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class TriggerContext:
    player_id: PlayerId | None = None
    source: InstanceId | None = None
    target: InstanceId | None = None
    target_player: PlayerId | None = None
    amount: int | None = None
    self_iid: InstanceId | None = None
    """The instance ID of the card whose hook is being invoked."""


# ---------------------------------------------------------------------------
# Event hierarchy – atomic state mutations queued by the resolver
# ---------------------------------------------------------------------------

class Event:
    """Base class for all events processed by the resolver."""


@dataclass(frozen=True, slots=True)
class TurnStarted(Event):
    player_id: PlayerId


@dataclass(frozen=True, slots=True)
class TurnEnded(Event):
    player_id: PlayerId


@dataclass(frozen=True, slots=True)
class CardDrawn(Event):
    player_id: PlayerId
    card: InstanceId


@dataclass(frozen=True, slots=True)
class CardPlayed(Event):
    player_id: PlayerId
    card: InstanceId
    target: InstanceId | None = None
    target_player: PlayerId | None = None


@dataclass(frozen=True, slots=True)
class UnitDeployed(Event):
    player_id: PlayerId
    unit: InstanceId
    position: int


@dataclass(frozen=True, slots=True)
class UnitAdvanced(Event):
    player_id: PlayerId
    unit: InstanceId
    position: int


@dataclass(frozen=True, slots=True)
class UnitRetreated(Event):
    player_id: PlayerId
    unit: InstanceId


@dataclass(frozen=True, slots=True)
class DamageDealt(Event):
    source: InstanceId | None
    target: InstanceId | None
    target_player: PlayerId | None
    amount: int


@dataclass(frozen=True, slots=True)
class HealApplied(Event):
    source: InstanceId | None
    target: InstanceId
    amount: int


@dataclass(frozen=True, slots=True)
class BuffApplied(Event):
    source: InstanceId | None
    target: InstanceId
    attack_delta: int = 0
    health_delta: int = 0


@dataclass(frozen=True, slots=True)
class UnitDestroyed(Event):
    unit: InstanceId


@dataclass(frozen=True, slots=True)
class GameOver(Event):
    winner: PlayerId
