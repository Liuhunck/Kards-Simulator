from __future__ import annotations

from kards_sim.actions import Attack, EndTurn, PlayCard
from kards_sim.cards.abilities.registry import default_registry
from kards_sim.cards import AbilitySpec, CardDefinition, CardRegistry
from kards_sim.cards.bases import BaseCardBase
from kards_sim.cards.samples import sample_card_registry
from kards_sim.cards.units import UnitCardBase
from kards_sim.engine import Engine
from kards_sim.resolver import Resolver
from kards_sim.state import GameConfig
from kards_sim.types import CardType, Lane, PlayerId, UnitClass, Zone


def test_smoke_can_start_and_play_unit() -> None:
    engine = Engine(resolver=Resolver(registry=default_registry()))
    registry = sample_card_registry()
    state = Engine.new_game(registry, ["UNIT_INF_1"] * 10, ["UNIT_INF_1"] * 10, seed=1)

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
        definition = CardDefinition(
            def_id="BASE",
            name="Base",
            card_type=CardType.BASE,
            cost=0,
        )

    class _Attacker(UnitCardBase):
        definition = CardDefinition(
            def_id="ATK",
            name="Attacker",
            card_type=CardType.UNIT,
            cost=0,
            acost=0,
            unit_class=UnitClass.INFANTRY,
            attack=2,
            health=1,
            abilities=(),
        )

    class _DefAmbush(UnitCardBase):
        definition = CardDefinition(
            def_id="DEF_AMB",
            name="Defender (Ambush)",
            card_type=CardType.UNIT,
            cost=0,
            acost=0,
            unit_class=UnitClass.INFANTRY,
            attack=1,
            health=2,
            abilities=(AbilitySpec("ambush"),),
        )

    registry = CardRegistry()
    registry.register_many([_Base, _Attacker, _DefAmbush])

    engine = Engine(resolver=Resolver(registry=default_registry()))
    state = Engine.new_game(
        registry, [], [], seed=1, config=GameConfig(starting_hand=0)
    )

    atk = state.allocate_instance("ATK", owner=PlayerId(0), zone=Zone.BOARD)
    dfd = state.allocate_instance("DEF_AMB", owner=PlayerId(1), zone=Zone.BOARD)

    atk_inst = state.get_instance(atk)
    dfd_inst = state.get_instance(dfd)
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
