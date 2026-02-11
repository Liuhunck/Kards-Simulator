from __future__ import annotations

from .registry import CardRegistry
from .bases.headquarters import Headquarters
from .units.bomber import Bomber
from .units.artillery import FieldGun
from .units.fighter import Fighter
from .units.infantry import Infantry, RadioTeam
from .units.tank import LightTank
from .orders.artillery_strike import ArtilleryStrike
from .countermeasures.sample_countermeasure import SampleCountermeasure


def sample_card_registry() -> CardRegistry:
    reg = CardRegistry()
    reg.register_many(
        [
            Headquarters,
            Infantry,
            RadioTeam,
            LightTank,
            FieldGun,
            Fighter,
            Bomber,
            ArtilleryStrike,
            SampleCountermeasure,
        ]
    )
    return reg
