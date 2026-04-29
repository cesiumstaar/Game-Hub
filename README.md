# Mini Game Hub

A small multi-user game hub with Bash-based authentication and Pygame-based gameplay.

Included games:
- Tic-Tac-Toe
- Tic-Tac-Toe vs Engine
- Othello
- Connect Four

## Requirements

- Python 3.10+
- Bash
- `pygame-ce`
- `numpy`
- `matplotlib`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pygame-ce numpy matplotlib
```

## Run

From the repository root:

```bash
bash main.sh
```

This will:
- authenticate two players
- open the game menu
- record results to `history.csv`
- print the terminal leaderboard

## Build Report

```bash
make
```

## Files

- `main.sh` - authentication and launch flow
- `game.py` - main menu, routing, stats, and post-game screen
- `games/` - game implementations
- `leaderboard.sh` - terminal leaderboard
- `report.tex` - LaTeX report source
