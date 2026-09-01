"""
Unit tests for the Sudoku logic and Flask API.
Run with:  pytest
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from sudoku_logic import (
    generate_puzzle,
    count_solutions,
    solve_board,
    is_valid,
    check_board,
    find_hint,
    DIFFICULTY_GIVENS,
)
from app import app as flask_app


# ---------------------------------------------------------------
# Logic tests
# ---------------------------------------------------------------
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_generated_puzzle_has_unique_solution(difficulty):
    """Every generated puzzle must have exactly one solution."""
    result = generate_puzzle(difficulty)
    puzzle = [row[:] for row in result["puzzle"]]
    assert count_solutions(puzzle, limit=2) == 1


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_repeated_generation_keeps_single_solution_for_each_difficulty(difficulty):
    """Generate several puzzles per difficulty and verify each has exactly one solution."""
    for _ in range(10):
        result = generate_puzzle(difficulty)
        puzzle = [row[:] for row in result["puzzle"]]
        assert count_solutions(puzzle, limit=2) == 1


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_given_count_matches_difficulty(difficulty):
    """The number of prefilled cells should match the difficulty target."""
    result = generate_puzzle(difficulty)
    givens = sum(1 for row in result["puzzle"] for v in row if v != 0)
    assert givens == DIFFICULTY_GIVENS[difficulty]


def test_solution_solves_puzzle():
    """The provided solution must actually solve its puzzle."""
    result = generate_puzzle("easy")
    solved = solve_board(result["puzzle"])
    assert solved == result["solution"]


def test_is_valid_detects_conflicts():
    board = [[0] * 9 for _ in range(9)]
    board[0][0] = 5
    assert is_valid(board, 0, 1, 5) is False  # same row
    assert is_valid(board, 1, 0, 5) is False  # same column
    assert is_valid(board, 1, 1, 5) is False  # same box
    assert is_valid(board, 4, 4, 5) is True   # unrelated cell


def test_check_board_finds_wrong_cells():
    result = generate_puzzle("easy")
    board = [row[:] for row in result["solution"]]
    # Introduce a deliberate error in an empty spot
    for r in range(9):
        for c in range(9):
            if result["puzzle"][r][c] == 0:
                board[r][c] = (result["solution"][r][c] % 9) + 1
                conflicts = check_board(board, result["solution"])
                assert [r, c] in conflicts
                return


def test_check_board_ignores_empty_and_correct_cells():
    result = generate_puzzle("easy")
    board = [row[:] for row in result["puzzle"]]

    assert check_board(board, result["solution"]) == []

    empty_cell = next(
        (r, c)
        for r in range(9)
        for c in range(9)
        if result["puzzle"][r][c] == 0
    )
    row, col = empty_cell
    board[row][col] = result["solution"][row][col]
    assert check_board(board, result["solution"]) == []


def test_find_hint_returns_correct_value():
    result = generate_puzzle("easy")
    hint = find_hint(result["puzzle"], result["solution"])
    assert hint is not None
    r, c, value = hint
    assert value == result["solution"][r][c]


def test_invalid_difficulty_raises():
    with pytest.raises(ValueError):
        generate_puzzle("impossible")


def test_solve_board_returns_none_for_unsolvable_board():
    board = [[0] * 9 for _ in range(9)]
    board[0][:8] = range(1, 9)
    board[1][8] = 9

    assert solve_board(board) is None


def test_find_hint_returns_none_for_complete_board():
    result = generate_puzzle("easy")

    assert find_hint(result["solution"], result["solution"]) is None


# ---------------------------------------------------------------
# API tests
# ---------------------------------------------------------------
@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def test_index_route(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Sudoku" in resp.data


def test_api_new_valid(client):
    resp = client.post("/api/new", json={"difficulty": "easy"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["difficulty"] == "easy"
    assert len(data["puzzle"]) == 9
    assert len(data["solution"]) == 9
    assert all(len(row) == 9 for row in data["puzzle"])
    assert all(len(row) == 9 for row in data["solution"])


def test_api_new_defaults_to_easy(client):
    resp = client.post("/api/new", json={})

    assert resp.status_code == 200
    assert resp.get_json()["difficulty"] == "easy"


def test_api_new_invalid_difficulty(client):
    resp = client.post("/api/new", json={"difficulty": "nope"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_api_hint_returns_empty_cell_from_solution(client):
    result = generate_puzzle("easy")
    resp = client.post(
        "/api/hint",
        json={"board": result["puzzle"], "solution": result["solution"]},
    )

    assert resp.status_code == 200
    hint = resp.get_json()
    assert 0 <= hint["row"] < 9
    assert 0 <= hint["col"] < 9
    assert result["puzzle"][hint["row"]][hint["col"]] == 0
    assert hint["value"] == result["solution"][hint["row"]][hint["col"]]


def test_api_hint_rejects_complete_board(client):
    result = generate_puzzle("easy")
    resp = client.post(
        "/api/hint",
        json={"board": result["solution"], "solution": result["solution"]},
    )

    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Board is already complete."


def test_api_check_returns_wrong_cells(client):
    result = generate_puzzle("easy")
    board = [row[:] for row in result["solution"]]
    row, col = next(
        (r, c)
        for r in range(9)
        for c in range(9)
        if result["solution"][r][c] != 1
    )
    board[row][col] = (result["solution"][row][col] % 9) + 1

    resp = client.post(
        "/api/check", json={"board": board, "solution": result["solution"]}
    )

    assert resp.status_code == 200
    assert resp.get_json()["conflicts"] == [[row, col]]


@pytest.mark.parametrize("endpoint", ["/api/hint", "/api/check"])
def test_api_rejects_malformed_grids(client, endpoint):
    resp = client.post(endpoint, json={"board": [[0]], "solution": [[0]]})

    assert resp.status_code == 400
    assert "9x9 grid" in resp.get_json()["error"]


def test_api_check_malformed(client):
    resp = client.post("/api/check", json={"board": [1, 2, 3], "solution": []})
    assert resp.status_code == 400
