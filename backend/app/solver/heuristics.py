"""Heuristic functions for informed search."""

from collections import deque
import logging
import os
from pathlib import Path
import pickle
import time

from app.cube.state import CubeState
from app.cube.moves import MOVE_TABLES

logger = logging.getLogger("cubevi.heuristics")

DEFAULT_PDB_FILENAME = "pdb.pickle"
DEFAULT_PDB_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_PDB_PATH = DEFAULT_PDB_DIR / DEFAULT_PDB_FILENAME

# In-memory cache mapping filepath (str) -> dict[pattern_pieces, distances_dict]
_LOADED_PDB_CACHE: dict[str, dict] = {}


def resolve_pdb_path(custom_path: str | Path | None = None) -> Path | None:
    """Resolve the path to the pre-computed PDB file.

    Checks:
    1. custom_path argument if provided
    2. PDB_PATH environment variable
    3. Default data directory: app/solver/data/pdb.pickle
    4. Solver module directory: app/solver/pdb.pickle
    5. Current working directory: ./pdb.pickle
    6. Relative backend candidate directories
    """
    if custom_path:
        p = Path(custom_path)
        if p.exists() and p.is_file():
            return p.resolve()

    env_path = os.getenv("PDB_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists() and p.is_file():
            return p.resolve()

    candidates = [
        DEFAULT_PDB_PATH,
        Path(__file__).resolve().parent / DEFAULT_PDB_FILENAME,
        Path.cwd() / DEFAULT_PDB_FILENAME,
        Path.cwd() / "data" / DEFAULT_PDB_FILENAME,
        Path.cwd() / "backend" / "app" / "solver" / "data" / DEFAULT_PDB_FILENAME,
        Path.cwd() / "backend" / "app" / "solver" / DEFAULT_PDB_FILENAME,
        Path.cwd() / "app" / "solver" / "data" / DEFAULT_PDB_FILENAME,
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()

    return None


def load_pdb_file(db_path: str | Path | None = None) -> dict:
    """Load and cache pre-computed pattern databases from disk.

    Supports files formatted as:
    - dict keyed by pattern_pieces tuple: e.g. {(0,1,2,3): dists, (4,5,6,7): dists}
    - dict with aliases: e.g. {'pdb1': dists, 'pdb2': dists}
    - single CornerPatternDatabase object or raw distances dict
    """
    resolved = resolve_pdb_path(db_path)
    if not resolved:
        return {}

    cache_key = str(resolved)
    if cache_key in _LOADED_PDB_CACHE:
        return _LOADED_PDB_CACHE[cache_key]

    logger.info(f"Loading pre-computed PDB from {resolved}...")
    try:
        with open(resolved, "rb") as f:
            data = pickle.load(f)
    except Exception as exc:
        logger.warning(f"Failed to load PDB from {resolved}: {exc}")
        return {}

    normalized: dict = {}
    if isinstance(data, dict):
        for k, v in data.items():
            if k == "pdb1":
                normalized[(0, 1, 2, 3)] = v
            elif k == "pdb2":
                normalized[(4, 5, 6, 7)] = v
            elif isinstance(k, tuple):
                normalized[tuple(k)] = v
            normalized[k] = v
    elif hasattr(data, "pattern_pieces") and hasattr(data, "distances"):
        normalized[tuple(data.pattern_pieces)] = data.distances

    _LOADED_PDB_CACHE[cache_key] = normalized
    return normalized


def load_precomputed_distances(
    pattern_pieces: tuple[int, ...],
    db_path: str | Path | None = None,
) -> dict | None:
    """Retrieve pre-computed distances for the given pattern pieces if available."""
    cache = load_pdb_file(db_path)
    pieces_tuple = tuple(pattern_pieces)

    if pieces_tuple in cache:
        return cache[pieces_tuple]

    # Check common aliases
    if pieces_tuple == (0, 1, 2, 3) and "pdb1" in cache:
        return cache["pdb1"]
    if pieces_tuple == (4, 5, 6, 7) and "pdb2" in cache:
        return cache["pdb2"]

    return None


def dump_pdb_file(
    filepath: str | Path,
    databases: dict,
) -> Path:
    """Dump pattern databases to disk using pickle HIGHEST_PROTOCOL."""
    out_path = Path(filepath)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "wb") as f:
        pickle.dump(databases, f, protocol=pickle.HIGHEST_PROTOCOL)

    _LOADED_PDB_CACHE[str(out_path.resolve())] = databases
    return out_path.resolve()


class CornerPatternDatabase:
    """
    Pattern Database for four selected corner pieces. 

    Abstract state : function that takes a state and returns "positions" and "orientations" for the pattern_pieces
        positions[i]   = position of tracked piece i
        orientations[i] = orientation of that piece
    """


    def __init__(
        self,
        pattern_pieces=(0, 1, 2, 3),
        distances: dict | None = None,
        db_path: str | Path | None = None,
        autoload: bool = True,
    ):
        self.pattern_pieces = tuple(pattern_pieces)

        if len(self.pattern_pieces) != 4:
            raise ValueError("Select exactly 4 corner pieces.")

        if len(set(self.pattern_pieces)) != 4:
            raise ValueError("Pattern piese must be distinct")

        if any(p not in range(8) for p in self.pattern_pieces):
            raise ValueError("Pieses must be between 0 & 7.")

        if distances is not None:
            self.distances = distances
            return

        self.distances = {}
        if autoload:
            precomputed = load_precomputed_distances(self.pattern_pieces, db_path=db_path)
            if precomputed is not None:
                self.distances = precomputed
                return

        self._build_database()

    def dump(self, filepath: str | Path) -> Path:
        """Dump this database instance to disk."""
        out_path = Path(filepath)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            pickle.dump({self.pattern_pieces: self.distances}, f, protocol=pickle.HIGHEST_PROTOCOL)
        return out_path.resolve()

    @classmethod
    def from_file(cls, filepath: str | Path, pattern_pieces=(0, 1, 2, 3)):
        """Load a database from a specific file."""
        return cls(pattern_pieces=pattern_pieces, db_path=filepath, autoload=True)



    def _abstract_state(self, state: CubeState):

        positions = tuple(
            state.cp.index(piece) 
            for piece in self.pattern_pieces
        )

        orientations = tuple(
            state.co[state.cp.index(piece)]
            for piece in self.pattern_pieces
        )

        return positions, orientations
            
    @staticmethod
    def _apply_quarter_turn(abstract_state, move):
        
        positions, orientations = abstract_state
        permutation, co_delta = MOVE_TABLES[move]

        new_abstract_positions = [permutation.index(old_pos) for old_pos in positions]

        new_abstract_orientations = [
            (orientation + co_delta[new_position]) % 3
            for orientation, new_position in zip(
                orientations, new_abstract_positions
            )
        ]

        return tuple(new_abstract_positions), tuple(new_abstract_orientations)


    @classmethod
    def _apply_abstract_move(cls, abstract_state, move: str):
        """
        Apply one of the 18 standard moves:
            U, U', U2, D, D', D2, R, R', R2,
            L, L', L2, F, F', F2, B, B', B2.

        Each complete move counts as one step.
        """

        move = move.strip()
        if not move:
            raise ValueError("Move cannot be empty.")

        base_move = move[0]
        suffix = move[1:]

        if base_move not in MOVE_TABLES:
            raise ValueError(f"Invalid base move: {base_move}")

        if suffix == "" : repetitions = 1
        elif suffix == "'" : repetitions = 3
        elif suffix == "2" : repetitions = 2
        else : raise ValueError("Invalid move notation.")

        for _ in range(repetitions):
            abstract_state = cls._apply_quarter_turn(
                abstract_state, base_move
            )

        return abstract_state
            

    def _build_database(self):

        solved_state = CubeState()
        start_state = self._abstract_state(solved_state)

        self.distances[start_state] = 0
        queue = deque([start_state])

        moves = [
            "U", "U'", "U2",
            "D", "D'", "D2",
            "R", "R'", "R2",
            "L", "L'", "L2",
            "F", "F'", "F2",
            "B", "B'", "B2",
        ]


        while queue:
            current_state = queue.popleft()
            next_distance = self.distances[current_state] + 1

            for move in moves:
                neighbor = self._apply_abstract_move(current_state, move)

                if neighbor not in self.distances:
                    self.distances[neighbor] = next_distance
                    queue.append(neighbor)

    def heuristic(self, state):
        abstract_state = self._abstract_state(state)

        if abstract_state not in self.distances:
            raise ValueError(
                "pattern state not found, Check MOVE_TABELS and cube orientation convention"
            )

        return self.distances[abstract_state]


if __name__ == "__main__":
    from app.solver.build_pdb import main
    main()
