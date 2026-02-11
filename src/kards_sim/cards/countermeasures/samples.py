from __future__ import annotations

from ..definitions import CardDefinition
from ..countermeasures.base import CountermeasureCardBase
from ...types import CardType


class SampleCountermeasure(CountermeasureCardBase):
    definition = CardDefinition(
        def_id="CM_SAMPLE",
        name="Countermeasure (Sample)",
        card_type=CardType.COUNTERMEASURE,
        cost=1,
        abilities=(),
    )
