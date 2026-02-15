from __future__ import annotations

from kards_sim.actions import Attack, EndTurn, PlayCard
from kards_sim.cards.abilities.registry import default_registry
from kards_sim.cards import AbilitySpec
from kards_sim.cards.bases import BaseCardBase, GermanyHeadquarters, SovietHeadquarters
from kards_sim.cards.units import UnitCardBase
from kards_sim.cards.units.infantry import Infantry
from kards_sim.cards.units.tank import Tank35T
from kards_sim.engine import Engine
from kards_sim.resolver import Resolver
from kards_sim.state import GameConfig
from kards_sim.types import CardType, Lane, PlayerId, UnitClass, Zone


def test_smoke_can_start_and_play_unit() -> None:
    engine = Engine(resolver=Resolver(registry=default_registry()))
    state = Engine.new_game(
        [GermanyHeadquarters] + [Infantry] * 10,
        [SovietHeadquarters] + [Infantry] * 10,
        seed=1,
    )

    assert (
        state.get_card_for_instance(state.players[PlayerId(0)].base_card_id).name
        == "Germany Headquarters"
    )
    assert (
        state.get_card_for_instance(state.players[PlayerId(1)].base_card_id).name
        == "Soviet Headquarters"
    )

    ap = state.active_player
    hand0 = state.players[ap].hand[0]
    res = engine.step(
        state,
        PlayCard(
            player_id=ap,
            card=hand0,
            index=0,
        ),
    )
    assert res.violation is None

    res2 = engine.step(state, EndTurn(player_id=ap))
    assert res2.violation is None


def test_ambush_strikes_first_and_can_cancel_attack() -> None:
    class _Base(BaseCardBase):
        name = "Base"
        card_type = CardType.BASE
        cost = 0

    class _Attacker(UnitCardBase):
        name = "Attacker"
        card_type = CardType.UNIT
        cost = 0
        acost = 0
        unit_class = UnitClass.INFANTRY
        attack_value = 2
        health_value = 1
        abilities = ()

    class _DefAmbush(UnitCardBase):
        name = "Defender (Ambush)"
        card_type = CardType.UNIT
        cost = 0
        acost = 0
        unit_class = UnitClass.INFANTRY
        attack_value = 1
        health_value = 2
        abilities = (AbilitySpec("ambush"),)

    engine = Engine(resolver=Resolver(registry=default_registry()))
    state = Engine.new_game(
        [_Base],
        [_Base],
        seed=1,
        config=GameConfig(starting_hand=0),
    )

    atk = state.allocate_instance(_Attacker, owner=PlayerId(0))
    dfd = state.allocate_instance(_DefAmbush, owner=PlayerId(1))

    atk_inst = state.get_instance(atk)
    dfd_inst = state.get_instance(dfd)
    atk_inst.zone = Zone.BOARD
    dfd_inst.zone = Zone.BOARD
    atk_inst.lane = Lane.FRONTLINE
    dfd_inst.lane = Lane.SUPPORTLINE
    atk_inst.exhausted = False
    dfd_inst.exhausted = False

    state.frontline.append(atk)
    state.supportline[PlayerId(1)].append(dfd)

    res = engine.step(state, Attack(player_id=PlayerId(0), attacker=atk, defender=dfd))
    assert res.violation is None

    # Defender has ambush and hits first; attacker has 1 HP so it dies and does not strike.
    assert any(getattr(ev, "source", None) == dfd for ev in res.events)
    assert not any(getattr(ev, "source", None) == atk for ev in res.events)


def test_tank35t_on_deploy_reduces_acost_with_friendly_infantry() -> None:
    engine = Engine(resolver=Resolver(registry=default_registry()))
    state = Engine.new_game(
        [GermanyHeadquarters, Tank35T],
        [SovietHeadquarters],
        seed=1,
        config=GameConfig(starting_hand=1),
    )

    ap = state.active_player
    state.players[ap].max_credits = 2
    state.players[ap].credits = 2

    inf = state.allocate_instance(Infantry, owner=ap)
    inf_inst = state.get_instance(inf)
    inf_inst.zone = Zone.BOARD
    inf_inst.lane = Lane.SUPPORTLINE
    inf_inst.exhausted = False
    state.supportline[ap].append(inf)

    tank = state.players[ap].hand[0]
    res = engine.step(state, PlayCard(player_id=ap, card=tank, index=0))
    assert res.violation is None

    tank_card = state.get_card_for_instance(tank)
    assert tank_card.acost == 0
