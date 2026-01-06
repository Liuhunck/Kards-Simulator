from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import CardType


@dataclass(frozen=True, slots=True)
class AbilitySpec:
    """Data-driven ability reference.

    `ability_id` maps to an implementation in the ability registry.
    `params` are passed to the implementation factory.
    """

    ability_id: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CardDefinition:
    """Static card definition loaded from data."""

    def_id: str
    name: str
    card_type: CardType
    cost: int
    acost: int
    attack: int | None = None
    health: int | None = None
    abilities: tuple[AbilitySpec, ...] = ()


def validate_definition(defn: CardDefinition) -> None:
    if defn.cost < 0:
        raise ValueError(f"cost must be >= 0: {defn.def_id}")
    if defn.card_type == CardType.UNIT:
        if defn.attack is None or defn.health is None:
            raise ValueError(f"unit must have attack/health: {defn.def_id}")
        if defn.attack < 0 or defn.health <= 0:
            raise ValueError(f"invalid unit stats: {defn.def_id}")
    elif defn.card_type == CardType.ORDER:
        if defn.attack is not None or defn.health is not None:
            raise ValueError(f"order must not have attack/health: {defn.def_id}")
    elif defn.card_type == CardType.BASE:
        pass
