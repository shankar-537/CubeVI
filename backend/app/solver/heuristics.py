"""Heuristic functions for informed search."""

from collections import deque
from app.cube.state import CubeState
from app.cube.moves import MOVE_TABLES


class CornerPatternDatabase:
    """
    Pattern Database for four selected corner pieces. 

    Abstract state : function that takes a state and returns "positions" and "orientations" for the pattern_pieces
        positions[i]   = position of tracked piece i
        orientations[i] = orientation of that piece
    """


    def __init__(self, pattern_pieces=(0, 1, 2, 3)):
        self.pattern_pieces = tuple(pattern_pieces)

        if len(self.pattern_pieces) != 4:
            raise ValueError("Select exactly 4 corner pieces.")

        if len(set(self.pattern_pieces)) != 4:
            raise ValueError("Pattern piese must be distinct")

        if any(p not in range(8) for p in self.pattern_pieces):
            raise ValueError("Pieses must be between 0 & 7.")
        
        self.distances = {}
        self._build_database()


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
