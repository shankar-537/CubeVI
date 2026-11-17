"""Pydantic contracts at the frontend-backend boundary.

Defines data validation models and schemas for request payloads and response
structures exchanged between the React frontend and FastAPI backend.
"""

from typing import Literal

from pydantic import BaseModel, Field

FaceName = Literal["U", "R", "F", "D", "L", "B"]


class HealthResponse(BaseModel):
    """Response returned by the health check endpoint."""

    status: str = Field(default="ok", description="Server health status")


class SolveRequest(BaseModel):
    """JSON payload sent by the React cube input form."""

    faces: dict[FaceName, list[str]] = Field(
        ...,
        description="Dictionary mapping each face (U, R, F, D, L, B) to 4 sticker colour codes ('W', 'R', 'G', 'Y', 'O', 'B')",
        examples=[
            {
                "U": ["W", "W", "W", "W"],
                "R": ["R", "R", "R", "R"],
                "F": ["G", "G", "G", "G"],
                "D": ["Y", "Y", "Y", "Y"],
                "L": ["O", "O", "O", "O"],
                "B": ["B", "B", "B", "B"],
            }
        ],
    )
    constraint: str = Field(
        default="",
        description="Optional natural-language constraint (e.g., 'under 7 moves', 'no F moves')",
    )


class SolveResponse(BaseModel):
    """JSON payload returned after a solution search is performed."""

    valid: bool = Field(..., description="Whether the cube state was valid and solvable")
    moves: list[str] = Field(
        ...,
        description="Sequence of standard Rubik's cube moves (e.g. ['R', 'U', 'R\'']) to solve the cube",
    )
    depth: int = Field(..., description="Total number of moves in the solution sequence")
    explanation: str = Field(
        ...,
        description="Human-readable explanation of how the solution was found",
    )
    parsed_constraint: dict[str, object] = Field(
        default_factory=dict,
        description="Structured representation of any natural-language constraint applied",
    )


class ScrambleResponse(BaseModel):
    """JSON payload returned by the demo scramble route."""

    scramble: list[str] = Field(
        ...,
        description="Sequence of random moves applied to generate the scramble",
    )
    faces: dict[str, list[str]] = Field(
        ...,
        description="Resulting 6-face sticker dictionary after applying scramble moves",
    )
