from __future__ import annotations

from dataclasses import dataclass

from .types import BoardPos, InstanceId, PlayerId


class Action:
    """Player-intent action. The engine validates and resolves it."""


@dataclass(frozen=True, slots=True)
class PlayCard(Action):
    player_id: PlayerId
    card: InstanceId
    index: int | None = None
    target: InstanceId | None = None
    target_hq: bool = False


@dataclass(frozen=True, slots=True)
class Attack(Action):
    player_id: PlayerId
    attacker: InstanceId
    defender: InstanceId | None = None
    defender_hq: bool = False


@dataclass(frozen=True, slots=True)
class EndTurn(Action):
    player_id: PlayerId
