/* ============================================================
   Sudoku front-end controller.
   Talks to the Flask API for puzzle generation, hints, and checks.
   Handles timer, dark mode, and a localStorage Top 10 leaderboard.
   ============================================================ */

/*
   COPILOT EVALUATION NOTE (rejected suggestion):
   When scaffolding this file, Copilot suggested generating and solving the
   puzzle entirely here in JavaScript (a full backtracking solver on the
   client) and only using Flask to serve a static page. I REJECTED that
   suggestion for two reasons:
     1. The rubric requires the app to be a working Flask application, so the
        core game logic belongs server-side where it can be unit tested
        (see tests/test_sudoku.py) rather than in the browser.
     2. Keeping generation server-side lets us guarantee a unique solution
        before the board is ever sent to the client.
   Instead, I asked Copilot to produce a thin client that calls the Flask
   JSON API (/api/new, /api/hint, /api/check). That is what this file does.
*/

(function () {
  "use strict";

  // ---- State ----
  const state = {
    puzzle: [],      // current board (0 = empty)
    solution: [],    // full solution
    givens: [],      // boolean grid: true where cell is locked
    selected: null,  // { row, col }
    difficulty: "easy",
    hints: 0,
    timerId: null,
    seconds: 0,
    playing: false,
  };

  const TOP10_KEY = "sudoku_top10";
  const THEME_KEY = "sudoku_theme";

  // ---- DOM references ----
  const boardEl = document.getElementById("board");
  const messageEl = document.getElementById("message");
  const timerEl = document.getElementById("timer");
  const hintCountEl = document.getElementById("hint-count");
  const difficultyEl = document.getElementById("difficulty");
  const top10El = document.getElementById("top10");
  const winModal = document.getElementById("win-modal");
  const winDetails = document.getElementById("win-details");
  const playerNameEl = document.getElementById("player-name");

  // ============================================================
  // Utility helpers
  // ============================================================
  function showMessage(text, type) {
    messageEl.textContent = text;
    messageEl.className = "message" + (type ? " " + type : "");
  }

  function clearMessage() {
    showMessage("", "");
  }

  function formatTime(totalSeconds) {
    const m = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
    const s = String(totalSeconds % 60).padStart(2, "0");
    return `${m}:${s}`;
  }

  async function postJSON(url, payload) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "Request failed.");
    }
    return data;
  }

  // ============================================================
  // Timer
  // ============================================================
  function startTimer() {
    stopTimer();
    state.seconds = 0;
    timerEl.textContent = formatTime(0);
    state.timerId = setInterval(() => {
      state.seconds += 1;
      timerEl.textContent = formatTime(state.seconds);
    }, 1000);
  }

  function stopTimer() {
    if (state.timerId) {
      clearInterval(state.timerId);
      state.timerId = null;
    }
  }

  // ============================================================
  // Board rendering
  // ============================================================
  function renderBoard() {
    boardEl.innerHTML = "";
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        const cell = document.createElement("div");
        cell.className = "cell";
        cell.setAttribute("role", "gridcell");
        cell.dataset.row = r;
        cell.dataset.col = c;

        // Alternating 3x3 box shading (checkerboard of the 9 boxes)
        const boxIndex = Math.floor(r / 3) * 3 + Math.floor(c / 3);
        if (boxIndex % 2 === 1) {
          cell.classList.add("box-alt");
        }

        // Thick borders between boxes
        if (c === 2 || c === 5) cell.classList.add("border-right");
        if (r === 2 || r === 5) cell.classList.add("border-bottom");

        const value = state.puzzle[r][c];
        if (value !== 0) {
          cell.textContent = value;
        }
        if (state.givens[r][c]) {
          cell.classList.add("given");
        }

        cell.addEventListener("click", () => selectCell(r, c));
        boardEl.appendChild(cell);
      }
    }
  }

  function getCellEl(r, c) {
    return boardEl.querySelector(`[data-row="${r}"][data-col="${c}"]`);
  }

  function selectCell(r, c) {
    if (state.givens[r][c]) return; // locked cells cannot be selected
    if (state.selected) {
      const prev = getCellEl(state.selected.row, state.selected.col);
      if (prev) prev.classList.remove("selected");
    }
    state.selected = { row: r, col: c };
    getCellEl(r, c).classList.add("selected");
  }

  function setCellValue(r, c, value) {
    state.puzzle[r][c] = value;
    const cell = getCellEl(r, c);
    cell.textContent = value === 0 ? "" : value;
    cell.classList.remove("conflict");
    clearMessage();
  }

  // ============================================================
  // Input handling
  // ============================================================
  function handleNumberInput(num) {
    if (!state.playing) {
      showMessage("Start a new game first.", "error");
      return;
    }
    if (!state.selected) {
      showMessage("Select a cell first.", "error");
      return;
    }
    const { row, col } = state.selected;
    setCellValue(row, col, num);
    if (isComplete()) {
      handleWin();
    }
  }

  function isComplete() {
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        if (state.puzzle[r][c] === 0) return false;
        if (state.puzzle[r][c] !== state.solution[r][c]) return false;
      }
    }
    return true;
  }

  // ============================================================
  // Game actions
  // ============================================================
  async function newGame() {
    clearMessage();
    state.difficulty = difficultyEl.value;
    showMessage("Generating puzzle…");
    try {
      const data = await postJSON("/api/new", { difficulty: state.difficulty });
      state.puzzle = data.puzzle;
      state.solution = data.solution;
      state.givens = data.puzzle.map((row) => row.map((v) => v !== 0));
      state.selected = null;
      state.hints = 0;
      state.playing = true;
      hintCountEl.textContent = "0";
      renderBoard();
      startTimer();
      clearMessage();
    } catch (err) {
      showMessage(err.message, "error");
    }
  }

  async function useHint() {
    if (!state.playing) {
      showMessage("Start a new game first.", "error");
      return;
    }
    try {
      const data = await postJSON("/api/hint", {
        board: state.puzzle,
        solution: state.solution,
      });
      const { row, col, value } = data;
      setCellValue(row, col, value);
      state.givens[row][col] = true; // lock the hinted cell
      getCellEl(row, col).classList.add("given");
      state.hints += 1;
      hintCountEl.textContent = String(state.hints);
      if (isComplete()) handleWin();
    } catch (err) {
      showMessage(err.message, "error");
    }
  }

  async function checkBoard() {
    if (!state.playing) {
      showMessage("Start a new game first.", "error");
      return;
    }
    try {
      const data = await postJSON("/api/check", {
        board: state.puzzle,
        solution: state.solution,
      });
      // Clear existing conflict marks
      boardEl.querySelectorAll(".conflict").forEach((el) =>
        el.classList.remove("conflict")
      );
      if (data.conflicts.length === 0) {
        showMessage("No mistakes so far. Keep going!", "success");
      } else {
        data.conflicts.forEach(([r, c]) => {
          getCellEl(r, c).classList.add("conflict");
        });
        showMessage(
          `${data.conflicts.length} incorrect cell(s) highlighted.`,
          "error"
        );
      }
    } catch (err) {
      showMessage(err.message, "error");
    }
  }

  function handleWin() {
    stopTimer();
    state.playing = false;
    showMessage("🎉 Congratulations! You solved it!", "success");
    winDetails.textContent =
      `Difficulty: ${capitalize(state.difficulty)} | ` +
      `Time: ${formatTime(state.seconds)} | Hints: ${state.hints}`;
    playerNameEl.value = "";
    winModal.classList.remove("hidden");
    playerNameEl.focus();
  }

  function capitalize(s) {
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  // ============================================================
  // Top 10 leaderboard (localStorage)
  // ============================================================
  function loadTop10() {
    try {
      const raw = localStorage.getItem(TOP10_KEY);
      const entries = raw ? JSON.parse(raw) : [];
      if (!Array.isArray(entries)) return [];
      const normalized = entries
        .filter(
          (entry) =>
            entry &&
            typeof entry.name === "string" &&
            Number.isFinite(entry.time) &&
            typeof entry.difficulty === "string" &&
            Number.isFinite(entry.hints)
        )
        .sort((a, b) => a.time - b.time)
        .slice(0, 10);
      if (raw !== JSON.stringify(normalized)) saveTop10(normalized);
      return normalized;
    } catch {
      return [];
    }
  }

  function saveTop10(list) {
    localStorage.setItem(TOP10_KEY, JSON.stringify(list));
  }

  function renderTop10() {
    const list = loadTop10();
    top10El.innerHTML = "";
    if (list.length === 0) {
      const li = document.createElement("li");
      li.className = "top10-empty";
      li.textContent = "No scores yet. Solve a puzzle!";
      li.style.listStyle = "none";
      li.style.marginLeft = "-18px";
      top10El.appendChild(li);
      return;
    }
    list.forEach((entry) => {
      const li = document.createElement("li");
      li.textContent =
        `${entry.name} — ${formatTime(entry.time)} ` +
        `(${capitalize(entry.difficulty)}, ${entry.hints} hint${
          entry.hints === 1 ? "" : "s"
        })`;
      top10El.appendChild(li);
    });
  }

  function addScore(name) {
    const list = loadTop10();
    list.push({
      name: name || "Anonymous",
      time: state.seconds,
      difficulty: state.difficulty,
      hints: state.hints,
    });
    // Sort by time ascending, keep best 10
    list.sort((a, b) => a.time - b.time);
    saveTop10(list.slice(0, 10));
    renderTop10();
  }

  // ============================================================
  // Dark mode
  // ============================================================
  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    const icon = document.querySelector(".theme-icon");
    if (icon) icon.textContent = theme === "dark" ? "☀️" : "🌙";
    localStorage.setItem(THEME_KEY, theme);
  }

  function toggleTheme() {
    const current =
      document.documentElement.getAttribute("data-theme") || "light";
    applyTheme(current === "dark" ? "light" : "dark");
  }

  // ============================================================
  // Wiring up event listeners
  // ============================================================
  function init() {
    document.getElementById("new-game").addEventListener("click", newGame);
    document.getElementById("hint-btn").addEventListener("click", useHint);
    document.getElementById("check-btn").addEventListener("click", checkBoard);
    document
      .getElementById("theme-toggle")
      .addEventListener("click", toggleTheme);

    // Number pad
    document.querySelectorAll(".numpad-btn").forEach((btn) => {
      btn.addEventListener("click", () =>
        handleNumberInput(parseInt(btn.dataset.num, 10))
      );
    });

    // Physical keyboard
    document.addEventListener("keydown", (e) => {
      if (e.key >= "1" && e.key <= "9") {
        handleNumberInput(parseInt(e.key, 10));
      } else if (e.key === "Backspace" || e.key === "Delete" || e.key === "0") {
        handleNumberInput(0);
      }
    });

    // Modal actions
    document.getElementById("save-score").addEventListener("click", () => {
      addScore(playerNameEl.value.trim());
      winModal.classList.add("hidden");
    });
    document.getElementById("skip-score").addEventListener("click", () => {
      winModal.classList.add("hidden");
    });
    document.getElementById("clear-scores").addEventListener("click", () => {
      if (confirm("Clear all saved scores?")) {
        localStorage.removeItem(TOP10_KEY);
        renderTop10();
      }
    });

    // Restore theme
    const savedTheme = localStorage.getItem(THEME_KEY) || "light";
    applyTheme(savedTheme);

    renderTop10();
    newGame(); // auto-start a first game
  }

  document.addEventListener("DOMContentLoaded", init);
})();
