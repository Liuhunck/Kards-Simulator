from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..base import CardBase
from ..specs import AbilitySpec
from ...events import CardPlayed, DamageDealt, Event, UnitDeployed
from ...state import GameState


@dataclass(frozen=True, slots=True)
class Ability:
    """Runtime ability implementation bound to a specific source card instance."""

    ability_id: str
    source_iid: int
    trigger: Callable[[GameState, Event], bool]
    handler: Callable[[GameState, Event], list[Event]]


class AbilityRegistry:
    def __init__(self) -> None:
        self._factories: dict[
            str,
            Callable[[int, dict], Ability],
        ] = {}

    def register(
        self, ability_id: str, factory: Callable[[int, dict], Ability]
    ) -> None:
        if ability_id in self._factories:
            raise KeyError(f"duplicate ability_id: {ability_id}")
        self._factories[ability_id] = factory

    def instantiate_for_card(
        self, source_iid: int, card_cls: type[CardBase]
    ) -> list[Ability]:
        abilities: list[Ability] = []
        for spec in card_cls.abilities:
            abilities.append(self.instantiate(source_iid, spec))
        return abilities

    def instantiate(self, source_iid: int, spec: AbilitySpec) -> Ability:
        factory = self._factories.get(spec.ability_id)
        if factory is None:
            raise KeyError(f"ability not registered: {spec.ability_id}")
        return factory(source_iid, spec.params)


def default_registry() -> AbilityRegistry:
    """Registry with a tiny set of built-in primitives.

    Extend this with more KARDS mechanics over time.
    """

    reg = AbilityRegistry()

    # On deploy: draw N
    def _on_deploy_draw(source_iid: int, params: dict) -> Ability:
        n = int(params.get("n", 1))

        def trigger(state: GameState, ev: Event) -> bool:
            return isinstance(ev, UnitDeployed) and int(ev.unit) == int(source_iid)

        def handler(state: GameState, ev: Event) -> list[Event]:
            from ...events import CardDrawn
            from ...resolver import enqueue_draw

            out: list[Event] = []
            pid = state.get_instance(ev.unit).owner
            for _ in range(n):
                drawn = enqueue_draw(state, pid)
                if drawn is not None:
                    out.append(CardDrawn(player_id=pid, card=drawn))
            return out

        return Ability(
            ability_id="on_deploy_draw",
            source_iid=source_iid,
            trigger=trigger,
            handler=handler,
        )

    reg.register("on_deploy_draw", _on_deploy_draw)

    # On play (order): deal damage to a target unit or HQ.
    def _on_play_deal_damage(source_iid: int, params: dict) -> Ability:
        amount = int(params.get("amount", 1))

        def trigger(state: GameState, ev: Event) -> bool:
            return isinstance(ev, CardPlayed) and int(ev.card) == int(source_iid)

        def handler(state: GameState, ev: Event) -> list[Event]:
            assert isinstance(ev, CardPlayed)
            if ev.target is None and ev.target_player is None:
                return []
            return [
                DamageDealt(
                    source=ev.card,
                    target=ev.target,
                    target_player=ev.target_player,
                    amount=amount,
                )
            ]

        return Ability(
            ability_id="on_play_deal_damage",
            source_iid=source_iid,
            trigger=trigger,
            handler=handler,
        )

    reg.register("on_play_deal_damage", _on_play_deal_damage)

    # Keyword ability: ambush (strikes first when attacked).
    # The actual combat ordering is handled by the unit base class; this registration
    # exists so data-driven cards can declare the ability without raising.
    def _ambush_keyword(source_iid: int, params: dict) -> Ability:
        _ = params

        def trigger(state: GameState, ev: Event) -> bool:
            return False

        def handler(state: GameState, ev: Event) -> list[Event]:
            return []

        return Ability(
            ability_id="ambush",
            source_iid=source_iid,
            trigger=trigger,
            handler=handler,
        )

    reg.register("ambush", _ambush_keyword)

    return reg
