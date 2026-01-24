from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import NewType


InstanceId = NewType("InstanceId", int)
PlayerId = NewType("PlayerId", int)


class CardType(str, Enum):
    BASE = "base"
    UNIT = "unit"
    ORDER = "order"
    COUNTERMEASURE = "countermeasure"


class UnitClass(str, Enum):
    INFANTRY = "infantry"
    TANK = "tank"
    ARTILLERY = "artillery"
    FIGHTER = "fighter"
    BOMBER = "bomber"


class Lane(str, Enum):
    FRONTLINE = "frontline"
    SUPPORTLINE = "supportline"


class Zone(str, Enum):
    DECK = "deck"
    HAND = "hand"
    DISCARD = "discard"
    BOARD = "board"
    HQ = "hq"


@dataclass(frozen=True, slots=True)
class BoardPos:
    lane: Lane
    index: int
