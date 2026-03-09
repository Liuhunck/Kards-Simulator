from .base import CardBase
from .unit import UnitCard
from .order import OrderCard
from .countermeasure import CountermeasureCard
from .headquarters import HeadquartersCard

from .germany import Bf109E, Blackout, CoordinatedOps, EagleClaw, Flak88, GermanyHeadquarters, PantherG, PanzerIIA, PanzerIIIL, Regiment1, Regiment432, Regiment980, Tank35T, Tank38T, StugIIIF
from .soviet import SovietHeadquarters
from .usa import UsaHeadquarters
from .britain import BritainHeadquarters
from .japan import JapanHeadquarters
from .italy import FiatCR42, FiatG50, M1340, SavoiaCavalry
from .neutral import (
    Infantry,
    RadioTeam,
    LightTank,
    FieldGun,
    Fighter,
    Bomber,
    ArtilleryStrike,
    SampleCountermeasure,
)


ALL_CARD_CLASSES: list[type[CardBase]] = [
    GermanyHeadquarters,
    SovietHeadquarters,
    UsaHeadquarters,
    BritainHeadquarters,
    JapanHeadquarters,
    Infantry,
    Regiment1,
    Regiment432,
    Regiment980,
    EagleClaw,
    Blackout,
    CoordinatedOps,
    RadioTeam,
    LightTank,
    Tank35T,
    StugIIIF,
    Tank38T,
    Bf109E,
    PanzerIIIL,
    Flak88,
    PantherG,
    PanzerIIA,
    FieldGun,
    Fighter,
    Bomber,
    ArtilleryStrike,
    SampleCountermeasure,
    FiatCR42,
    SavoiaCavalry,
    FiatG50,
    M1340,
]


__all__ = [
    "CardBase",
    "UnitCard",
    "OrderCard",
    "CountermeasureCard",
    "HeadquartersCard",
    "ALL_CARD_CLASSES",
    # Germany
    "GermanyHeadquarters",
    "Regiment1",
    "Regiment432",
    "Regiment980",
    "EagleClaw",
    "Blackout",
    "CoordinatedOps",
    "Tank35T",
    "StugIIIF",
    "Tank38T",
    "Bf109E",
    "PanzerIIIL",
    "Flak88",
    "PantherG",
    "PanzerIIA",
    # Soviet
    "SovietHeadquarters",
    # USA
    "UsaHeadquarters",
    # Britain
    "BritainHeadquarters",
    # Japan
    "JapanHeadquarters",
    # Italy
    "FiatCR42",
    "SavoiaCavalry",
    "FiatG50",
    "M1340",
    # Neutral
    "Infantry",
    "RadioTeam",
    "LightTank",
    "FieldGun",
    "Fighter",
    "Bomber",
    "ArtilleryStrike",
    "SampleCountermeasure",
]
