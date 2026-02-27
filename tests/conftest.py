from __future__ import annotations

import pytest

from kards_sim.engine import Engine
from kards_sim.resolver import Resolver
from kards_sim.state import GameState, GameConfig
from kards_sim.types import InstanceId, Lane, PlayerId, Zone


@pytest.fixture
def engine() -> Engine:
    return Engine(resolver=Resolver())


def place_on_board(
    state: GameState,
    iid: InstanceId,
    lane: Lane,
    owner: PlayerId | None = None,
    exhausted: bool = False,
) -> None:
    """Put an already-allocated card instance onto the board."""
    ci = state.inst(iid)
    ci.zone = Zone.BOARD
    ci.lane = lane
    ci.exhausted = exhausted
    if owner is None:
        owner = ci.owner
    if lane == Lane.FRONTLINE:
        state.frontline.append(iid)
    elif lane == Lane.SUPPORTLINE:
        state.supportline[owner].append(iid)
