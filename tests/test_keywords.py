"""Keyword mechanic tests: ambush, blitz, heavy armor, smokescreen, etc."""
from __future__ import annotations

from kards_sim.actions import Advance, Attack, PlayCard
from kards_sim.cards import HeadquartersCard, UnitCard
from kards_sim.engine import Engine
from kards_sim.state import GameConfig
from kards_sim.types import Keyword, Lane, PlayerId, UnitClass, Zone

from conftest import place_on_board


def test_ambush_strikes_first_and_cancels_attack(engine: Engine) -> None:
    class _HQ(HeadquartersCard):
        name = "Test HQ"
        health_value = 20

    class _Attacker(UnitCard):
        name = "Attacker"
        unit_class = UnitClass.INFANTRY
        cost = 0
        acost = 0
        attack_value = 2
        health_value = 1

    class _Defender(UnitCard):
        name = "Defender (Ambush)"
        unit_class = UnitClass.INFANTRY
        cost = 0
        acost = 0
        attack_value = 1
        health_value = 2
        keywords = frozenset({Keyword.AMBUSH})

    state = Engine.new_game([_HQ], [_HQ], seed=1, config=GameConfig(starting_hand=0))

    atk = state.allocate_card(_Attacker, owner=PlayerId(0))
    dfd = state.allocate_card(_Defender, owner=PlayerId(1))
    place_on_board(state, atk, Lane.FRONTLINE)
    place_on_board(state, dfd, Lane.SUPPORTLINE)

    res = engine.step(state, Attack(player_id=PlayerId(0), attacker=atk, defender=dfd))
    assert res.violation is None
    assert any(getattr(ev, "source", None) == dfd for ev in res.events)
    assert not any(getattr(ev, "source", None) == atk for ev in res.events)


def test_blitz_not_exhausted_on_deploy(engine: Engine) -> None:
    class _HQ(HeadquartersCard):
        name = "Test HQ"
        health_value = 20

    class _BlitzUnit(UnitCard):
        name = "Blitz Unit"
        unit_class = UnitClass.TANK
        cost = 0
        acost = 0
        attack_value = 3
        health_value = 3
        keywords = frozenset({Keyword.BLITZ})

    state = Engine.new_game(
        [_HQ, _BlitzUnit], [_HQ], seed=1, config=GameConfig(starting_hand=1),
    )

    ap = state.active_player
    iid = state.players[ap].hand[0]
    res = engine.step(state, PlayCard(player_id=ap, card=iid, index=0))
    assert res.violation is None
    assert not state.inst(iid).exhausted


def test_heavy_armor_reduces_damage(engine: Engine) -> None:
    class _HQ(HeadquartersCard):
        name = "Test HQ"
        health_value = 20

    class _HeavyUnit2(UnitCard):
        name = "Heavy Armor 2 Unit"
        unit_class = UnitClass.TANK
        cost = 0
        acost = 0
        attack_value = 1
        health_value = 10
        heavy_armor = 2

    class _HeavyUnit3(UnitCard):
        name = "Heavy Armor 3 Unit"
        unit_class = UnitClass.TANK
        cost = 0
        acost = 0
        attack_value = 1
        health_value = 10
        heavy_armor = 3

    class _Attacker(UnitCard):
        name = "Attacker"
        unit_class = UnitClass.INFANTRY
        cost = 0
        acost = 0
        attack_value = 5
        health_value = 10

    state = Engine.new_game(
        [_HQ], [_HQ], seed=1, config=GameConfig(starting_hand=0),
    )

    # Heavy Armor 2: 5 - 2 = 3 effective; 10 - 3 = 7
    atk = state.allocate_card(_Attacker, owner=PlayerId(0))
    hvy2 = state.allocate_card(_HeavyUnit2, owner=PlayerId(1))
    place_on_board(state, atk, Lane.FRONTLINE)
    place_on_board(state, hvy2, Lane.SUPPORTLINE)

    res = engine.step(state, Attack(player_id=PlayerId(0), attacker=atk, defender=hvy2))
    assert res.violation is None
    assert state.inst(hvy2).current_health == 7

    # Heavy Armor 3: 5 - 3 = 2 effective; 10 - 2 = 8
    state2 = Engine.new_game(
        [_HQ], [_HQ], seed=1, config=GameConfig(starting_hand=0),
    )
    atk2 = state2.allocate_card(_Attacker, owner=PlayerId(0))
    hvy3 = state2.allocate_card(_HeavyUnit3, owner=PlayerId(1))
    place_on_board(state2, atk2, Lane.FRONTLINE)
    place_on_board(state2, hvy3, Lane.SUPPORTLINE)

    res2 = engine.step(state2, Attack(player_id=PlayerId(0), attacker=atk2, defender=hvy3))
    assert res2.violation is None
    assert state2.inst(hvy3).current_health == 8


# -- Smokescreen ---------------------------------------------------------------

def test_smokescreen_prevents_being_attacked(engine: Engine) -> None:
    """烟幕单位不能被敌方单位攻击。"""
    class _HQ(HeadquartersCard):
        name = "Test HQ"
        health_value = 20

    class _SmokeUnit(UnitCard):
        name = "Smoke"
        unit_class = UnitClass.TANK
        cost = 0
        acost = 0
        attack_value = 1
        health_value = 3
        keywords = frozenset({Keyword.SMOKESCREEN})

    class _Attacker(UnitCard):
        name = "Attacker"
        unit_class = UnitClass.INFANTRY
        cost = 0
        acost = 0
        attack_value = 2
        health_value = 3

    state = Engine.new_game(
        [_HQ, _SmokeUnit], [_HQ], seed=1, config=GameConfig(starting_hand=0),
    )
    smoke = state.allocate_card(_SmokeUnit, owner=PlayerId(1))
    atk = state.allocate_card(_Attacker, owner=PlayerId(0))

    place_on_board(state, smoke, Lane.SUPPORTLINE, owner=PlayerId(1))
    state.inst(smoke).smokescreen_active = True
    place_on_board(state, atk, Lane.FRONTLINE, owner=PlayerId(0))
    state.players[PlayerId(0)].credits = 10

    res = engine.step(state, Attack(player_id=PlayerId(0), attacker=atk, defender=smoke))
    assert res.violation is not None
    assert "smokescreen" in res.violation.reason


def test_smokescreen_lost_after_attack(engine: Engine) -> None:
    """烟幕单位攻击后应失去烟幕。"""
    class _HQ(HeadquartersCard):
        name = "Test HQ"
        health_value = 20

    class _SmokeUnit(UnitCard):
        name = "Smoke"
        unit_class = UnitClass.TANK
        cost = 0
        acost = 0
        attack_value = 1
        health_value = 5
        keywords = frozenset({Keyword.SMOKESCREEN})

    class _Target(UnitCard):
        name = "Target"
        unit_class = UnitClass.INFANTRY
        cost = 0
        acost = 0
        attack_value = 1
        health_value = 5

    state = Engine.new_game(
        [_HQ], [_HQ], seed=1, config=GameConfig(starting_hand=0),
    )
    smoke = state.allocate_card(_SmokeUnit, owner=PlayerId(0))
    target = state.allocate_card(_Target, owner=PlayerId(1))
    place_on_board(state, smoke, Lane.FRONTLINE, owner=PlayerId(0))
    state.inst(smoke).smokescreen_active = True
    state.inst(smoke).exhausted = False
    place_on_board(state, target, Lane.FRONTLINE, owner=PlayerId(1))
    state.players[PlayerId(0)].credits = 10

    engine.step(state, Attack(player_id=PlayerId(0), attacker=smoke, defender=target))
    assert state.inst(smoke).smokescreen_active is False


def test_smokescreen_lost_after_advance(engine: Engine) -> None:
    """烟幕单位推进到前线后应失去烟幕。"""
    class _HQ(HeadquartersCard):
        name = "Test HQ"
        health_value = 20

    class _SmokeUnit(UnitCard):
        name = "Smoke"
        unit_class = UnitClass.TANK
        cost = 0
        acost = 0
        attack_value = 1
        health_value = 3
        keywords = frozenset({Keyword.SMOKESCREEN, Keyword.BLITZ})

    state = Engine.new_game(
        [_HQ, _SmokeUnit], [_HQ], seed=1, config=GameConfig(starting_hand=1),
    )
    ap = state.active_player
    iid = state.players[ap].hand[0]
    engine.step(state, PlayCard(player_id=ap, card=iid, index=0))
    assert state.inst(iid).smokescreen_active is True

    state.players[ap].credits = 10
    engine.step(state, Advance(player_id=ap, card=iid, index=0))
    assert state.inst(iid).smokescreen_active is False


def test_smokescreen_not_activated_with_guard(engine: Engine) -> None:
    """守护单位不能具有烟幕。"""
    class _HQ(HeadquartersCard):
        name = "Test HQ"
        health_value = 20

    class _GuardSmoke(UnitCard):
        name = "GuardSmoke"
        unit_class = UnitClass.INFANTRY
        cost = 0
        acost = 0
        attack_value = 1
        health_value = 3
        keywords = frozenset({Keyword.GUARD, Keyword.SMOKESCREEN, Keyword.BLITZ})

    state = Engine.new_game(
        [_HQ, _GuardSmoke], [_HQ], seed=1, config=GameConfig(starting_hand=1),
    )
    ap = state.active_player
    iid = state.players[ap].hand[0]
    engine.step(state, PlayCard(player_id=ap, card=iid, index=0))
    assert state.inst(iid).smokescreen_active is False
