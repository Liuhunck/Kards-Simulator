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

    def play(self, state: GameState, action: PlayCard) -> list:
        can_play_card(state, action.player_id, action.card)
        require(action.index is not None, "unit requires index")
        assert action.index is not None
        can_deploy_unit(state, action.player_id, action.card, action.index)

        inst = state.get_instance(action.card)
        player = state.players[action.player_id]

        player.credits -= self.definition.cost
        player.hand.remove(action.card)
        state.supportline[action.player_id].insert(action.index, action.card)

        inst.cost = self.definition.acost
        inst.zone = Zone.BOARD
        inst.lane = Lane.SUPPORTLINE
        inst.exhausted = True

        return [
            CardPlayed(
                player_id=action.player_id,
                card=action.card,
                target=action.target,
                target_player=(
                    state.other(action.player_id) if action.target_hq else None
                ),
            ),
            UnitDeployed(
                player_id=action.player_id,
                unit=action.card,
                pos=action.index,
            ),
        ]

    def advance(self, state: GameState, action: Advance) -> list:
        can_advance_unit(state, action.player_id, action.card, action.index)
        inst = state.get_instance(action.card)
        assert inst.cost is not None

        state.players[action.player_id].credits -= inst.cost
        state.supportline[action.player_id].remove(action.card)
        state.frontline.insert(action.index, action.card)
        inst.lane = Lane.FRONTLINE

        return [
            UnitAdvanced(
                player_id=action.player_id,
                unit=action.card,
                pos=action.index,
            )
        ]

    def attack(self, state: GameState, action: Attack) -> list:
        can_attack(state, action.player_id, action.attacker, action.defender)

        a = state.get_instance(action.attacker)
        a.exhausted = True

        assert action.defender is not None
        d = state.get_instance(action.defender)

        a_def = state.get_def(a.def_id)
        d_def = state.get_def(d.def_id)

        def has_retaliatory_damage() -> bool:
            if d_def.card_type == CardType.BASE:
                return False
            if a_def.unit_class == UnitClass.ARTILLERY:
                return False
            if (
                a_def.unit_class == UnitClass.BOMBER
                and d_def.unit_class != UnitClass.FIGHTER
            ):
                return False
            if d_def.unit_class == UnitClass.BOMBER:
                return False
            return True

        # Keyword check: ambush on the defender means defender strikes first.
        has_ambush = any(
            spec.ability_id.lower() == "ambush" for spec in d_def.abilities
        )

        assert a.current_health is not None
        assert d.current_health is not None
        assert a.attack is not None

        out: list = []
        if has_ambush:
            assert d.attack is not None
            out.append(
                DamageDealt(
                    source=action.defender,
                    target=action.attacker,
                    amount=d.attack,
                    target_player=None,
                )
            )
            if d.attack < a.current_health:
                out.append(
                    DamageDealt(
                        source=action.attacker,
                        target=action.defender,
                        amount=a.attack,
                        target_player=None,
                    )
                )
        elif has_retaliatory_damage():
            out.append(
                DamageDealt(
                    source=action.attacker,
                    target=action.defender,
                    amount=a.attack,
                    target_player=None,
                )
            )
            assert d.attack is not None
            out.append(
                DamageDealt(
                    source=action.defender,
                    target=action.attacker,
                    amount=d.attack,
                    target_player=None,
                )
            )
        else:
            out.append(
                DamageDealt(
                    source=action.attacker,
                    target=action.defender,
                    amount=a.attack,
                    target_player=None,
                )
            )

        return out
