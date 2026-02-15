from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..types import CardType, Nation

if TYPE_CHECKING:
    from .base import CardBase


@dataclass(frozen=True, slots=True)
class AbilitySpec:
    ability_id: str
    params: dict[str, Any] = field(default_factory=dict)


def validate_card_class(card_cls: type["CardBase"]) -> None:
    card_name = card_cls.__name__
    nation = getattr(card_cls, "nation", None)
    card_type = getattr(card_cls, "card_type", None)
    cost = getattr(card_cls, "cost", None)
    acost = getattr(card_cls, "acost", None)
    unit_class = getattr(card_cls, "unit_class", None)
    attack_value = getattr(card_cls, "attack_value", None)
    health_value = getattr(card_cls, "health_value", None)
    abilities = getattr(card_cls, "abilities", ())

    if not isinstance(nation, Nation):
        raise ValueError(f"nation must be Nation enum: {card_name}")
    if not isinstance(card_type, CardType):
        raise ValueError(f"card_type must be CardType enum: {card_name}")
    if not isinstance(abilities, tuple):
        raise ValueError(f"abilities must be tuple: {card_name}")

    if card_type == CardType.UNIT:
        if not isinstance(cost, int) or cost < 0:
            raise ValueError(f"unit cost must be >= 0 int: {card_name}")
        if unit_class is None:
            raise ValueError(f"unit must have unit_class: {card_name}")
        if attack_value is None or health_value is None:
            raise ValueError(f"unit must have attack/health: {card_name}")
        if attack_value < 0 or health_value <= 0:
            raise ValueError(f"invalid unit stats: {card_name}")
        if acost is None or acost < 0:
            raise ValueError(f"unit must have non-negative acost: {card_name}")
    elif card_type == CardType.ORDER:
        if not isinstance(cost, int) or cost < 0:
            raise ValueError(f"order cost must be >= 0 int: {card_name}")
        if attack_value is not None or health_value is not None:
            raise ValueError(f"order must not have attack/health: {card_name}")
        if unit_class is not None:
            raise ValueError(f"order must not have unit_class: {card_name}")
    elif card_type == CardType.BASE:
        if not isinstance(health_value, int) or health_value <= 0:
            raise ValueError(f"base must have positive health_value: {card_name}")
        if attack_value is not None:
            raise ValueError(f"base must not have attack_value: {card_name}")
        if unit_class is not None:
            raise ValueError(f"base must not have unit_class: {card_name}")
    elif card_type == CardType.COUNTERMEASURE:
        if not isinstance(cost, int) or cost < 0:
            raise ValueError(f"countermeasure cost must be >= 0 int: {card_name}")
        if attack_value is not None or health_value is not None:
            raise ValueError(f"countermeasure must not have attack/health: {card_name}")
        if unit_class is not None:
            raise ValueError(f"countermeasure must not have unit_class: {card_name}")
