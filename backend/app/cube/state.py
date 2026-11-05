class CubeState:
    """
    Represents the state of a 2x2x2 Rubik's Cube.

    Corner position IDs:
        0 = URF
        1 = UFL
        2 = ULB
        3 = UBR
        4 = DFR
        5 = DLF
        6 = DBL
        7 = DRB

    cp[i] = corner piece occupying position i
    co[i] = orientation of the corner at position i
    """
    CORNER_NAMES = (
            'URF', 'UFL', 'ULB', 'UBR',
            'DFR', 'DLF', 'DBL', 'DRB'
    )


    def __init__(self, cp=None, co=None):

        # corner permutation : self.co is the single permutation of 8 corners (0 - 7)
        self.cp = (
            cp.copy() if cp is not None
            else list(range(8))
        )

        # corner orientations : each corner will have its own orientations (0 or 1 or 2)
        self.co = (
            co.copy() if co is not None
            else [0] * 8
        )

    def is_solved(self):
        """returns True if the cube is solved else False"""

        return (
            self.cp == list(range(8))
            and self.co == [0] * 8
        )

    def is_valid(self):
        """ valid cube state : state which is achievable from the solved state using valid moves
        returns True if the cube state is valid otherwise False """

        if not isinstance(self.cp, list) or not isinstance(self.co, list):
            return False

    # Check number of corners
        if len(self.cp) != 8 or len(self.co) != 8:
            return False

    # Check that corner permutation contains only integers
    # type(x) is int excludes Boolean values
        if any(type(piece) is not int for piece in self.cp):
            return False

    # Check that every corner appears exactly once
        if sorted(self.cp) != list(range(8)):
            return False

    # Check that orientations contain only integers
        if any(type(orientation) is not int for orientation in self.co):
            return False

    # Every corner orientation must be 0, 1, or 2
        if any(orientation not in (0, 1, 2) for orientation in self.co):
            return False

    # Total corner twist must be divisible by 3
        if sum(self.co) % 3 != 0:
            return False

        return True
    
    def copy(self):
        return CubeState(self.cp, self.co)

    def __repr__(self):
        return f"CubeState(cp={self.cp}, co={self.co})"

    
