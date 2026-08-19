# Copilot Instructions — Sudoku (Flask)

This file gives GitHub Copilot the context and conventions to follow when
suggesting code for this project.

## Project overview
A browser-based Sudoku game served by a **Flask** backend. The Flask app
renders a single HTML page and exposes a small JSON API. All puzzle logic
(generation, solving, uniqueness checking, hints, validation) lives on the
server in `sudoku_logic.py` so it can be unit tested independently of the UI.

## Tech stack
- Backend: Python 3 + Flask (`app.py`, `sudoku_logic.py`)
- Frontend: plain HTML (Jinja2 templates), vanilla JavaScript, plain CSS
- Tests: pytest (`tests/`)
- No frontend build step, no external JS frameworks.

## Coding conventions
- Python: PEP 8, snake_case, docstrings on every public function.
- JavaScript: `"use strict"`, camelCase, small single-purpose functions,
  wrapped in an IIFE to avoid polluting the global scope.
- CSS: use CSS custom properties (variables) for theming. Light and dark
  themes are driven by a `data-theme` attribute on `<html>`.
- Always include clear comments and consistent error handling.
- API responses are JSON. Errors return `{ "error": "..." }` with an
  appropriate HTTP status code.

## Functional requirements Copilot should respect
- Puzzles must have exactly **one unique solution**.
- Difficulty (easy/medium/hard) changes the number of prefilled cells.
- Prefilled and hinted cells are locked.
- Invalid entries get visual feedback (conflict highlighting).
- Hint fills one correct empty cell and locks it.
- Check highlights incorrect entries.
- A timer and hint counter run during play.
- On completion, prompt for a name and store a **Top 10** list
  (name, time, difficulty, hints) in `localStorage`.
- Dark mode toggle persists via `localStorage`.

## What to avoid
- Do not move puzzle logic into the frontend; keep it server-side.
- Do not use browser storage for anything other than the leaderboard and
  the theme preference.
- Do not add heavy dependencies or a JS framework.
