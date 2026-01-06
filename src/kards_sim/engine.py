from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .cards import AbilitySpec, CardDefinition, validate_definition
from .resolver import Resolver, StepResult
from .state import GameConfig, GameState, PlayerState
from .types import CardType, PlayerId, Zone


@dataclass(slots=True)
class Engine:
    """High-level helper to create state and drive the resolver."""

    resolver: Resolver

    @staticmethod
    def load_definitions_json(path: str | Path) -> dict[str, CardDefinition]:
        p = Path(path)
        data = json.loads(p.read_text(encoding="utf-8"))
        defs: dict[str, CardDefinition] = {}
        for row in data["cards"]:
            abilities = tuple(
                AbilitySpec(ability_id=a["id"], params=dict(a.get("params", {})))
                for a in row.get("abilities", [])
            )
            defn = CardDefinition(
                def_id=row["id"],
                name=row["name"],
                card_type=CardType(row["type"]),
                cost=row.get("cost", 0),
                acost=row.get("acost", None),
                attack=row.get("attack", None),
                health=row.get("health", None),
                abilities=abilities,
            )
            validate_definition(defn)
            defs[defn.def_id] = defn
        return defs

    @staticmethod
    def new_game(
        definitions: dict[str, CardDefinition],
        deck_p0: Iterable[str],
        deck_p1: Iterable[str],
        seed: int = 1,
        config: GameConfig | None = None,
    ) -> GameState:
        cfg = config or GameConfig()
        state = GameState(
            config=cfg,
            definitions=definitions,
            instances={},
            players={},
            active_player=PlayerId(0),
            turn=1,
            rng_seed=seed,
            next_instance_id=1,
        )

        state.players[PlayerId(0)] = PlayerState(
            player_id=PlayerId(0),
            hq_health=cfg.starting_hq_health,
        )
        state.players[PlayerId(1)] = PlayerState(
            player_id=PlayerId(1),
            hq_health=cfg.starting_hq_health,
        )

        # Allocate deck instances
        for pid, deck in ((PlayerId(0), deck_p0), (PlayerId(1), deck_p1)):
            for def_id in deck:
                iid = state.allocate_instance(def_id, owner=pid, zone=Zone.DECK)
                state.players[pid].deck.append(iid)

        # Initialize board slots
        state.frontline = []
        state.supportline = {
            PlayerId(0): [
                state.allocate_instance(
                    def_id="BASE", owner=PlayerId(0), zone=Zone.BOARD
                )
            ],
            PlayerId(1): [
                state.allocate_instance(
                    def_id="BASE", owner=PlayerId(1), zone=Zone.BOARD
                )
            ],
        }

        # Starting credits and draw
        for pid in (PlayerId(0), PlayerId(1)):
            p = state.players[pid]
            p.max_credits = 1
            p.credits = 1

        from .resolver import enqueue_draw

        for _ in range(cfg.starting_hand):
            enqueue_draw(state, PlayerId(0))
            enqueue_draw(state, PlayerId(1))

        return state

    def step(self, state: GameState, action) -> StepResult:
        return self.resolver.step(state, action)
