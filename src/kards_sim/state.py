from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .types import CardType, InstanceId, Keyword, Lane, PlayerId, UnitClass, Zone

if TYPE_CHECKING:
    from .cards.base import CardBase


@dataclass(slots=True)
class CardInstance:
    """Runtime state for a single card on the table.

    The *card* reference points to the immutable card definition (class
    instance).  All mutable per-game state lives here so that the card
    template itself is never modified.
    """

    iid: InstanceId
    card: CardBase
    owner: PlayerId
    zone: Zone
    lane: Lane

    current_health: int = 0
    current_attack: int = 0
    operation_cost: int = 0

    exhausted: bool = True

    attacks_this_turn: int = 0
    smokescreen_active: bool = False
    ambush_available: bool = True
    mobilize_active: bool = True


@dataclass(slots=True)
class PlayerState:
    player_id: PlayerId
    hq_iid: InstanceId
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
    game_over: bool = False
    winner: PlayerId | None = None

    # ---- helpers ---------------------------------------------------------

    def opponent(self, pid: PlayerId) -> PlayerId:
        return PlayerId(1) if pid == PlayerId(0) else PlayerId(0)

    def frontline_owner(self) -> PlayerId | None:
        if not self.frontline:
            return None
        return self.inst(self.frontline[0]).owner

    # ---- instance access -------------------------------------------------

    def inst(self, iid: InstanceId) -> CardInstance:
        return self.instances[iid]

    def card(self, iid: InstanceId) -> CardBase:
        return self.instances[iid].card

    def card_type_of(self, iid: InstanceId) -> CardType:
        return self.instances[iid].card.card_type

    # ---- board queries ---------------------------------------------------

    def board_unit_iids(self) -> list[InstanceId]:
        out: list[InstanceId] = []
        for slots in self.supportline.values():
            out.extend(slots)
        out.extend(self.frontline)
        return out

    def board_all_iids(self) -> list[InstanceId]:
        out = self.board_unit_iids()
        for p in self.players.values():
            out.append(p.hq_iid)
        return out

    def friendly_board_iids(self, pid: PlayerId) -> list[InstanceId]:
        out: list[InstanceId] = []
        for iid in self.board_unit_iids():
            if self.inst(iid).owner == pid:
                out.append(iid)
        return out

    def enemy_board_iids(self, pid: PlayerId) -> list[InstanceId]:
        return self.friendly_board_iids(self.opponent(pid))

    def has_keyword(self, iid: InstanceId, kw: Keyword) -> bool:
        if kw is Keyword.HEAVY_ARMOR:
            return self.card(iid).heavy_armor > 0
        return kw in self.card(iid).keywords

    # ---- health / damage -------------------------------------------------

    def is_alive(self, iid: InstanceId) -> bool:
        return self.inst(iid).current_health > 0

    def is_dead(self, iid: InstanceId) -> bool:
        ci = self.inst(iid)
        return ci.zone == Zone.BOARD and ci.current_health <= 0

    def apply_damage(self, iid: InstanceId, amount: int) -> int:
        """Apply *amount* damage and return the effective damage dealt."""
        ci = self.inst(iid)
        effective = max(0, amount)
        ci.current_health -= effective
        return effective

    # ---- id allocation ---------------------------------------------------

    def _next_iid(self) -> InstanceId:
        iid = InstanceId(self.next_instance_id)
        self.next_instance_id += 1
        return iid

    def allocate_hq(
        self,
        card_cls: type[CardBase],
        owner: PlayerId,
        hp_override: int | None = None,
    ) -> InstanceId:
        iid = self._next_iid()
        card_obj = card_cls()
        hp = hp_override if hp_override is not None else getattr(card_obj, "health_value", 20)
        self.instances[iid] = CardInstance(
            iid=iid,
            card=card_obj,
            owner=owner,
            zone=Zone.BOARD,
            lane=Lane.SUPPORTLINE,
            current_health=hp,
        )
        return iid

    def allocate_card(
        self, card_cls: type[CardBase], owner: PlayerId
    ) -> InstanceId:
        iid = self._next_iid()
        card_obj = card_cls()
        self.instances[iid] = CardInstance(
            iid=iid,
            card=card_obj,
            owner=owner,
            zone=Zone.DECK,
            lane=Lane.NOT_ON_BOARD,
            current_health=getattr(card_obj, "health_value", 0),
            current_attack=getattr(card_obj, "attack_value", 0),
            operation_cost=getattr(card_obj, "acost", 0),
        )
        return iid

    # ---- observation for RL ----------------------------------------------

    def to_observation(self) -> dict:
        """Stable, minimal observation dict for RL integrations."""
        obs: dict = {
            "turn": self.turn,
            "active_player": int(self.active_player),
            "game_over": self.game_over,
            "winner": int(self.winner) if self.winner is not None else None,
            "players": {},
            "supportline": {},
            "frontline": [int(i) for i in self.frontline],
            "instances": {},
        }
        for pid, p in self.players.items():
            obs["players"][int(pid)] = {
                "credits": p.credits,
                "max_credits": p.max_credits,
                "deck_size": len(p.deck),
                "hand": [int(i) for i in p.hand],
                "discard": [int(i) for i in p.discard],
                "hq": int(p.hq_iid),
            }
        for pid, slots in self.supportline.items():
            obs["supportline"][int(pid)] = [int(i) for i in slots]
        for iid, ci in self.instances.items():
            obs["instances"][int(iid)] = {
                "card_class": ci.card.__class__.__name__,
                "owner": int(ci.owner),
                "zone": ci.zone.value,
                "lane": ci.lane.value,
                "current_health": ci.current_health,
                "current_attack": ci.current_attack,
                "operation_cost": ci.operation_cost,
                "exhausted": ci.exhausted,
                "keywords": [kw.value for kw in ci.card.keywords],
            }
        return obs
