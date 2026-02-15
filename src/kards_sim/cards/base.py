from __future__ import annotations

from typing import TYPE_CHECKING

from ..events import Trigger
from ..types import CardType, Nation
from .specs import AbilitySpec

if TYPE_CHECKING:
    from ..actions import Advance, Attack, PlayCard
    from ..events import Event, Trigger, TriggerContext
    from ..state import GameState


class CardBase:
    """Base class for all card implementations."""

    name: str = "Card"
    card_type: CardType = CardType.ORDER
    nation: Nation = Nation.NEUTRAL
    abilities: tuple[AbilitySpec, ...] = ()

    @property
    def country(self) -> Nation:
        return self.__class__.nation

    def deploy(self, state: GameState, action: PlayCard) -> list[Event]:
        from ..rules import RuleViolation

        raise RuleViolation("deploy not supported")

    def advance(self, state: GameState, action: Advance) -> list[Event]:
        from ..rules import RuleViolation

        raise RuleViolation("advance not supported")

    def attack(self, state: GameState, action: Attack) -> list[Event]:
        from ..rules import RuleViolation

        raise RuleViolation("attack not supported")

    def on_turn_start(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        return []

    def on_turn_end(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        return []

    def before_attack(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        return []

    def after_attack(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        return []

    def before_deal_damage(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        return []

    def after_deal_damage(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        return []

    def before_take_damage(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        return []

    def after_take_damage(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        return []

    def on_death(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        return []

    def after_death(self, state: GameState, ctx: TriggerContext) -> list[Event]:
        return []

    def trigger(
        self, state: GameState, trigger: Trigger, ctx: TriggerContext
    ) -> list[Event]:
        if trigger == Trigger.TURN_START:
            return self.on_turn_start(state, ctx)
        if trigger == Trigger.TURN_END:
            return self.on_turn_end(state, ctx)
        if trigger == Trigger.BEFORE_ATTACK:
            return self.before_attack(state, ctx)
        if trigger == Trigger.AFTER_ATTACK:
            return self.after_attack(state, ctx)
        if trigger == Trigger.BEFORE_DEAL_DAMAGE:
            return self.before_deal_damage(state, ctx)
        if trigger == Trigger.AFTER_DEAL_DAMAGE:
            return self.after_deal_damage(state, ctx)
        if trigger == Trigger.BEFORE_TAKE_DAMAGE:
            return self.before_take_damage(state, ctx)
        if trigger == Trigger.AFTER_TAKE_DAMAGE:
            return self.after_take_damage(state, ctx)
        if trigger == Trigger.ON_DEATH:
            return self.on_death(state, ctx)
        if trigger == Trigger.AFTER_DEATH:
            return self.after_death(state, ctx)
        return []
