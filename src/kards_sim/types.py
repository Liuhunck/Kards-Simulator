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


@dataclass(frozen=True, slots=True)
class BoardPos:
    lane: Lane
    index: int
