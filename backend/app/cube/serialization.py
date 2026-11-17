
from app.cube.state import CubeState


# Facelet indices follow the frontend order:
# U: 0-3, R: 4-7, F: 8-11,
# D: 12-15, L: 16-19, B: 20-23.
#
# Each face is read row by row:
# 0 1
# 2 3

# The order of faces in each corner is important.
# It follows the same corner orientation convention
# used by the backend MOVE_TABLES.

CORNER_FACELETS = [
    # URF
    [('U', 3), ('R', 0), ('F', 1)],

    # UFL
    [('U', 2), ('F', 0), ('L', 1)],

    # ULB
    [('U', 0), ('L', 0), ('B', 1)],

    # UBR
    [('U', 1), ('B', 0), ('R', 1)],

    # DFR
    [('D', 1), ('F', 3), ('R', 2)],

    # DLF
    [('D', 0), ('L', 3), ('F', 2)],

    # DBL
    [('D', 2), ('B', 3), ('L', 2)],

    # DRB
    [('D', 3), ('R', 3), ('B', 2)],
]


# Colour arrangement of each solved corner.
# The order corresponds to CubeState.CORNER_NAMES.

CORNER_COLORS = [
    ('W', 'R', 'G'),  # URF
    ('W', 'G', 'O'),  # UFL
    ('W', 'O', 'B'),  # ULB
    ('W', 'B', 'R'),  # UBR
    ('Y', 'G', 'R'),  # DFR
    ('Y', 'O', 'G'),  # DLF
    ('Y', 'B', 'O'),  # DBL
    ('Y', 'R', 'B'),  # DRB
]


VALID_COLORS = {'W', 'R', 'G', 'B', 'Y', 'O'}

CORNER_LOOKUP = {
    frozenset(colors): piece_id
    for piece_id, colors in enumerate(CORNER_COLORS)
}


def validate_faces(faces):
    """Validate the six input faces and their sticker colours."""

    required_faces = {'U', 'R', 'F', 'D', 'L', 'B'}

    if not isinstance(faces, dict):
        raise ValueError("Faces must be a dictionary.")

    if set(faces.keys()) != required_faces:
        raise ValueError("Exactly six faces U, R, F, D, L, B are required.")

    for face in required_faces:
        stickers = faces[face]

        if not isinstance(stickers, list) or len(stickers) != 4:
            raise ValueError(f"Face {face} must contain exactly 4 stickers.")

        for color in stickers:
            if color not in VALID_COLORS:
                raise ValueError(f"Invalid colour {color} on face {face}.")

    all_colors = [
        color
        for face in required_faces
        for color in faces[face]
    ]

    for color in VALID_COLORS:
        if all_colors.count(color) != 4:
            raise ValueError(
                f"Colour {color} must appear exactly 4 times."
            )


def state_from_faces(faces):
    """
    Convert six face arrays into CubeState(cp, co).

    cp[position] = corner piece occupying that position
    co[position] = orientation of that corner
    """

    validate_faces(faces)

    cp = [-1] * 8
    co = [-1] * 8

    for position in range(8):

        # Read the three stickers belonging to this position.
        current_colors = tuple(
            faces[face][index]
            for face, index in CORNER_FACELETS[position]
        )

        # Identify which original corner piece occupies this position.
        piece_id = CORNER_LOOKUP.get(frozenset(current_colors))

        if piece_id is None:
            raise ValueError(
                f"Invalid corner at position {position}: {current_colors}"
            )

        cp[position] = piece_id

        # Find the position of the white/yellow sticker.
        orientation = next(
            (
                i for i, color in enumerate(current_colors)
                if color in ('W', 'Y')
            ),
            None
        )

        if orientation is None:
            raise ValueError(
                f"Corner at position {position} has no W/Y sticker."
            )

        # Check that the other two stickers have the correct cyclic order.
        original_colors = CORNER_COLORS[piece_id]

        expected_colors = tuple(
            original_colors[(i - orientation) % 3]
            for i in range(3)
        )

        if current_colors != expected_colors:
            raise ValueError(
                f"Incorrect colour order at corner {position}."
            )

        co[position] = orientation

    state = CubeState(cp, co)

    if not state.is_valid():
        raise ValueError(
            "Invalid cube: corner permutation or orientation is impossible."
        )

    return state


def faces_from_state(state):
    """
    Convert CubeState(cp, co) back into six face arrays.

    Useful for scrambles, testing and frontend communication.
    """

    if not state.is_valid():
        raise ValueError("Cannot serialize an invalid cube state.")

    faces = {
        face: [None] * 4
        for face in ('U', 'R', 'F', 'D', 'L', 'B')
    }

    for position in range(8):

        piece_id = state.cp[position]
        orientation = state.co[position]

        original_colors = CORNER_COLORS[piece_id]

        current_colors = [
            original_colors[(i - orientation) % 3]
            for i in range(3)
        ]

        for i, (face, index) in enumerate(
            CORNER_FACELETS[position]
        ):
            faces[face][index] = current_colors[i]

    return faces
