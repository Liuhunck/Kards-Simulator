from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .types import BoardPos, InstanceId, PlayerId


class Event:
    """Atomic event processed by the resolver queue."""


class Trigger(str, Enum):
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    BEFORE_ATTACK = "before_attack"
    AFTER_ATTACK = "after_attack"
    BEFORE_DEAL_DAMAGE = "before_deal_damage"
    AFTER_DEAL_DAMAGE = "after_deal_damage"
    BEFORE_TAKE_DAMAGE = "before_take_damage"
    AFTER_TAKE_DAMAGE = "after_take_damage"
    ON_DEATH = "on_death"
    AFTER_DEATH = "after_death"


@dataclass(frozen=True, slots=True)
class TriggerContext:
    player_id: PlayerId | None = None
    source: InstanceId | None = None
    target: InstanceId | None = None
    amount: int | None = None


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
    target_player: PlayerId | None = None  ### 没用


@dataclass(frozen=True, slots=True)
class UnitDeployed(Event):
    player_id: PlayerId
    unit: InstanceId
    pos: int


@dataclass(frozen=True, slots=True)
class UnitAdvanced(Event):
    player_id: PlayerId
    unit: InstanceId
    pos: int


@dataclass(frozen=True, slots=True)
class DamageDealt(Event):
    source: InstanceId | None
    target: InstanceId | None
    target_player: PlayerId | None
    amount: int


@dataclass(frozen=True, slots=True)
class UnitDestroyed(Event):
    unit: InstanceId
