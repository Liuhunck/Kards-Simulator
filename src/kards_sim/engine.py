from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

from .cards.base import CardBase
from .cards.headquarters import HeadquartersCard
from .resolver import Resolver, StepResult
from .state import GameConfig, GameState, PlayerState
from .types import PlayerId


@dataclass(slots=True)
class Engine:
    """High-level helper to create a game and drive the resolver."""

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

        hq_p0_cls = deck_p0[0]
        hq_p1_cls = deck_p1[0]
        cards_p0 = deck_p0[1:]
        cards_p1 = deck_p1[1:]

        if not issubclass(hq_p0_cls, HeadquartersCard):
            raise ValueError(f"first card in deck_p0 must be HeadquartersCard: {hq_p0_cls.__name__}")
        if not issubclass(hq_p1_cls, HeadquartersCard):
            raise ValueError(f"first card in deck_p1 must be HeadquartersCard: {hq_p1_cls.__name__}")

        state = GameState(
            config=cfg,
            instances={},
            players={},
            active_player=PlayerId(0),
            turn=1,
            rng_seed=seed,
            next_instance_id=1,
        )

        hq0_iid = state.allocate_hq(hq_p0_cls, owner=PlayerId(0), hp_override=cfg.starting_p0_hp)
        hq1_iid = state.allocate_hq(hq_p1_cls, owner=PlayerId(1), hp_override=cfg.starting_p1_hp)

        state.players[PlayerId(0)] = PlayerState(player_id=PlayerId(0), hq_iid=hq0_iid)
        state.players[PlayerId(1)] = PlayerState(player_id=PlayerId(1), hq_iid=hq1_iid)

        for pid, cards in ((PlayerId(0), cards_p0), (PlayerId(1), cards_p1)):
            for card_cls in cards:
                iid = state.allocate_card(card_cls, owner=pid)
                state.players[pid].deck.append(iid)

        random.seed(state.rng_seed)
        random.shuffle(state.players[PlayerId(0)].deck)
        random.shuffle(state.players[PlayerId(1)].deck)

        state.frontline = []
        state.supportline = {
            PlayerId(0): [hq0_iid],
            PlayerId(1): [hq1_iid],
        }

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
