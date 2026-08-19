# Sudoku — Flask Edition

A responsive, accessible Sudoku game built on a **Flask** backend with a
vanilla JavaScript front-end. Puzzle logic lives server-side and is fully
unit tested.

## Features
- Puzzles guaranteed to have **one unique solution**
- Difficulty levels (Easy / Medium / Hard) that change prefilled cells
- Locked prefilled and hinted cells
- **Hint** button — fills one correct cell and locks it
- **Check** button — highlights incorrect entries
- Conflict highlighting and a completion (congratulations) message
- Timer and hint counter
- **Top 10** leaderboard (name, time, difficulty, hints) stored in `localStorage`
- **Dark mode** toggle that persists across sessions
- Responsive layout, alternating 3×3 box colors, no layout shift

## Project structure
```
sudoku_flask/
├── app.py               # Flask app + JSON API
├── sudoku_logic.py      # Puzzle generation / solving / validation
├── instructions.md      # Copilot instruction file
├── requirements.txt
├── templates/
│   └── index.html       # Main page (Jinja2)
├── static/
│   ├── css/style.css    # Themes, layout, responsive styles
│   └── js/sudoku.js     # Front-end controller
├── tests/
│   └── test_sudoku.py   # pytest suite
└── Screenshots/         # Copilot prompt screenshots
```

## Setup & run

```bash
# 1. (optional) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run the Flask app
flask run
# or:
python app.py
```

Then open <http://127.0.0.1:5000> in your browser.

## Running tests
```bash
pytest
```

## API endpoints
| Method | Endpoint     | Purpose                              |
|--------|--------------|--------------------------------------|
| GET    | `/`          | Serve the game page                  |
| POST   | `/api/new`   | Generate a puzzle for a difficulty   |
| POST   | `/api/hint`  | Return one correct cell              |
| POST   | `/api/check` | Return a list of incorrect cells     |
