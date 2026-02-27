from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import NewType


InstanceId = NewType("InstanceId", int)
PlayerId = NewType("PlayerId", int)


class CardType(str, Enum):
    HEADQUARTERS = "headquarters"
    UNIT = "unit"
    ORDER = "order"
    COUNTERMEASURE = "countermeasure"


class UnitClass(str, Enum):
    INFANTRY = "infantry"
    TANK = "tank"
    ARTILLERY = "artillery"
    FIGHTER = "fighter"
    BOMBER = "bomber"


class Nation(str, Enum):
    USA = "usa"
    GERMANY = "germany"
    SOVIET = "soviet"
    JAPAN = "japan"
    BRITAIN = "britain"
    FRANCE = "france"
    ITALY = "italy"
    POLAND = "poland"
    FINLAND = "finland"
    NEUTRAL = "neutral"


class Lane(str, Enum):
    FRONTLINE = "frontline"
    SUPPORTLINE = "supportline"
    NOT_ON_BOARD = "not_on_board"


class Zone(str, Enum):
    DECK = "deck"
    HAND = "hand"
    DISCARD = "discard"
    BOARD = "board"


class Keyword(str, Enum):
    """Reusable keyword abilities handled by the engine.

    These are common mechanics shared by many cards. The resolver and
    rules modules contain the built-in logic for each keyword; individual
    card classes only need to list which keywords they possess.
    """

    GUARD = "guard"
    """Adjacent non-guard units cannot be attacked (except by bombers/artillery)."""

    HEAVY_ARMOR = "heavy_armor"
    """Incoming unit damage is reduced (up to 3)."""

    BLITZ = "blitz"
    """Can operate (move/attack) on the same turn it is deployed."""

    FURY = "fury"
    """Can attack twice per turn."""

    AMBUSH = "ambush"
    """When attacked, strikes first. If the attacker dies, it deals no damage."""

    SMOKESCREEN = "smokescreen"
    """Cannot be targeted by enemy units until it moves or attacks."""

    MOBILIZE = "mobilize"
    """Gains +1/+1 at the start of its owner's turn. Lost when damaged."""

    PINCER = "pincer"
    """On deploy, choose another friendly unit; both gain a shared buff."""

    LONG_RANGE = "long_range"
    """Can attack any lane without adjacency restriction."""

    RESISTANCE = "resistance"
    """Takes 1 less damage from orders."""


@dataclass(frozen=True, slots=True)
class BoardPos:
    lane: Lane
    index: int
