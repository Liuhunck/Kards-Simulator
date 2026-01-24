from __future__ import annotations

from dataclasses import dataclass

from .types import BoardPos, InstanceId, PlayerId


class Event:
    """Atomic event processed by the resolver queue."""


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
class DamageDealt(Event):
    source: InstanceId | None
    target: InstanceId | None
    amount: int


@dataclass(frozen=True, slots=True)
class UnitDestroyed(Event):
    unit: InstanceId
