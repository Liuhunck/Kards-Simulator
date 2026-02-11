from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cards.registry import CardCatalog
    from .cards.definitions import CardDefinition
from .types import BoardPos, CardType, InstanceId, Lane, PlayerId, Zone


@dataclass(slots=True)
class CardInstance:
    instance_id: InstanceId
    def_id: str
    owner: PlayerId
    zone: Zone
    lane: Lane | None = None
    pos: BoardPos | None = None  # not used

    cost: int | None = None

    base_attack: int | None = None
    base_health: int | None = None

    damage_taken: int = 0
    exhausted: bool = True

    @property
    def attack(self) -> int | None:
        return self.base_attack

    @property
    def max_health(self) -> int | None:
        return self.base_health

    @property
    def current_health(self) -> int | None:
        if self.base_health is None:
            return None
        return self.base_health - self.damage_taken

    @property
    def is_dead(self) -> bool:
        h = self.current_health
        return h is not None and h <= 0


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
    starting_p0_hp: int = 20
    starting_p1_hp: int = 20


@dataclass(slots=True)
class GameState:
    config: GameConfig
    definitions: dict[str, "CardDefinition"]
    card_catalog: "CardCatalog"
    instances: dict[InstanceId, CardInstance]
    players: dict[PlayerId, PlayerState]

    supportline: dict[PlayerId, list[InstanceId]] = field(default_factory=dict)
    frontline: list[InstanceId] = field(default_factory=list)

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

    def get_instance(self, iid: InstanceId) -> CardInstance:
        return self.instances[iid]

    def get_def(self, def_id: str) -> CardDefinition:
        return self.definitions[def_id]

    def get_card(self, def_id: str):
        return self.card_catalog.get(def_id)

    def get_card_for_instance(self, iid: InstanceId):
        return self.get_card(self.get_instance(iid).def_id)

    def allocate_base_instance(self, owner: PlayerId, hp: int) -> InstanceId:
        iid = InstanceId(self.next_instance_id)
        self.next_instance_id += 1
        inst = CardInstance(
            instance_id=iid,
            def_id="BASE",
            owner=owner,
            zone=Zone.BOARD,
            base_health=hp,
        )
        inst.lane = Lane.SUPPORTLINE
        self.instances[iid] = inst
        return iid

    def allocate_instance(self, def_id: str, owner: PlayerId, zone: Zone) -> InstanceId:
        iid = InstanceId(self.next_instance_id)
        self.next_instance_id += 1
        defn = self.get_def(def_id)
        inst = CardInstance(
            instance_id=iid,
            def_id=def_id,
            owner=owner,
            zone=zone,
            base_attack=defn.attack,
            base_health=defn.health,
        )
        self.instances[iid] = inst
        return iid

    def card_type_of(self, iid: InstanceId) -> CardType:
        return self.get_def(self.get_instance(iid).def_id).card_type

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
                    "def_id": inst.def_id,
                    "owner": int(inst.owner),
                    "zone": inst.zone.value,
                    "lane": inst.lane.value if inst.lane else None,
                    "cost": inst.cost,
                    "attack": inst.attack,
                    "max_health": inst.max_health,
                    "current_health": inst.current_health,
                    "exhausted": inst.exhausted,
                }
                for iid, inst in self.instances.items()
            },
        }
