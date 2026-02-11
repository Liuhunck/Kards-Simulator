from __future__ import annotations

import random
from typing import Iterable
from dataclasses import dataclass

from .cards import (
    CardCatalog,
    CardRegistry,
)
from .resolver import Resolver, StepResult
from .state import GameConfig, GameState, PlayerState
from .types import PlayerId, Zone


@dataclass(slots=True)
class Engine:
    """High-level helper to create state and drive the resolver."""

    resolver: Resolver

    @staticmethod
    def new_game(
        card_registry: CardRegistry,
        deck_p0: Iterable[str],
        deck_p1: Iterable[str],
        seed: int = 1,
        config: GameConfig | None = None,
    ) -> GameState:
        cfg = config or GameConfig()
        catalog, definitions = CardCatalog.from_registry(card_registry)
        state = GameState(
            config=cfg,
            definitions=definitions,
            card_catalog=catalog,
            instances={},
            players={},
            active_player=PlayerId(0),
            turn=1,
            rng_seed=seed,
            next_instance_id=1,
        )

        # Allocate base instances
        play0_base_iid = state.allocate_base_instance(
            owner=PlayerId(0), hp=cfg.starting_p0_hp
        )
        play1_base_iid = state.allocate_base_instance(
            owner=PlayerId(1), hp=cfg.starting_p1_hp
        )

        # Initialize players
        state.players[PlayerId(0)] = PlayerState(
            player_id=PlayerId(0),
            base_card_id=play0_base_iid,
        )
        state.players[PlayerId(1)] = PlayerState(
            player_id=PlayerId(1),
            base_card_id=play1_base_iid,
        )

        # Allocate deck instances
        for pid, deck in ((PlayerId(0), deck_p0), (PlayerId(1), deck_p1)):
            for def_id in deck:
                iid = state.allocate_instance(def_id, owner=pid, zone=Zone.DECK)
                state.players[pid].deck.append(iid)

        # Shuffle decks
        random.seed(state.rng_seed)
        random.shuffle(state.players[PlayerId(0)].deck)
        random.shuffle(state.players[PlayerId(1)].deck)

        # Initialize board slots
        state.frontline = []
        state.supportline = {
            PlayerId(0): [play0_base_iid],
            PlayerId(1): [play1_base_iid],
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
