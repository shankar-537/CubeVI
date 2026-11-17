"""Tests for the solver engine: pattern databases, search algorithms, and solver facade."""

import pytest

from app.cube.moves import apply_move, apply_moves
from app.cube.state import CubeState
from app.solver.heuristics import CornerPatternDatabase
from app.solver.search import Algorithms
from app.solver.solver import SolveResult, get_algorithms, solve


def test_solved_cube_solve():
    """Solving an already solved cube should return an empty move list immediately."""
    solved = CubeState.solved()
    result = solve(solved)
    assert isinstance(result, SolveResult)
    assert result.moves == []
    assert "already in a solved state" in result.explanation


def test_one_move_scramble_is_solved():
    """The solver should reverse any single-move scramble."""
    for move in ["R", "U", "F", "D", "L", "B"]:
        scrambled = apply_move(CubeState.solved(), move)
        result = solve(scrambled)
        assert result is not None
        assert len(result.moves) == 1

        restored = apply_moves(scrambled, result.moves)
        assert restored.is_solved(), f"Failed to restore after single move {move}"


def test_two_move_scramble_is_solved():
    """The solver should find a valid solution for two-move scrambles."""
    scramble_moves = ["R", "U"]
    scrambled = apply_moves(CubeState.solved(), scramble_moves)
    result = solve(scrambled)

    assert result is not None
    assert len(result.moves) == 2
    restored = apply_moves(scrambled, result.moves)
    assert restored.is_solved()


def test_three_move_scramble_is_solved():
    """The solver should find a valid solution for a 3-move scramble."""
    scramble_moves = ["R", "U", "R'"]
    scrambled = apply_moves(CubeState.solved(), scramble_moves)
    result = solve(scrambled)

    assert result is not None
    restored = apply_moves(scrambled, result.moves)
    assert restored.is_solved()


def test_solver_invalid_cube():
    """The solver facade should raise ValueError when passed an invalid cube."""
    invalid_cube = CubeState(co=[1, 0, 0, 0, 0, 0, 0, 0])
    with pytest.raises(ValueError, match="Invalid cube state"):
        solve(invalid_cube)


def test_solver_max_depth_constraint():
    """If the scramble requires more moves than max_depth, solve returns None."""
    scramble_moves = ["R", "U", "R'", "U'"]
    scrambled = apply_moves(CubeState.solved(), scramble_moves)

    # Scramble requires multiple moves; limiting max_depth to 1 should yield no solution
    result = solve(scrambled, constraint={"max_depth": 1})
    assert result is None


def test_corner_pattern_database():
    """CornerPatternDatabase should correctly initialize and return admissible heuristics."""
    pdb = get_algorithms().pdb1
    solved = CubeState.solved()
    assert pdb.heuristic(solved) == 0

    scrambled = apply_move(solved, "R")
    h = pdb.heuristic(scrambled)
    assert h >= 0
    assert h <= 1

    # Invalid pattern pieces configuration
    with pytest.raises(ValueError, match="Select exactly 4"):
        CornerPatternDatabase(pattern_pieces=(0, 1, 2))

    with pytest.raises(ValueError, match="distinct"):
        CornerPatternDatabase(pattern_pieces=(0, 1, 2, 2))

    with pytest.raises(ValueError, match="between 0 & 7"):
        CornerPatternDatabase(pattern_pieces=(0, 1, 2, 8))


def test_algorithms_bfs():
    """Algorithms.breadth_first_search should find shortest path on shallow states."""
    algorithms = get_algorithms()
    solved = CubeState.solved()

    assert algorithms.breadth_first_search(solved) == []

    scrambled = apply_moves(solved, ["F", "U"])
    solution = algorithms.breadth_first_search(scrambled)
    assert solution is not None
    assert len(solution) == 2

    restored = apply_moves(scrambled, solution)
    assert restored.is_solved()

    invalid_cube = CubeState(cp=[0, 0, 2, 3, 4, 5, 6, 7])
    with pytest.raises(ValueError):
        algorithms.breadth_first_search(invalid_cube)


def test_algorithms_ida_star():
    """Algorithms.IDA_star should solve cubes and validate against invalid input."""
    algorithms = get_algorithms()
    solved = CubeState.solved()

    assert algorithms.IDA_star(solved) == []

    scrambled = apply_moves(solved, ["U", "R", "U'"])
    solution = algorithms.IDA_star(scrambled)
    assert solution is not None
    restored = apply_moves(scrambled, solution)
    assert restored.is_solved()

    invalid_cube = CubeState(co=[2, 0, 0, 0, 0, 0, 0, 0])
    with pytest.raises(ValueError):
        algorithms.IDA_star(invalid_cube)


def test_pdb_disk_loading_and_dump(tmp_path):
    """CornerPatternDatabase should load from pre-computed disk files and support dumping."""
    # 1. Existing database should have loaded 136,080 states from disk
    pdb = get_algorithms().pdb1
    assert len(pdb.distances) == 136080
    assert pdb.heuristic(CubeState.solved()) == 0

    # 2. Test dumping to a custom file and reloading
    temp_pdb_file = tmp_path / "test_pdb.pickle"
    pdb.dump(temp_pdb_file)
    assert temp_pdb_file.exists()

    reloaded = CornerPatternDatabase.from_file(temp_pdb_file, pattern_pieces=(0, 1, 2, 3))
    assert len(reloaded.distances) == 136080
    assert reloaded.heuristic(CubeState.solved()) == 0


def test_pdb_fallback_when_file_not_found(tmp_path):
    """When autoload=False or nonexistent path without precomputed pieces, it gracefully handles."""
    nonexistent = tmp_path / "nonexistent.pickle"
    # When initialized with custom missing path, it should fallback without crashing
    # using autoload=False to test pure in-memory or fallback behavior
    pdb = CornerPatternDatabase(pattern_pieces=(0, 1, 2, 3), db_path=nonexistent, autoload=True)
    assert len(pdb.distances) == 136080
