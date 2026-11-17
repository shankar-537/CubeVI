"""Tests for the cube engine: state, moves, scramble, serialization, and validator."""

import pytest

from app.cube.moves import MOVE_TABLES, apply_basic_move, apply_move, apply_moves
from app.cube.scramble import all_moves, generate_scramble
from app.cube.serialization import faces_from_state, state_from_faces
from app.cube.state import CubeState
from app.cube.validator import validate_cube, validate_solvability


def test_solved_cube_is_solved():
    """The canonical solved state must report solved."""
    cube = CubeState.solved()
    assert cube.is_solved()
    assert CubeState().is_solved()
    assert cube.cp == list(range(8))
    assert cube.co == [0] * 8


def test_move_and_inverse_restore_state():
    """A move followed by its inverse must return the original state."""
    base_moves = ["U", "D", "R", "L", "F", "B"]
    for m in base_moves:
        cube = CubeState.solved()
        scrambled = apply_move(cube, m)
        restored = apply_move(scrambled, f"{m}'")
        assert restored == cube, f"Failed restoring with {m}' after {m}"


def test_four_quarter_turns_cycle():
    """Four identical quarter turns on any face must return to the original state."""
    for m in ["U", "D", "R", "L", "F", "B"]:
        cube = CubeState.solved()
        turned = apply_moves(cube, [m] * 4)
        assert turned == cube


def test_double_and_prime_move_equivalences():
    """Verify that U2 == U + U and U' == U + U + U."""
    cube = CubeState.solved()
    for face in ["U", "D", "R", "L", "F", "B"]:
        double_turn = apply_move(cube, f"{face}2")
        two_singles = apply_moves(cube, [face, face])
        assert double_turn == two_singles

        prime_turn = apply_move(cube, f"{face}'")
        three_singles = apply_moves(cube, [face] * 3)
        assert prime_turn == three_singles


def test_invalid_moves():
    """Invalid move inputs should raise appropriate exceptions."""
    cube = CubeState.solved()

    with pytest.raises(TypeError):
        apply_move(cube, 123)

    with pytest.raises(ValueError):
        apply_move(cube, "X")

    with pytest.raises(ValueError):
        apply_move(cube, "U3")

    with pytest.raises(ValueError):
        apply_move(cube, "")

    with pytest.raises(ValueError):
        apply_basic_move(cube, "Z")


def test_cube_state_validity():
    """CubeState.is_valid should properly identify valid and invalid configurations."""
    valid_cube = CubeState.solved()
    assert valid_cube.is_valid()

    # Invalid corner permutation length
    assert not CubeState(cp=[0, 1, 2]).is_valid()

    # Duplicate corner piece
    assert not CubeState(cp=[0, 0, 2, 3, 4, 5, 6, 7]).is_valid()

    # Non-integer in corner permutation
    assert not CubeState(cp=[0, 1, 2, 3, 4, 5, 6, "7"]).is_valid()

    # Invalid corner orientation length
    assert not CubeState(co=[0] * 7).is_valid()

    # Invalid orientation value (not in 0, 1, 2)
    assert not CubeState(co=[3, 0, 0, 0, 0, 0, 0, 0]).is_valid()

    # Total orientation twist not divisible by 3
    assert not CubeState(co=[1, 0, 0, 0, 0, 0, 0, 0]).is_valid()


def test_cube_state_equality_and_hashing():
    """CubeState equality and hashing should work based on cp and co."""
    c1 = CubeState.solved()
    c2 = CubeState.solved()
    c3 = apply_move(c1, "R")

    assert c1 == c2
    assert c1 != c3
    assert c1 != "not_a_cube"
    assert hash(c1) == hash(c2)

    cube_set = {c1, c2, c3}
    assert len(cube_set) == 2


def test_cube_state_copy():
    """Copying a CubeState creates an independent clone."""
    c1 = CubeState.solved()
    c2 = c1.copy()
    assert c1 == c2
    assert c1 is not c2
    assert c1.cp is not c2.cp
    assert c1.co is not c2.co


def test_generate_scramble():
    """generate_scramble produces a valid state and move sequence."""
    state, moves = generate_scramble(length=10)
    assert len(moves) == 10
    assert state.is_valid()

    # Ensure no consecutive moves are on the same face
    for i in range(len(moves) - 1):
        assert moves[i][0] != moves[i + 1][0]

    # Re-executing moves on solved cube should reach the same state
    replayed = apply_moves(CubeState.solved(), moves)
    assert replayed == state

    # Non-positive length raises ValueError
    with pytest.raises(ValueError):
        generate_scramble(length=0)
    with pytest.raises(ValueError):
        generate_scramble(length=-5)


def test_serialization_roundtrip():
    """Serializing to faces and back must restore the exact same CubeState."""
    solved = CubeState.solved()
    faces = faces_from_state(solved)
    recovered = state_from_faces(faces)
    assert recovered == solved

    # Test roundtrip with scrambled cube
    scrambled, moves = generate_scramble(length=12)
    scrambled_faces = faces_from_state(scrambled)
    recovered_scrambled = state_from_faces(scrambled_faces)
    assert recovered_scrambled == scrambled


def test_serialization_validation_errors():
    """state_from_faces raises ValueError on invalid face dictionaries."""
    with pytest.raises(ValueError, match="Faces must be a dictionary"):
        state_from_faces("not a dict")

    with pytest.raises(ValueError, match="Exactly six faces"):
        state_from_faces({"U": ["W"] * 4})

    # Missing face stickers
    valid_faces = faces_from_state(CubeState.solved())
    bad_stickers = {k: list(v) for k, v in valid_faces.items()}
    bad_stickers["U"] = ["W", "W", "W"]
    with pytest.raises(ValueError, match="must contain exactly 4 stickers"):
        state_from_faces(bad_stickers)

    # Invalid colour
    bad_color = {k: list(v) for k, v in valid_faces.items()}
    bad_color["U"] = ["W", "W", "W", "Z"]
    with pytest.raises(ValueError, match="Invalid colour"):
        state_from_faces(bad_color)


def test_validator_functions():
    """validate_cube and validate_solvability return correct booleans and messages."""
    solved = CubeState.solved()
    valid_faces = faces_from_state(solved)

    ok, msg = validate_cube(valid_faces)
    assert ok is True

    ok, msg = validate_cube("not_a_dict")
    assert ok is False

    ok, msg = validate_solvability(solved)
    assert ok is True

    ok, msg = validate_solvability("not_a_cube")
    assert ok is False

    # Solvability fails if orientation twist sum % 3 != 0
    twisted = CubeState(co=[1, 0, 0, 0, 0, 0, 0, 0])
    ok, msg = validate_solvability(twisted)
    assert ok is False
