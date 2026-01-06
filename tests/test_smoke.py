from __future__ import annotations

from pathlib import Path

from kards_sim.actions import EndTurn, PlayCard
from kards_sim.abilities.registry import default_registry
from kards_sim.engine import Engine
from kards_sim.resolver import Resolver
from kards_sim.types import BoardPos, Lane, PlayerId


def test_smoke_can_start_and_play_unit() -> None:
    root = Path(__file__).resolve().parents[1]
    defs = Engine.load_definitions_json(root / "data" / "cards.sample.json")
    engine = Engine(resolver=Resolver(registry=default_registry()))
    state = Engine.new_game(defs, ["UNIT_INF_1"] * 10, ["UNIT_INF_1"] * 10, seed=1)

    ap = state.active_player
    hand0 = state.players[ap].hand[0]
    res = engine.step(
        state,
        PlayCard(
            player_id=ap,
            card=hand0,
            board_pos=BoardPos(lane=Lane.FRONTLINE, owner=None, column=0),
        ),
    )
    assert res.violation is None

    res2 = engine.step(state, EndTurn(player_id=ap))
    assert res2.violation is None
