"""Engine lifecycle tests: game setup, turn flow, win condition."""
from __future__ import annotations

from kards_sim.actions import Attack, EndTurn, PlayCard
from kards_sim.cards import (
    HeadquartersCard,
    UnitCard,
    GermanyHeadquarters,
    SovietHeadquarters,
    Infantry,
)
from kards_sim.engine import Engine
from kards_sim.state import GameConfig
from kards_sim.types import Lane, PlayerId, UnitClass

from conftest import place_on_board


def test_new_game_initializes_hq(engine: Engine) -> None:
    state = Engine.new_game(
        [GermanyHeadquarters] + [Infantry] * 10,
        [SovietHeadquarters] + [Infantry] * 10,
        seed=1,
    )
    assert state.card(state.players[PlayerId(0)].hq_iid).name == "Germany Headquarters"
    assert state.card(state.players[PlayerId(1)].hq_iid).name == "Soviet Headquarters"


def test_deploy_unit_and_end_turn(engine: Engine) -> None:
    state = Engine.new_game(
        [GermanyHeadquarters] + [Infantry] * 10,
        [SovietHeadquarters] + [Infantry] * 10,
        seed=1,
    )
    ap = state.active_player
    hand0 = state.players[ap].hand[0]

    res = engine.step(state, PlayCard(player_id=ap, card=hand0, index=0))
    assert res.violation is None

    res2 = engine.step(state, EndTurn(player_id=ap))
    assert res2.violation is None


def test_game_over_on_hq_destroyed(engine: Engine) -> None:
    class _HQ(HeadquartersCard):
        name = "Test HQ"
        health_value = 1

    class _Attacker(UnitCard):
        name = "Attacker"
        unit_class = UnitClass.INFANTRY
        cost = 0
        acost = 0
        attack_value = 5
        health_value = 10

    state = Engine.new_game(
        [_HQ, _Attacker],
        [_HQ],
        seed=1,
        config=GameConfig(starting_hand=0, starting_p1_hp=1),
    )

    atk = state.allocate_card(_Attacker, owner=PlayerId(0))
    place_on_board(state, atk, Lane.FRONTLINE)

    hq1_iid = state.players[PlayerId(1)].hq_iid
    res = engine.step(state, Attack(player_id=PlayerId(0), attacker=atk, defender=hq1_iid))
    assert res.violation is None
    assert state.game_over
    assert state.winner == PlayerId(0)
