from __future__ import annotations

import random
from typing import Sequence
from dataclasses import dataclass

from .types import PlayerId
from .cards import CardBase, BaseCardBase
from .resolver import Resolver, StepResult
from .state import GameConfig, GameState, PlayerState


@dataclass(slots=True)
class Engine:
    """High-level helper to create state and drive the resolver."""

    resolver: Resolver

    @staticmethod
    def new_game(
        deck_p0: Sequence[type[CardBase]],
        deck_p1: Sequence[type[CardBase]],
        seed: int = 1,
        config: GameConfig | None = None,
    ) -> GameState:
        cfg = config or GameConfig()

        if len(deck_p0) == 0:
            raise ValueError("player 0 deck is empty")
        if len(deck_p1) == 0:
            raise ValueError("player 1 deck is empty")

        base_p0_cls = deck_p0[0]
        base_p1_cls = deck_p1[0]
        deck_p0 = deck_p0[1:]
        deck_p1 = deck_p1[1:]

        if not issubclass(base_p0_cls, BaseCardBase):
            raise ValueError(f"hq_p0 must be base card class: {base_p0_cls.__name__}")
        if not issubclass(base_p1_cls, BaseCardBase):
            raise ValueError(f"hq_p1 must be base card class: {base_p1_cls.__name__}")

        state = GameState(
            config=cfg,
            instances={},
            players={},
            active_player=PlayerId(0),
            turn=1,
            rng_seed=seed,
            next_instance_id=1,
        )

        # Allocate base instances
        play0_base_iid = state.allocate_base_instance(
            base_card_cls=base_p0_cls,
            owner=PlayerId(0),
            hp=cfg.starting_p0_hp,
        )
        play1_base_iid = state.allocate_base_instance(
            base_card_cls=base_p1_cls,
            owner=PlayerId(1),
            hp=cfg.starting_p1_hp,
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
            for card_cls in deck:
                iid = state.allocate_instance(card_cls, owner=pid)
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
