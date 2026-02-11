from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..actions import Advance, Attack, PlayCard
    from ..events import Event
    from ..state import GameState
    from .definitions import CardDefinition


class CardBase:
    """Base class for all card implementations."""

    definition: CardDefinition | None = None

    def __init__(self, definition: CardDefinition | None = None) -> None:
        if definition is None:
            definition = self.__class__.definition
        if definition is None:
            raise ValueError("card definition missing")
        self.definition = definition

    @property
    def def_id(self) -> str:
        return self.definition.def_id

    def play(self, state: GameState, action: PlayCard) -> list[Event]:
        from ..rules import RuleViolation

        raise RuleViolation("play not supported")

    def advance(self, state: GameState, action: Advance) -> list[Event]:
        from ..rules import RuleViolation

        raise RuleViolation("advance not supported")

    def attack(self, state: GameState, action: Attack) -> list[Event]:
        from ..rules import RuleViolation

        raise RuleViolation("attack not supported")
