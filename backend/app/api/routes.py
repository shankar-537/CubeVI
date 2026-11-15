
"""HTTP routes: web requests translated into application-service calls."""

from functools import lru_cache

from fastapi import APIRouter, HTTPException

from app.schemas import ScrambleResponse, SolveRequest, SolveResponse
from app.cube.serialization import state_from_faces
from app.solver.search import Algorithms
from app.solver.solver import solve
router = APIRouter()


# Build the solver only once.
# This is important because constructing Algorithms builds both PDBs.
@lru_cache(maxsize=1)
def get_solver():
    return Algorithms()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/scramble", response_model=ScrambleResponse)
def scramble(length: int = 6) -> ScrambleResponse:
    # We'll implement this after the solve endpoint.
    raise HTTPException(
        status_code=501,
        detail="Scramble route is not implemented yet."
    )


@router.post("/solve", response_model=SolveResponse)
def solve_cube(request: SolveRequest) -> SolveResponse:
    """
    Receive face colours, convert them into CubeState,
    run IDA* via the solver facade, and return the solution.
    """
    if request.constraint.strip():
        raise HTTPException(
            status_code=501,
            detail="Move constraints are not supported yet."
        )

    try:
        cube = state_from_faces(request.faces)
    except (ValueError, TypeError) as error:
        raise HTTPException(status_code=400, detail=str(error))

    if not cube.is_valid():
        raise HTTPException(
            status_code=400,
            detail="Invalid cube configuration."
        )

    try:
        result = solve(cube)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    if result is None:
        raise HTTPException(
            status_code=422,
            detail="No solution found within the maximum search depth."
        )

    return SolveResponse(
        valid=True,
        moves=result.moves,
        depth=len(result.moves),
        explanation=result.explanation,
        parsed_constraint={}
    )
