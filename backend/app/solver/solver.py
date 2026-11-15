"""Stable solver facade used by API routes."""

from dataclasses import dataclass
from functools import lru_cache

from app.cube.state import CubeState
from app.solver.search import Algorithms


@dataclass(frozen=True)
class SolveResult:
    """Keep search details behind a small result object."""

    moves: list[str]
    explanation: str
    nodes_expanded: int = 0


@lru_cache(maxsize=1)
def get_algorithms() -> Algorithms:
    """Cache the Algorithms instance so Pattern Databases are built only once."""
    return Algorithms()


def solve(cube: CubeState, constraint: dict[str, object] | None = None) -> SolveResult | None:
    """
    Solve the given CubeState using IDA* with PDB heuristic.

    Args:
        cube: The current CubeState (validated).
        constraint: Optional dictionary with constraints (e.g. max_depth).

    Returns:
        SolveResult if solved, or None if no solution within max_depth.
    """
    if not cube.is_valid():
        raise ValueError("Invalid cube state: impossible permutation or orientation.")

    # 1. Handle already solved state
    if cube.is_solved():
        return SolveResult(
            moves=[],
            explanation="Cube is already in a solved state."
        )

    # 2. Extract constraint parameters (default max_depth = 20 for 2x2)
    max_depth = 20
    if constraint and isinstance(constraint, dict):
        if "max_depth" in constraint:
            max_depth = int(constraint["max_depth"])

    # 3. Run IDA* search
    algorithms = get_algorithms()
    solution = algorithms.IDA_star(cube, max_depth=max_depth)

    # 4. If no solution found
    if solution is None:
        return None

    # 5. Build user-facing explanation
    explanation = (
        f"Cube solved successfully in {len(solution)} moves "
        f"using IDA* with Pattern Database heuristic."
    )

    return SolveResult(
        moves=solution,
        explanation=explanation,
        nodes_expanded=0
    )