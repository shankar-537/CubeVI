from .state import CubeState

"""
Corner positions:
0 = URF, 1 = UFL, 2 = ULB, 3 = UBR
4 = DFR, 5 = DLF, 6 = DBL, 7 = DRB

permutation list and co_delta list are used in the apply_basic_move function.

permutation list tells us which OLD position supplies the corner for each NEW position.
co_delta[i] is the orientation change at NEW position i. 
""" 


MOVE_TABLES = {
    "U": (
        [3, 0, 1, 2, 4, 5, 6, 7],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ),
    "D": (
        [0, 1, 2, 3, 5, 6, 7, 4],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ),
    "R": (
        [4, 1, 2, 0, 7, 5, 6, 3],
        [2, 0, 0, 1, 1, 0, 0, 2],
    ),
    "L": (
        [0, 2, 6, 3, 4, 1, 5, 7],
        [0, 1, 2, 0, 0, 2, 1, 0],
    ),
    "F": (
        [1, 5, 2, 3, 0, 4, 6, 7],
        [1, 2, 0, 0, 2, 1, 0, 0],
    ),
    "B": (
        [0, 1, 3, 7, 4, 5, 2, 6],
        [0, 0, 1, 2, 0, 0, 2, 1],
    ),
}

def apply_basic_move(state: CubeState, basic_move: str) -> CubeState:

    """ 
    Apply one clockwise quarter-turn: U, D, R, L, F, or B.

    Returns a NEW CubeState without modifying the original. 
    """

    if basic_move not in MOVE_TABLES:
        raise ValueError(f'{basic_move} is an invalid move.')

    permutation, co_delta = MOVE_TABLES[basic_move]

    # new corner permutation:
    new_cp = [state.cp[permutation[i]] for i in range(len(permutation))]

    # new corner orientation:
    new_co = [
        (state.co[permutation[i]] + co_delta[i]) % 3 
         for i in range(len(co_delta))
    ]

    return CubeState(new_cp, new_co)

def apply_move(state: CubeState, move: str) -> CubeState:
    """
    Supported moves:
        U, D, R, L, F, B
        U', D', R', L', F', B',
        U2, D2, R2, L2, F2, B2

    rest all strings are considered as invalid inputs
    this function takes a move and a state,
    checks weather the move is valid move if valid then calculate the new CubeState and returns a new 
    CubeState otherwise throws an error.
    """

    if not isinstance(move, str):
        raise TypeError(f'Move must be a string.')

    move = move.strip()

    if len(move) not in [1, 2]:
        raise ValueError(f'Invalid move.')

    basic_move = move[0]

    suffix = move[1:]

    if suffix not in ["", "'", "2"]:
        raise ValueError(f'Invalid move.')

    # A normal move = one quarter-turn.
    # An inverse move = three clockwise quarter-turns.
    # A double move = two quarter-turns.

    # defining a variable 'turns' which represents number of turns
    turns = {
        "" : 1,
        "'" : 3,
        "2" : 2
    }[suffix]

    result = state.copy()

    for _ in range(turns):
        result = apply_basic_move(result, basic_move)

    return result


def apply_moves(state: CubeState, moves: list) -> CubeState:
    """
    Apply a sequence of moves.

    Example:
        apply_moves(state, ["R", "U", "R'", "U'"])
    """

    result = state.copy()

    for move in moves:
        result = apply_move(result, move)

    return result