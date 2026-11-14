from collections import deque
from app.cube.state import CubeState
from app.cube.moves import apply_move
from app.solver.heuristics import CornerPatternDatabase

# BFS solution :
class Algorithms:

    def __init__(self):
        # All 18 standard moves
        self.moves = [
            "U", "U'", "U2",
            "D", "D'", "D2",
            "R", "R'", "R2",
            "L", "L'", "L2",
            "F", "F'", "F2",
            "B", "B'", "B2",
        ]

        self.pdb1 = CornerPatternDatabase(
            pattern_pieces=(0, 1, 2, 3)
        )

        self.pdb2 = CornerPatternDatabase(
            pattern_pieces=(4, 5, 6, 7)
        )


    @staticmethod
    def state_key(state: CubeState):
        """creating a hashable key for a cube state"""
        return (tuple(state.cp), tuple(state.co))

    @staticmethod
    def reconstruct_path(parent, current_key):
        """Reconstruct the solution by following parent records."""
        path = []

        while parent[current_key] is not None:
            previous_key, move = parent[current_key]
            path.append(move)
            current_key = previous_key

        path.reverse()
        return path

    # BFS algorithm : 
    def breadth_first_search(self, start_state: CubeState):
        """
        Find a shortest solution using BFS.

        Returns a list of moves if a solution is found,
        or None if no solution is found.
        """

        if not start_state.is_valid():
            raise ValueError("The start state of the cube is invalid")

        if start_state.is_solved():
            return []

        start_key = self.state_key(start_state)

        queue = deque([start_state])
        visited = {start_key}

        # Maps each discovered state to (previous state key, move).
        # The initial state has no parent.
        parent = {
            start_key : None
        }

        while queue:
            current_state = queue.popleft()
            current_key = self.state_key(current_state)

            for move in self.moves:
                next_state = apply_move(current_state, move)
                next_key = self.state_key(next_state)

                if next_key in visited:
                    continue

                visited.add(next_key)
                parent[next_key] = (current_key, move)

                if next_state.is_solved():
                    return self.reconstruct_path(parent, next_key)

                queue.append(next_state)

        return None
    
    # DFS algorithm :
    def depth_first_search(self, start_state: CubeState, max_depth: int = 7):

        if not start_state.is_valid():
            raise ValueError('The start state of the cube is invalid')

        if start_state.is_solved():
            return []

        path = []
        start_key = self.state_key(start_state)
        path_key = {start_key}
        found = self._dfs(start_state, 0, max_depth, path, path_key)

        if found :
            return path

        return None

    # DFS helper function :
    def _dfs(self, curr_state: CubeState, depth: int, max_depth: int, path: list, path_key: set):

        if curr_state.is_solved():
            return True

        # if the depth is greather than max_depth to prevent overflow terminate the search for that branch
        if max_depth <= depth: return False

        # Explore each possible move :
        for move in self.moves:
            next_state = apply_move(curr_state, move)
            next_key = self.state_key(next_state)

            # Avoid revisiting a state in the current path
            if next_key in path_key:
                continue

            
            path.append(move)
            path_key.add(next_key)

            # Recursively call the _dfs() function.
            if self._dfs(next_state, depth+1, max_depth, path, path_key):
                return True

            # backtracking 
            path.pop()
            path_key.remove(next_key)

        return False


    def iterative_deepening_search(self, start_state: CubeState, max_depth: int = 7):

        if not start_state.is_valid():
            raise ValueError("Start state is invalid")

        if start_state.is_solved():
            return []

        start_key = self.state_key(start_state)

        for level in range(max_depth + 1):
            path = []
            path_key = {start_key}

            found = self._dfs(start_state, 0, level, path, path_key)

            if found:
                return path

        return None

    def IDA_star(self, initial_state: CubeState, max_depth = 20):
        """
        Solve the cube using IDA*.

        Returns:
            List of moves if solved.
            None if no solution is found within max_depth.
        """

        if not initial_state.is_valid():
            raise ValueError("Invalid start state.")

        if initial_state.is_solved():
            return []
        
        initial_key = self.state_key(initial_state)
        path = []
        path_key = {initial_key}
        
        bound = max(self.pdb1.heuristic(initial_state), self.pdb2.heuristic(initial_state))

        while bound <= max_depth:

            result = self._ida_search(
                initial_state,
                0,
                bound,
                None,
                path,
                path_key
            )

            if result is True:
                return path

            if result == float("inf"):
                return None

            bound = result

        return None

    
    def _ida_search(self, current_state: CubeState, g, bound, previous_move, path: list, path_key: set):

        h = max(self.pdb1.heuristic(current_state), self.pdb2.heuristic(current_state))
        f = g + h

        # Exceeded the current threshold.
        if f > bound:
            return f

        # Goal test.
        if current_state.is_solved():
            return True 

        minimum_excess = float("inf")

        for move in self.moves:

            # Skip consecutive moves of the same face.
            if previous_move is not None:
                if move[0] == previous_move[0]:
                    continue


            # move to next state
            next_state = apply_move(current_state, move)
            next_key = self.state_key(next_state)

            if next_key in path_key:
                continue

            path.append(move)
            path_key.add(next_key)

            result = self._ida_search(
                next_state,
                g+1,
                bound,
                move,
                path,
                path_key
            )

            if result is True:
                return True

            if result < minimum_excess:
                minimum_excess = result

            path.pop()
            path_key.remove(next_key)

        return minimum_excess
