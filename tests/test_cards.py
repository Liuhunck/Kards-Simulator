"""Card-specific ability tests."""
from __future__ import annotations

from kards_sim.actions import Attack, EndTurn, PlayCard
from kards_sim.cards import (
    GermanyHeadquarters,
    SovietHeadquarters,
    ArtilleryStrike,
    Infantry,
    Fighter,
    Bomber,
    Tank35T,
    FiatCR42,
    FiatG50,
    Flak88,
    PantherG,
    SavoiaCavalry,
    StugIIIF,
    LightTank,
    PanzerIIIL,
)
from kards_sim.engine import Engine
from kards_sim.state import GameConfig
from kards_sim.types import Lane, PlayerId, UnitClass, Zone

from conftest import place_on_board


# -- Tank35T ---------------------------------------------------------------

def test_tank35t_reduces_acost_with_friendly_infantry(engine: Engine) -> None:
    state = Engine.new_game(
        [GermanyHeadquarters, Tank35T],
        [SovietHeadquarters],
        seed=1,
        config=GameConfig(starting_hand=1),
    )

    ap = state.active_player
    state.players[ap].max_credits = 2
    state.players[ap].credits = 2

    inf = state.allocate_card(Infantry, owner=ap)
    place_on_board(state, inf, Lane.SUPPORTLINE)

    tank = state.players[ap].hand[0]
    res = engine.step(state, PlayCard(player_id=ap, card=tank, index=0))
    assert res.violation is None
    assert state.inst(tank).operation_cost == 0


# -- FiatCR42 --------------------------------------------------------------

def test_fiat_cr42_gains_attack_when_outnumbering(engine: Engine) -> None:
    state = Engine.new_game(
        [GermanyHeadquarters, FiatCR42],
        [SovietHeadquarters],
        seed=1,
        config=GameConfig(starting_hand=1),
    )

    ap = state.active_player

    inf = state.allocate_card(Infantry, owner=ap)
    place_on_board(state, inf, Lane.SUPPORTLINE)

    fiat_iid = state.players[ap].hand[0]
    res = engine.step(state, PlayCard(player_id=ap, card=fiat_iid, index=0))
    assert res.violation is None
    assert state.inst(fiat_iid).current_attack == 2


def test_fiat_cr42_no_buff_when_not_outnumbering(engine: Engine) -> None:
    state = Engine.new_game(
        [GermanyHeadquarters, FiatCR42],
        [SovietHeadquarters],
        seed=1,
        config=GameConfig(starting_hand=1),
    )

    ap = state.active_player
    opponent = state.opponent(ap)

    enemy_inf = state.allocate_card(Infantry, owner=opponent)
    place_on_board(state, enemy_inf, Lane.SUPPORTLINE)

    fiat_iid = state.players[ap].hand[0]
    res = engine.step(state, PlayCard(player_id=ap, card=fiat_iid, index=0))
    assert res.violation is None
    assert state.inst(fiat_iid).current_attack == 1


# -- SavoiaCavalry ---------------------------------------------------------

def test_savoia_cavalry_has_blitz(engine: Engine) -> None:
    state = Engine.new_game(
        [GermanyHeadquarters, SavoiaCavalry],
        [SovietHeadquarters],
        seed=1,
        config=GameConfig(starting_hand=1),
    )

    ap = state.active_player
    iid = state.players[ap].hand[0]
    res = engine.step(state, PlayCard(player_id=ap, card=iid, index=0))
    assert res.violation is None
    assert not state.inst(iid).exhausted


def test_savoia_cavalry_counts_as_infantry_and_tank() -> None:
    card = SavoiaCavalry()
    assert card.unit_class == UnitClass.INFANTRY
    assert card.counts_as(UnitClass.INFANTRY)
    assert card.counts_as(UnitClass.TANK)
    assert not card.counts_as(UnitClass.ARTILLERY)


def test_savoia_cavalry_triggers_tank35t_deploy(engine: Engine) -> None:
    """Tank35T requires friendly infantry to reduce acost.
    SavoiaCavalry counts as infantry, so it should satisfy that condition."""
    state = Engine.new_game(
        [GermanyHeadquarters, Tank35T],
        [SovietHeadquarters],
        seed=1,
        config=GameConfig(starting_hand=1),
    )

    ap = state.active_player
    state.players[ap].max_credits = 2
    state.players[ap].credits = 2

    savoia = state.allocate_card(SavoiaCavalry, owner=ap)
    place_on_board(state, savoia, Lane.SUPPORTLINE)

    tank = state.players[ap].hand[0]
    res = engine.step(state, PlayCard(player_id=ap, card=tank, index=0))
    assert res.violation is None
    assert state.inst(tank).operation_cost == 0


# -- StugIIIF --------------------------------------------------------------

def test_stug_iii_f_double_attack_vs_tank(engine: Engine) -> None:
    """StuG III F deals double attack damage when attacking a tank."""
    state = Engine.new_game(
        [GermanyHeadquarters], [SovietHeadquarters],
        seed=1, config=GameConfig(starting_hand=0),
    )
    state.players[PlayerId(0)].credits = 10

    stug = state.allocate_card(StugIIIF, owner=PlayerId(0))
    enemy_tank = state.allocate_card(LightTank, owner=PlayerId(1))
    place_on_board(state, stug, Lane.FRONTLINE)
    place_on_board(state, enemy_tank, Lane.SUPPORTLINE)

    # StuG: 2 atk (doubled to 4 vs tank), 3 hp. LightTank: 3 atk, 3 hp.
    res = engine.step(state, Attack(player_id=PlayerId(0), attacker=stug, defender=enemy_tank))
    assert res.violation is None
    assert state.inst(enemy_tank).current_health <= 0
    # Attack restored to 2 after combat
    assert state.inst(stug).current_attack == 2


def test_stug_iii_f_doubles_when_retaliating_vs_tank(engine: Engine) -> None:
    """StuG III F doubles attack when retaliating against a tank too."""
    state = Engine.new_game(
        [GermanyHeadquarters], [SovietHeadquarters],
        seed=1, config=GameConfig(starting_hand=0),
    )
    state.players[PlayerId(0)].credits = 10

    stug = state.allocate_card(StugIIIF, owner=PlayerId(1))
    enemy_tank = state.allocate_card(LightTank, owner=PlayerId(0))
    place_on_board(state, stug, Lane.SUPPORTLINE)
    place_on_board(state, enemy_tank, Lane.FRONTLINE)

    # Enemy LightTank (3 atk, 3 hp) attacks StugIIIF (2 atk → 4 doubled, 3 hp).
    res = engine.step(state, Attack(player_id=PlayerId(0), attacker=enemy_tank, defender=stug))
    assert res.violation is None
    # LightTank: 3 hp - 4 (doubled retaliation) = -1 → destroyed
    assert state.inst(enemy_tank).current_health <= 0
    # StugIIIF: 3 hp - 3 = 0 → also destroyed
    assert state.inst(stug).current_health <= 0
    # Attack restored after combat
    assert state.inst(stug).current_attack == 2


def test_stug_iii_f_normal_attack_vs_infantry(engine: Engine) -> None:
    """StuG III F does NOT double attack against non-tank units."""
    state = Engine.new_game(
        [GermanyHeadquarters], [SovietHeadquarters],
        seed=1, config=GameConfig(starting_hand=0),
    )
    state.players[PlayerId(0)].credits = 10

    stug = state.allocate_card(StugIIIF, owner=PlayerId(0))
    enemy_inf = state.allocate_card(Infantry, owner=PlayerId(1))
    place_on_board(state, stug, Lane.FRONTLINE)
    place_on_board(state, enemy_inf, Lane.SUPPORTLINE)

    # StuG: 2 atk (no doubling vs infantry). Infantry: 1 hp → destroyed.
    res = engine.step(state, Attack(player_id=PlayerId(0), attacker=stug, defender=enemy_inf))
    assert res.violation is None
    assert state.inst(enemy_inf).current_health <= 0
    assert state.inst(stug).current_attack == 2


# -- FiatG50 ---------------------------------------------------------------

def test_fiat_g50_heals_hq_on_deal_damage(engine: Engine) -> None:
    """菲亚特G.50造成伤害时，友方总部恢复同等防御力。"""
    state = Engine.new_game(
        [GermanyHeadquarters], [SovietHeadquarters],
        seed=1, config=GameConfig(starting_hand=0),
    )
    state.players[PlayerId(0)].credits = 10

    # Damage our HQ first so we can observe the heal
    hq0_iid = state.players[PlayerId(0)].hq_iid
    state.inst(hq0_iid).current_health = 15  # 5 damage taken

    fiat = state.allocate_card(FiatG50, owner=PlayerId(0))
    enemy_inf = state.allocate_card(Infantry, owner=PlayerId(1))
    place_on_board(state, fiat, Lane.FRONTLINE)
    place_on_board(state, enemy_inf, Lane.SUPPORTLINE)

    # Fiat G.50: 2 atk. Deals 2 damage to infantry → HQ heals 2 (15 → 17)
    res = engine.step(state, Attack(player_id=PlayerId(0), attacker=fiat, defender=enemy_inf))
    assert res.violation is None
    assert state.inst(hq0_iid).current_health == 17


def test_fiat_g50_heal_does_not_exceed_max_hp(engine: Engine) -> None:
    """治疗不应超过总部最大生命值。"""
    state = Engine.new_game(
        [GermanyHeadquarters], [SovietHeadquarters],
        seed=1, config=GameConfig(starting_hand=0),
    )
    state.players[PlayerId(0)].credits = 10

    hq0_iid = state.players[PlayerId(0)].hq_iid
    assert state.inst(hq0_iid).current_health == 20  # full HP

    fiat = state.allocate_card(FiatG50, owner=PlayerId(0))
    enemy_inf = state.allocate_card(Infantry, owner=PlayerId(1))
    place_on_board(state, fiat, Lane.FRONTLINE)
    place_on_board(state, enemy_inf, Lane.SUPPORTLINE)

    res = engine.step(state, Attack(player_id=PlayerId(0), attacker=fiat, defender=enemy_inf))
    assert res.violation is None
    # HQ already at max 20, heal should not push above
    assert state.inst(hq0_iid).current_health == 20


# -- PanzerIIIL ---------------------------------------------------------------

def test_panzer_iii_l_gains_attack_from_non_tank_types(engine: Engine) -> None:
    state = Engine.new_game(
        [GermanyHeadquarters, PanzerIIIL],
        [SovietHeadquarters],
        seed=1,
        config=GameConfig(starting_hand=1),
    )
    state.players[PlayerId(0)].credits = 10

    inf = state.allocate_card(Infantry, owner=PlayerId(0))
    place_on_board(state, inf, Lane.SUPPORTLINE)
    ftr = state.allocate_card(Fighter, owner=PlayerId(0))
    place_on_board(state, ftr, Lane.SUPPORTLINE)

    pz_iid = state.players[PlayerId(0)].hand[0]
    res = engine.step(state, PlayCard(player_id=PlayerId(0), card=pz_iid, index=0))
    assert res.violation is None
    # 2 distinct non-tank types (infantry + fighter) → base 3 + 2 = 5
    assert state.inst(pz_iid).current_attack == 5


def test_panzer_iii_l_no_bonus_without_non_tank(engine: Engine) -> None:
    state = Engine.new_game(
        [GermanyHeadquarters, PanzerIIIL],
        [SovietHeadquarters],
        seed=1,
        config=GameConfig(starting_hand=1),
    )
    state.players[PlayerId(0)].credits = 10

    tank = state.allocate_card(LightTank, owner=PlayerId(0))
    place_on_board(state, tank, Lane.SUPPORTLINE)

    pz_iid = state.players[PlayerId(0)].hand[0]
    res = engine.step(state, PlayCard(player_id=PlayerId(0), card=pz_iid, index=0))
    assert res.violation is None
    # Only friendly tank on board → 0 non-tank types → attack stays 3
    assert state.inst(pz_iid).current_attack == 3


def test_panzer_iii_l_updates_on_new_deploy(engine: Engine) -> None:
    state = Engine.new_game(
        [GermanyHeadquarters, PanzerIIIL],
        [SovietHeadquarters],
        seed=1,
        config=GameConfig(starting_hand=1),
    )
    state.players[PlayerId(0)].credits = 20

    pz_iid = state.players[PlayerId(0)].hand[0]
    res = engine.step(state, PlayCard(player_id=PlayerId(0), card=pz_iid, index=0))
    assert res.violation is None
    # No friendlies yet → attack = 3
    assert state.inst(pz_iid).current_attack == 3

    inf_iid = state.allocate_card(Infantry, owner=PlayerId(0))
    state.players[PlayerId(0)].hand.append(inf_iid)
    state.inst(inf_iid).zone = Zone.HAND
    res2 = engine.step(state, PlayCard(player_id=PlayerId(0), card=inf_iid, index=0))
    assert res2.violation is None
    # Infantry deployed → 1 non-tank type → attack = 4
    assert state.inst(pz_iid).current_attack == 4


# -- Flak88 -------------------------------------------------------------------

def test_flak88_doubles_vs_tank(engine: Engine) -> None:
    state = Engine.new_game(
        [GermanyHeadquarters], [SovietHeadquarters],
        seed=1, config=GameConfig(starting_hand=0),
    )
    state.players[PlayerId(0)].credits = 10

    flak = state.allocate_card(Flak88, owner=PlayerId(0))
    enemy_tank = state.allocate_card(LightTank, owner=PlayerId(1))
    place_on_board(state, flak, Lane.FRONTLINE)
    place_on_board(state, enemy_tank, Lane.SUPPORTLINE)

    # Flak88: 3 atk → 6 doubled vs tank; LightTank: 3 hp
    res = engine.step(state, Attack(player_id=PlayerId(0), attacker=flak, defender=enemy_tank))
    assert res.violation is None
    assert state.inst(enemy_tank).current_health <= 0
    assert state.inst(flak).current_attack == 3


def test_flak88_doubles_vs_fighter(engine: Engine) -> None:
    state = Engine.new_game(
        [GermanyHeadquarters], [SovietHeadquarters],
        seed=1, config=GameConfig(starting_hand=0),
    )
    state.players[PlayerId(0)].credits = 10

    flak = state.allocate_card(Flak88, owner=PlayerId(0))
    enemy_ftr = state.allocate_card(Fighter, owner=PlayerId(1))
    place_on_board(state, flak, Lane.FRONTLINE)
    place_on_board(state, enemy_ftr, Lane.SUPPORTLINE)

    # Flak88: 3 atk → 6 doubled vs fighter
    res = engine.step(state, Attack(player_id=PlayerId(0), attacker=flak, defender=enemy_ftr))
    assert res.violation is None
    assert state.inst(enemy_ftr).current_health <= 0
    assert state.inst(flak).current_attack == 3


def test_flak88_ambush_doubles_vs_tank(engine: Engine) -> None:
    """When a tank attacks Flak88, ambush strikes first with doubled attack."""
    state = Engine.new_game(
        [GermanyHeadquarters], [SovietHeadquarters],
        seed=1, config=GameConfig(starting_hand=0),
    )
    state.players[PlayerId(0)].credits = 10

    flak = state.allocate_card(Flak88, owner=PlayerId(1))
    enemy_tank = state.allocate_card(LightTank, owner=PlayerId(0))
    place_on_board(state, flak, Lane.SUPPORTLINE)
    place_on_board(state, enemy_tank, Lane.FRONTLINE)

    # LightTank (3 atk, 3 hp) attacks Flak88 (3 atk → 6 doubled, 4 hp).
    # Ambush: Flak88 strikes first with 6, kills LightTank (3 hp).
    # LightTank dies before dealing damage → Flak88 takes 0 damage.
    res = engine.step(state, Attack(player_id=PlayerId(0), attacker=enemy_tank, defender=flak))
    assert res.violation is None
    assert state.inst(enemy_tank).current_health <= 0
    assert state.inst(flak).current_health == 4  # untouched
    assert state.inst(flak).current_attack == 3  # restored


def test_flak88_ambush_no_double_vs_infantry(engine: Engine) -> None:
    """When infantry attacks Flak88, ambush strikes first but NOT doubled."""
    state = Engine.new_game(
        [GermanyHeadquarters], [SovietHeadquarters],
        seed=1, config=GameConfig(starting_hand=0),
    )
    state.players[PlayerId(0)].credits = 10

    flak = state.allocate_card(Flak88, owner=PlayerId(1))
    enemy_inf = state.allocate_card(Infantry, owner=PlayerId(0))
    place_on_board(state, flak, Lane.SUPPORTLINE)
    place_on_board(state, enemy_inf, Lane.FRONTLINE)

    # Infantry (1 atk, 1 hp) attacks Flak88 (3 atk normal, 4 hp).
    # Ambush: Flak88 strikes first with 3, kills Infantry (1 hp).
    res = engine.step(state, Attack(player_id=PlayerId(0), attacker=enemy_inf, defender=flak))
    assert res.violation is None
    assert state.inst(enemy_inf).current_health <= 0
    assert state.inst(flak).current_health == 4
    assert state.inst(flak).current_attack == 3


def test_flak88_normal_vs_infantry(engine: Engine) -> None:
    state = Engine.new_game(
        [GermanyHeadquarters], [SovietHeadquarters],
        seed=1, config=GameConfig(starting_hand=0),
    )
    state.players[PlayerId(0)].credits = 10

    flak = state.allocate_card(Flak88, owner=PlayerId(0))
    enemy_inf = state.allocate_card(Infantry, owner=PlayerId(1))
    place_on_board(state, flak, Lane.FRONTLINE)
    place_on_board(state, enemy_inf, Lane.SUPPORTLINE)

    # Flak88: 3 atk (no double vs infantry); Infantry: 1 hp
    res = engine.step(state, Attack(player_id=PlayerId(0), attacker=flak, defender=enemy_inf))
    assert res.violation is None
    assert state.inst(enemy_inf).current_health <= 0
    assert state.inst(flak).current_attack == 3


# -- PantherG -----------------------------------------------------------------

def test_panther_g_has_heavy_armor_1() -> None:
    card = PantherG()
    assert card.heavy_armor == 1
    assert card.order_immune is True


def test_panther_g_immune_to_enemy_orders(engine: Engine) -> None:
    state = Engine.new_game(
        [GermanyHeadquarters, ArtilleryStrike],
        [SovietHeadquarters],
        seed=1, config=GameConfig(starting_hand=1),
    )
    state.players[PlayerId(0)].credits = 10

    panther = state.allocate_card(PantherG, owner=PlayerId(1))
    place_on_board(state, panther, Lane.SUPPORTLINE)

    order_iid = state.players[PlayerId(0)].hand[0]
    res = engine.step(
        state,
        PlayCard(player_id=PlayerId(0), card=order_iid, target=panther),
    )
    assert res.violation is not None
    assert "immune" in res.violation.reason
