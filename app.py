"""
Flask application entry point for the Sudoku game.

Serves the single-page game UI and exposes a small JSON API that the
front-end calls for puzzle generation, hints, and validation. All puzzle
logic lives server-side in sudoku_logic.py so it can be unit tested.
"""

from flask import Flask, render_template, request, jsonify
from sudoku_logic import (
    generate_puzzle,
    find_hint,
    check_board,
    DIFFICULTY_GIVENS,
)

app = Flask(__name__)


@app.route("/")
def index():
    """Render the main game page."""
    return render_template("index.html")


@app.route("/api/new", methods=["POST"])
def api_new():
    """Generate a new puzzle for the requested difficulty."""
    data = request.get_json(silent=True) or {}
    difficulty = str(data.get("difficulty", "easy")).lower()

    if difficulty not in DIFFICULTY_GIVENS:
        return jsonify({"error": f"Invalid difficulty '{difficulty}'."}), 400

    try:
        result = generate_puzzle(difficulty)
    except Exception as exc:  # defensive: surface a clean error to the client
        return jsonify({"error": f"Failed to generate puzzle: {exc}"}), 500

    return jsonify(
        {
            "puzzle": result["puzzle"],
            "solution": result["solution"],
            "difficulty": difficulty,
        }
    )


@app.route("/api/hint", methods=["POST"])
def api_hint():
    """Return one correct cell for the current board."""
    data = request.get_json(silent=True) or {}
    board = data.get("board")
    solution = data.get("solution")

    error = _validate_grids(board, solution)
    if error:
        return jsonify({"error": error}), 400

    hint = find_hint(board, solution)
    if hint is None:
        return jsonify({"error": "Board is already complete."}), 400

    row, col, value = hint
    return jsonify({"row": row, "col": col, "value": value})


@app.route("/api/check", methods=["POST"])
def api_check():
    """Return a list of incorrect cells on the current board."""
    data = request.get_json(silent=True) or {}
    board = data.get("board")
    solution = data.get("solution")

    error = _validate_grids(board, solution)
    if error:
        return jsonify({"error": error}), 400

    conflicts = check_board(board, solution)
    return jsonify({"conflicts": conflicts})


def _validate_grids(*grids):
    """Return an error string if any grid is not a valid 9x9 matrix."""
    for grid in grids:
        if not isinstance(grid, list) or len(grid) != 9:
            return "Board data is malformed (expected a 9x9 grid)."
        for row in grid:
            if not isinstance(row, list) or len(row) != 9:
                return "Board data is malformed (expected a 9x9 grid)."
    return None


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Resource not found."}), 404


@app.errorhandler(500)
def server_error(_):
    return jsonify({"error": "Internal server error."}), 500


if __name__ == "__main__":
    app.run(debug=True)
