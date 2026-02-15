from __future__ import annotations

from .base import CardBase
from .bases import (
    BritainHeadquarters,
    GermanyHeadquarters,
    JapanHeadquarters,
    SovietHeadquarters,
    UsaHeadquarters,
)
from .units.bomber import Bomber
from .units.artillery import FieldGun
from .units.fighter import Fighter
from .units.infantry import Infantry, RadioTeam, Regiment1, Regiment432
from .units.tank import LightTank, Tank35T
from .orders.artillery_strike import ArtilleryStrike
from .countermeasures.sample_countermeasure import SampleCountermeasure


def sample_card_classes() -> list[type[CardBase]]:
    return [
        GermanyHeadquarters,
        SovietHeadquarters,
        UsaHeadquarters,
        BritainHeadquarters,
        JapanHeadquarters,
        Infantry,
        Regiment1,
        Regiment432,
        RadioTeam,
        LightTank,
        Tank35T,
        FieldGun,
        Fighter,
        Bomber,
        ArtilleryStrike,
        SampleCountermeasure,
    ]
