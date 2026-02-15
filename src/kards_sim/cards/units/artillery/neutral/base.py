from __future__ import annotations

from .....types import Nation
from ..base import ArtilleryBase


class NeutralArtilleryBase(ArtilleryBase):
    nation = Nation.NEUTRAL
