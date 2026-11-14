"""Stable solver facade used by API routes."""

from dataclasses import dataclass

from app.cube.moves import apply_move
from app.cube.state import CubeState


@dataclass(frozen=True)
class SolveResult:
    """Keep search details behind a small result object."""

    moves: list[str]
    explanation: str
    nodes_expanded: int = 0


def solve(cube: CubeState, constraint: dict[str, object]) -> SolveResult | None:
    """Choose search settings from parsed constraint data."""
    # TODO: handle solved input, choose a depth, call IDA*, and create an
    # explanation that the frontend can show beside the move sequence.
    raise NotImplementedError

