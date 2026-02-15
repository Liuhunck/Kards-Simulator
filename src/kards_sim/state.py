from __future__ import annotations

from dataclasses import dataclass, field

from .cards.base import CardBase
from .cards.bases import BaseCardBase
from .types import CardType, InstanceId, Lane, PlayerId, Zone


@dataclass(slots=True)
class CardInstance:
    instance_id: InstanceId
    card: CardBase
    owner: PlayerId
    zone: Zone
    lane: Lane
    exhausted: bool = True


@dataclass(slots=True)
class PlayerState:
    player_id: PlayerId
    base_card_id: InstanceId
    credits: int = 0
    max_credits: int = 0

    deck: list[InstanceId] = field(default_factory=list)
    hand: list[InstanceId] = field(default_factory=list)
    discard: list[InstanceId] = field(default_factory=list)
    countermeasures: list[InstanceId] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PendingChoice:
    player_id: PlayerId
    prompt: str
    valid_targets: tuple[str, ...] = ()


@dataclass(slots=True)
class GameConfig:
    columns: int = 5
    starting_hand: int = 4
    starting_p0_hp: int | None = None
    starting_p1_hp: int | None = None


@dataclass(slots=True)
class GameState:
    config: GameConfig
    players: dict[PlayerId, PlayerState]
    instances: dict[InstanceId, CardInstance]

    frontline: list[InstanceId] = field(default_factory=list)
    supportline: dict[PlayerId, list[InstanceId]] = field(default_factory=dict)

    active_player: PlayerId = PlayerId(0)
    turn: int = 1
    rng_seed: int = 1

    next_instance_id: int = 1
    pending_choice: PendingChoice | None = None

    def other(self, pid: PlayerId) -> PlayerId:
        return PlayerId(1) if pid == PlayerId(0) else PlayerId(0)

    def frontline_owner(self) -> PlayerId | None:
        if len(self.frontline) == 0:
            return None
        return self.get_instance(self.frontline[0]).owner

    def all_board_unit_ids(self) -> list[InstanceId]:
        out: list[InstanceId] = []
        for _, slots in self.supportline.items():
            out.extend(slots)
        out.extend(self.frontline)
        return out

    def all_board_card_ids(self) -> list[InstanceId]:
        out = self.all_board_unit_ids()
        for p in self.players.values():
            out.append(p.base_card_id)
        return out

    def get_instance(self, iid: InstanceId) -> CardInstance:
        return self.instances[iid]

    def get_attack(self, iid: InstanceId) -> int | None:
        card = self.get_card_for_instance(iid)
        return getattr(card, "attack_value", None)

    def get_max_health(self, iid: InstanceId) -> int | None:
        card = self.get_card_for_instance(iid)
        return getattr(card, "health_value", None)

    def get_damage_taken(self, iid: InstanceId) -> int:
        card = self.get_card_for_instance(iid)
        current_health = getattr(card, "current_health", None)
        max_health = getattr(card, "health_value", None)
        if current_health is None or max_health is None:
            return 0
        return max(0, int(max_health) - int(current_health))

    def get_current_health(self, iid: InstanceId) -> int | None:
        card = self.get_card_for_instance(iid)
        current = getattr(card, "current_health", None)
        if current is not None:
            return int(current)
        return getattr(card, "health_value", None)

    def is_dead(self, iid: InstanceId) -> bool:
        health = self.get_current_health(iid)
        return health is not None and health <= 0

    def get_action_cost(self, iid: InstanceId) -> int | None:
        card = self.get_card_for_instance(iid)
        return getattr(card, "acost", None)

    def set_action_cost(self, iid: InstanceId, value: int) -> None:
        card = self.get_card_for_instance(iid)
        card.acost = int(value)

    def apply_damage(self, iid: InstanceId, amount: int) -> None:
        card = self.get_card_for_instance(iid)
        card.health_value -= int(amount)

    def get_card_for_instance(self, iid: InstanceId):
        return self.instances[iid].card

    def get_next_iid(self) -> InstanceId:
        out = self.next_instance_id
        self.next_instance_id += 1
        return InstanceId(out)

    def allocate_base_instance(
        self,
        base_card_cls: type["BaseCardBase"],
        owner: PlayerId,
        hp: int | None = None,
    ) -> InstanceId:
        iid = self.get_next_iid()
        card_obj = base_card_cls()
        if hp is not None:
            card_obj.health_value = int(hp)
        self.instances[iid] = CardInstance(
            instance_id=iid,
            card=card_obj,
            owner=owner,
            zone=Zone.BOARD,
            lane=Lane.SUPPORTLINE,
        )
        return iid

    def allocate_instance(
        self, card_cls: type["CardBase"], owner: PlayerId
    ) -> InstanceId:
        iid = self.get_next_iid()
        card_obj = card_cls()
        self.instances[iid] = CardInstance(
            instance_id=iid,
            card=card_obj,
            owner=owner,
            zone=Zone.DECK,
            lane=Lane.NOT_ON_BOARD,
        )
        return iid

    def card_type_of(self, iid: InstanceId) -> CardType:
        return self.instances[iid].card.card_type

    def to_observation(self) -> dict:
        """Stable, minimal observation dict for RL integrations."""
        return {
            "turn": self.turn,
            "active_player": int(self.active_player),
            "players": {
                int(pid): {
                    "credits": p.credits,
                    "max_credits": p.max_credits,
                    "deck": [int(iid) for iid in p.deck],
                    "hand": [int(iid) for iid in p.hand],
                    "discard": [int(iid) for iid in p.discard],
                    "countermeasures": [int(iid) for iid in p.countermeasures],
                    "base": int(p.base_card_id),
                }
                for pid, p in self.players.items()
            },
            "supportline": {
                int(pid): [int(iid) for iid in slots]
                for pid, slots in self.supportline.items()
            },
            "frontline": [int(iid) for iid in self.frontline],
            "instances": {
                int(iid): {
                    "card_class": inst.card.__class__.__name__,
                    "owner": int(inst.owner),
                    "zone": inst.zone.value,
                    "lane": inst.lane.value if inst.lane else None,
                    "cost": self.get_action_cost(iid),
                    "attack": self.get_attack(iid),
                    "max_health": self.get_max_health(iid),
                    "current_health": self.get_current_health(iid),
                    "exhausted": inst.exhausted,
                }
                for iid, inst in self.instances.items()
            },
        }
