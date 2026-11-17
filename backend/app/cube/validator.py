"""Validation functions kept separate from the state data model."""

from app.cube.state import CubeState

valid_faces={'U', 'R', 'F', 'D', 'L', 'B'}
valid_colours={'W', 'R', 'G', 'Y', 'O', 'B'}

def validate_cube(faces: dict[str, list[str]]):

    """
    validate the color input recieved from the fronted.
    This checks the input format and color counts.

    input is something like:
    {'U': ['W','W','W','W']
     'R': ['R','R','R','R']
     'F': ['F','F','F','F']
     'D': ['D','D','D','D']
     'L': ['L','L','L','L']
     'B': ['B','B','B','B']
     }
    """
    if not isinstance(faces, dict):
            return False, ("Faces must be provided as a dictionary.")
    if set(faces.keys())!=valid_faces:
        return False, "Faces must contain exactly U,R, F, D, L, B."


    all_stickers=[]

    for face in valid_faces:
        stickers = faces[face]

        if not isinstance(stickers, list):
            return False, f'Face {face} must contain a list.'

        if len(stickers) != 4:
            return False, f'Face {face} must contain exactly 4 stickers.'

        for colour in stickers:
            if colour not in valid_colours:
                return False, f' Invalid colour {colour} on face {face}.'

        all_stickers.extend(stickers)

    for colour in valid_colours:
        if all_stickers.count(colour) != 4:
            return False, f'Colour {colour} must appear only 4 times.'

    return True, 'cube color input is valid.'

def validate_solvability(cube: CubeState):

    """
    Validate the internal cp/co representation of a 2x2x2 cube.
    """

    if not isinstance(cube, CubeState):
        return False, "Input must be a CubeState object."

    if len(cube.cp) != 8:
        return False, "The cubestate must only have 8 corner positions."

    if sorted(cube.cp) != list(range(8)):
        return False, "Each cube state corner must only appear once"

    if len(cube.co) != 8:
        return False, "The cube must contain exactly 8 corners orientations."

    if any(type(orientation) is not int for orientation in cube.co):
        return False, "Corner orientation must be integers."

    if any(orientation not in (0,1,2) for orientation in cube.co):
        return False, "Corner orientation must be between 0 and 1 or 2."

    if sum(cube.co) % 3 != 0:
        return False, "Corner orientation must be divisible by 3."

    return True, "Cube state is valid and solvable."



