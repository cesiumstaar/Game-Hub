# Mini Game Hub

A secure, multi-user game hub integrating Bash scripting for authentication and Python (Pygame) for gameplay. Two authenticated players select a game from a menu, play via a graphical interface, and have their results recorded on a persistent leaderboard.

## Requirements

- Python 3.10+
- pip packages: `pygame-ce`, `numpy`, `matplotlib`
- Bash (for authentication and leaderboard)

### Install dependencies

```bash
pip install pygame-ce numpy matplotlib
```

## How to Run

```bash
cd hub
bash main.sh
```

This will:
1. Prompt two players to login or register
2. Launch the Pygame game menu
3. Let players choose and play games
4. Record results and show leaderboard + charts

## Project Structure

```
hub/
├── main.sh              # Entry point - Bash authentication
├── game.py              # Game engine - menu, result recording, visualizations
├── leaderboard.sh       # Bash leaderboard display script
├── games/
│   ├── __init__.py      # Package init
│   ├── base_game.py     # Abstract base class for all games
│   ├── tictactoe.py     # 10x10 Tic-Tac-Toe (5 in a row)
│   ├── othello.py       # 8x8 Othello (Reversi)
│   └── connect4.py      # 7x7 Connect Four
├── report/
│   ├── report.tex       # LaTeX project report
│   └── Makefile         # Compile the report
├── users.tsv            # Auto-generated user credentials (SHA-256 hashed)
└── history.csv          # Auto-generated game results log
```

## Games

| Game | Board | Win Condition |
|------|-------|---------------|
| Tic-Tac-Toe | 10x10 | 5 marks in a row (horizontal, vertical, diagonal) |
| Othello | 8x8 | Most discs when no valid moves remain |
| Connect Four | 7x7 | 4 coins in a row (horizontal, vertical, diagonal) |

## Technical Highlights

- **NumPy arrays** for all game boards
- **No loops in win detection** - uses NumPy slicing, sliding windows, and vectorized operations
- **SHA-256 password hashing** - never stores plaintext passwords
- **Pygame GUI** for all games - no terminal-based gameplay
- **Matplotlib charts** - top 5 players bar chart + most played games pie chart
- **Modular OOP design** - base class with inheritance for each game

## Building the Report

```bash
cd hub/report
make
```

---

## Weekly Commit Schedule

### Week 1 - Project Setup & Authentication

| Who | Files | Commit Message |
|-----|-------|----------------|
| **Shresth** | `main.sh` | `feat: add bash authentication system with SHA-256 password hashing and user registration` |
| **Aryan** | `game.py`, `games/__init__.py`, `games/base_game.py` | `feat: add game engine with menu system and abstract base class for board games` |

**What these files do:**
- `main.sh` - Authenticates two players via terminal (login/register), hashes passwords with SHA-256, stores in `users.tsv`, then launches `game.py`
- `game.py` - Main game engine: Pygame menu for game selection, result recording to `history.csv`, matplotlib visualization, post-game loop
- `games/base_game.py` - Abstract base class `BoardGame` with NumPy board, turn management, and abstract `check_win()`
- `games/__init__.py` - Package initializer importing all game classes

---

### Week 2 - Tic-Tac-Toe & Connect Four

| Who | Files | Commit Message |
|-----|-------|----------------|
| **Shresth** | `games/tictactoe.py` | `feat: implement 10x10 Tic-Tac-Toe with NumPy sliding window win detection and Pygame GUI` |
| **Aryan** | `games/connect4.py` | `feat: implement 7x7 Connect Four with gravity, coin-drop animation, and NumPy win detection` |

**What these files do:**
- `games/tictactoe.py` - 10x10 Tic-Tac-Toe where 5 in a row wins. Uses `sliding_window_view` for loop-free win detection. Player 1 = +1 (X), Player 2 = -1 (O)
- `games/connect4.py` - 7x7 Connect Four with gravity physics. Coins drop to lowest empty row. Win detection uses boolean masks + NumPy slicing. Includes drop animation

---

### Week 3 - Othello & Leaderboard

| Who | Files | Commit Message |
|-----|-------|----------------|
| **Shresth** | `games/othello.py` | `feat: implement 8x8 Othello with disc flipping, valid move hints, and NumPy-based scoring` |
| **Aryan** | `leaderboard.sh` | `feat: add bash leaderboard script with per-game stats and sortable metrics` |

**What these files do:**
- `games/othello.py` - Full Othello/Reversi with 8-direction move validation, disc flipping, turn skipping when no moves, and numpy-based disc counting for win determination
- `leaderboard.sh` - Reads `history.csv`, computes wins/losses/ratio per player per game, displays formatted table sorted by user-chosen metric (wins, losses, or ratio)

---

### Week 4 - Visualization & Integration Polish

| Who | Files | Commit Message |
|-----|-------|----------------|
| **Shresth** | `game.py` (update visualization functions) | `feat: add matplotlib visualizations with top-5 players bar chart and most-played games pie chart` |
| **Aryan** | `game.py` (update post-game loop + menu), `games/__init__.py` | `feat: add post-game screen with play-again option and integrate leaderboard sort selection in menu` |

**Note:** Both Shresth and Aryan modify `game.py` in this week. Shresth works on the `show_visualizations()` and chart display functions. Aryan works on `post_game_screen()` and `game_menu()` enhancements. **Use a branch and merge** to create the required merge commit.

**Recommended workflow for Week 4:**
1. Shresth creates branch `feature/visualizations`, makes changes, pushes
2. Aryan creates branch `feature/postgame`, makes changes, pushes
3. One person merges both branches into `main` (this creates the required merge commit)

---

### Week 5 - Report & Documentation

| Who | Files | Commit Message |
|-----|-------|----------------|
| **Shresth** | `report/report.tex`, `report/Makefile` | `docs: add LaTeX project report with code explanations, hurdles, and bibliography` |
| **Aryan** | `README.md` | `docs: add comprehensive README with setup instructions, project structure, and usage guide` |

**What these files do:**
- `report/report.tex` - Full LaTeX report covering: libraries used, features implemented, code logic for each component, hurdles faced, future improvements, and bibliography
- `report/Makefile` - Compiles the LaTeX report with `make` (runs pdflatex twice for table of contents)
- `README.md` - Project documentation with installation instructions, how to run, project structure, game descriptions, and technical highlights

---

## Commit Summary Table

| Week | Shresth's Commit | Aryan's Commit |
|------|-------------------|----------------|
| 1 | `main.sh` - Authentication | `game.py`, `base_game.py`, `__init__.py` - Game engine + base class |
| 2 | `tictactoe.py` - Tic-Tac-Toe game | `connect4.py` - Connect Four game |
| 3 | `othello.py` - Othello game | `leaderboard.sh` - Leaderboard script |
| 4 | `game.py` update - Visualizations | `game.py` update - Post-game loop (use branches + merge) |
| 5 | `report/` - LaTeX report + Makefile | `README.md` - Project documentation |

## Important Notes

1. **Week 4 must use branches** to create the required merge commit
2. All commit messages should be descriptive (use the suggested messages above)
3. Each person must commit from their own GitHub account
4. The repository must be **private**
5. At the end, `bash main.sh` from the `hub/` directory should run everything
