"""
Core Sudoku logic: puzzle generation, solving, validation.

Design goals:
- Every generated puzzle has exactly ONE unique solution.
- Difficulty controls how many cells are pre-filled (given cells).
- Pure Python, no external deps, so it is easy to unit test.
"""

import random
import copy

# Board is a 9x9 list of lists. 0 represents an empty cell.
SIZE = 9
BOX = 3

# Number of "given" (prefilled) cells per difficulty.
# Fewer givens -> harder puzzle.
DIFFICULTY_GIVENS = {
    "easy": 45,
    "medium": 34,
    "hard": 28,
}


def _find_empty(board):
    """Return (row, col) of the first empty cell, or None if full."""
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 0:
                return r, c
    return None


def is_valid(board, row, col, num):
    """Check whether placing `num` at (row, col) breaks Sudoku rules."""
    # Row check
    for c in range(SIZE):
        if board[row][c] == num and c != col:
            return False
    # Column check
    for r in range(SIZE):
        if board[r][col] == num and r != row:
            return False
    # 3x3 box check
    box_r = (row // BOX) * BOX
    box_c = (col // BOX) * BOX
    for r in range(box_r, box_r + BOX):
        for c in range(box_c, box_c + BOX):
            if board[r][c] == num and (r, c) != (row, col):
                return False
    return True


def _solve(board):
    """Backtracking solver. Fills the board in place. Returns True if solvable."""
    empty = _find_empty(board)
    if empty is None:
        return True
    row, col = empty
    for num in range(1, SIZE + 1):
        if is_valid(board, row, col, num):
            board[row][col] = num
            if _solve(board):
                return True
            board[row][col] = 0
    return False


def count_solutions(board, limit=2):
    """
    Count solutions up to `limit`. We only need to know if there is
    exactly one solution, so we stop early once we exceed 1.
    """
    empty = _find_empty(board)
    if empty is None:
        return 1
    row, col = empty
    total = 0
    for num in range(1, SIZE + 1):
        if is_valid(board, row, col, num):
            board[row][col] = num
            total += count_solutions(board, limit)
            board[row][col] = 0
            if total >= limit:
                return total
    return total


def _fill_full_board():
    """Generate a fully solved, randomized Sudoku board."""
    board = [[0] * SIZE for _ in range(SIZE)]

    def fill(pos=0):
        if pos == SIZE * SIZE:
            return True
        r, c = divmod(pos, SIZE)
        nums = list(range(1, SIZE + 1))
        random.shuffle(nums)
        for num in nums:
            if is_valid(board, r, c, num):
                board[r][c] = num
                if fill(pos + 1):
                    return True
                board[r][c] = 0
        return False

    fill()
    return board


def generate_puzzle(difficulty="easy"):
    """
    Generate a puzzle with a UNIQUE solution.

    Returns a dict: {"puzzle": board_with_zeros, "solution": full_board}
    """
    difficulty = difficulty.lower()
    if difficulty not in DIFFICULTY_GIVENS:
        raise ValueError(f"Unknown difficulty: {difficulty}")

    solution = _fill_full_board()
    puzzle = copy.deepcopy(solution)

    target_givens = DIFFICULTY_GIVENS[difficulty]
    cells_to_remove = SIZE * SIZE - target_givens

    # Remove cells one by one, but only if uniqueness is preserved.
    positions = [(r, c) for r in range(SIZE) for c in range(SIZE)]
    random.shuffle(positions)

    removed = 0
    for r, c in positions:
        if removed >= cells_to_remove:
            break
        backup = puzzle[r][c]
        puzzle[r][c] = 0
        # Verify the puzzle still has exactly one solution.
        board_copy = copy.deepcopy(puzzle)
        if count_solutions(board_copy, limit=2) != 1:
            # Removing this cell breaks uniqueness -> put it back.
            puzzle[r][c] = backup
        else:
            removed += 1

    return {"puzzle": puzzle, "solution": solution}


def solve_board(board):
    """Return a solved copy of the board, or None if unsolvable."""
    board_copy = copy.deepcopy(board)
    if _solve(board_copy):
        return board_copy
    return None


def find_hint(board, solution):
    """
    Return (row, col, value) for one empty cell filled from the solution,
    or None if the board is already complete.
    """
    empties = [
        (r, c)
        for r in range(SIZE)
        for c in range(SIZE)
        if board[r][c] == 0
    ]
    if not empties:
        return None
    r, c = random.choice(empties)
    return r, c, solution[r][c]


def check_board(board, solution):
    """
    Compare a (partially) filled board against the solution.
    Returns a list of [row, col] coordinates that are filled but wrong.
    """
    conflicts = []
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] != 0 and board[r][c] != solution[r][c]:
                conflicts.append([r, c])
    return conflicts
