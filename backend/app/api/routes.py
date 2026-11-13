
"""HTTP routes: web requests translated into application-service calls."""

from functools import lru_cache

from fastapi import APIRouter, HTTPException

from app.schemas import ScrambleResponse, SolveRequest, SolveResponse
from app.cube.serialization import state_from_faces
from app.solver.search import Algorithms

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
    run IDA*, and return the solution.
    """

    # Constraint parsing is not implemented yet.
    if request.constraint.strip():
        raise HTTPException(
            status_code=501,
            detail="Move constraints are not supported yet."
        )

    # Step 1: Convert sticker colours into CubeState.
    try:
        cube = state_from_faces(request.faces)

    except (ValueError, TypeError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    # Step 2: Check that the cube is valid.
    if not cube.is_valid():
        raise HTTPException(
            status_code=400,
            detail="Invalid cube configuration."
        )

    # Step 3: Run the existing IDA* algorithm.
    try:
        solver = get_solver()
        solution = solver.IDA_star(cube)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    # Step 4: Check whether a solution was found.
    if solution is None:
        raise HTTPException(
            status_code=422,
            detail="No solution found within the maximum search depth."
        )

    # Step 5: Return the solution.
    return SolveResponse(
        valid=True,
        moves=solution,
        depth=len(solution),
        explanation=(
            "Cube solved successfully using IDA* "
            "with Pattern Database heuristics."
        ),
        parsed_constraint={}
    )
