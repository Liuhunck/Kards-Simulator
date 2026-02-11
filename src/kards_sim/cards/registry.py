from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..types import CardType
from .base import CardBase
from .definitions import CardDefinition, validate_definition
from .bases.base import BaseCardBase
from .units.base import UnitCardBase
from .orders.base import OrderCardBase
from .countermeasures.base import CountermeasureCardBase


class CardRegistry:
    """Registry for concrete card classes keyed by definition id."""

    def __init__(self) -> None:
        self._cards: dict[str, type[CardBase]] = {}

    def register(self, cls: type[CardBase]) -> None:
        defn = getattr(cls, "definition", None)
        if defn is None:
            raise ValueError("card class missing definition")
        validate_definition(defn)
        if defn.def_id in self._cards:
            raise KeyError(f"duplicate card def_id: {defn.def_id}")
        self._cards[defn.def_id] = cls

    def register_many(self, classes: Iterable[type[CardBase]]) -> None:
        for cls in classes:
            self.register(cls)

    def build_definitions(self) -> dict[str, CardDefinition]:
        return {
            defn.def_id: defn
            for defn in (cls.definition for cls in self._cards.values())
            if defn is not None
        }

    def resolve_class(self, defn: CardDefinition) -> type[CardBase]:
        override = self._cards.get(defn.def_id)
        if override is not None:
            return override
        if defn.card_type == CardType.UNIT:
            return UnitCardBase
        if defn.card_type == CardType.ORDER:
            return OrderCardBase
        if defn.card_type == CardType.COUNTERMEASURE:
            return CountermeasureCardBase
        return BaseCardBase


@dataclass(slots=True)
class CardCatalog:
    """Runtime lookup of card implementations by definition id."""

    cards: dict[str, CardBase]

    @classmethod
    def from_definitions(
        cls,
        definitions: dict[str, CardDefinition],
        registry: CardRegistry | None = None,
    ) -> "CardCatalog":
        reg = registry or CardRegistry()
        cards: dict[str, CardBase] = {}
        for defn in definitions.values():
            card_cls = reg.resolve_class(defn)
            cards[defn.def_id] = card_cls(defn)
        return cls(cards=cards)

    @classmethod
    def from_registry(
        cls, registry: CardRegistry
    ) -> tuple["CardCatalog", dict[str, CardDefinition]]:
        definitions = registry.build_definitions()
        return cls.from_definitions(definitions, registry=registry), definitions

    def get(self, def_id: str) -> CardBase:
        return self.cards[def_id]
