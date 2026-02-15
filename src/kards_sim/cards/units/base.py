from __future__ import annotations

from typing import TYPE_CHECKING

from ...actions import Advance, Attack, PlayCard
from ...events import CardPlayed, DamageDealt, UnitAdvanced, UnitDeployed
from ...rules import (
    can_advance_unit,
    can_attack,
    can_deploy_unit,
    can_play_card,
    require,
)
from ...types import CardType, Lane, UnitClass, Zone
from ..base import CardBase

if TYPE_CHECKING:
    from ...state import GameState


class UnitCardBase(CardBase):
    """Shared behavior for unit cards."""

    card_type = CardType.UNIT
    cost: int
    acost: int
    unit_class: UnitClass
    attack_value: int
    health_value: int

    def deploy(self, state: GameState, action: PlayCard) -> list:
        iid = action.card
        can_play_card(state, action.player_id, iid)
        require(action.index is not None, "unit requires index")
        assert action.index is not None
        can_deploy_unit(state, action.player_id, iid, action.index)

        inst = state.get_instance(iid)
        player = state.players[action.player_id]
        card = state.get_card_for_instance(iid)
        require(getattr(card, "cost", None) is not None, "unit missing cost")
        require(getattr(card, "acost", None) is not None, "unit missing acost")

        player.credits -= int(card.cost)
        player.hand.remove(iid)
        state.supportline[action.player_id].insert(action.index, iid)

        state.set_action_cost(iid, int(card.acost))
        inst.zone = Zone.BOARD
        inst.lane = Lane.SUPPORTLINE
        inst.exhausted = True

        return [
            CardPlayed(
                player_id=action.player_id,
                card=iid,
                target=action.target,
                target_player=(
                    state.other(action.player_id) if action.target_hq else None
                ),
            ),
            UnitDeployed(
                player_id=action.player_id,
                unit=iid,
                pos=action.index,
            ),
        ]

    def advance(self, state: GameState, action: Advance) -> list:
        iid = action.card
        can_advance_unit(state, action.player_id, iid, action.index)
        inst = state.get_instance(iid)
        action_cost = state.get_action_cost(iid)
        assert action_cost is not None

        state.players[action.player_id].credits -= action_cost
        state.supportline[action.player_id].remove(iid)
        state.frontline.insert(action.index, iid)
        inst.lane = Lane.FRONTLINE

        return [
            UnitAdvanced(
                player_id=action.player_id,
                unit=iid,
                pos=action.index,
            )
        ]

    def attack(self, state: GameState, action: Attack) -> list:
        iid = action.attacker
        can_attack(state, action.player_id, iid, action.defender)

        a = state.get_instance(iid)
        a.exhausted = True

        assert action.defender is not None
        d = state.get_instance(action.defender)

        a_card = state.get_card_for_instance(iid)
        d_card = state.get_card_for_instance(action.defender)

        def has_retaliatory_damage() -> bool:
            if d_card.card_type == CardType.BASE:
                return False
            if a_card.unit_class == UnitClass.ARTILLERY:
                return False
            if (
                a_card.unit_class == UnitClass.BOMBER
                and d_card.unit_class != UnitClass.FIGHTER
            ):
                return False
            if d_card.unit_class == UnitClass.BOMBER:
                return False
            return True

        # Keyword check: ambush on the defender means defender strikes first.
        has_ambush = any(
            spec.ability_id.lower() == "ambush" for spec in d_card.abilities
        )

        a_current_health = state.get_current_health(iid)
        d_current_health = state.get_current_health(action.defender)
        a_attack = state.get_attack(iid)
        d_attack = state.get_attack(action.defender)

        assert a_current_health is not None
        assert d_current_health is not None
        assert a_attack is not None

        out: list = []
        if has_ambush:
            assert d_attack is not None
            out.append(
                DamageDealt(
                    source=action.defender,
                    target=iid,
                    amount=d_attack,
                    target_player=None,
                )
            )
            if d_attack < a_current_health:
                out.append(
                    DamageDealt(
                        source=iid,
                        target=action.defender,
                        amount=a_attack,
                        target_player=None,
                    )
                )
        elif has_retaliatory_damage():
            out.append(
                DamageDealt(
                    source=iid,
                    target=action.defender,
                    amount=a_attack,
                    target_player=None,
                )
            )
            assert d_attack is not None
            out.append(
                DamageDealt(
                    source=action.defender,
                    target=iid,
                    amount=d_attack,
                    target_player=None,
                )
            )
        else:
            out.append(
                DamageDealt(
                    source=iid,
                    target=action.defender,
                    amount=a_attack,
                    target_player=None,
                )
            )

        return out
