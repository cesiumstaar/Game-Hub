# Game-Hub-
Course project of CS108: Systems Software Lab
# Mini Game Hub

## Overview
Mini Game Hub is a secure multi-user game platform built using **Bash**, **Python**, and **Pygame**.  
The system allows two authenticated users to log in, choose from a set of board games, play through a graphical interface, and store match results in a persistent leaderboard/history system.

The goal of the project is to build a complete end-to-end system that combines user authentication, game logic, graphical gameplay, result storage, and leaderboard/statistics display.

## Proposed Features

### 1. User Authentication
- Two players log in before starting a game.
- New users can register if their username does not already exist.
- Passwords are stored securely using **SHA-256 hashing** in `users.tsv`.
- Plaintext passwords are never stored.

### 2. Multi-Game Menu
After authentication, the system will show a game menu where players can choose one of the supported games:
- Tic-Tac-Toe
- Othello (Reversi)
- Connect Four

### 3. Graphical Gameplay
- All games will run in a **Pygame GUI window**.
- Players interact using mouse input.
- The interface will display the board, turns, and result messages.

### 4. Object-Oriented Game Design
- A common base class will be used for all 2-player board games.
- Each game will inherit from this base class and implement its own rules.

### 5. Result Recording
- After each game, the winner, loser, date, and game name will be saved to `history.csv`.

### 6. Leaderboard and Analytics
- A Bash script will read match history and display leaderboard statistics.
- The system will also show simple visualizations such as:
  - top players by wins,
  - most played games.

### 7. Replay Option
- After a match, players can choose to return to the menu and play another game or quit.

## System Design

The project follows a modular design with a clear separation between authentication, game management, individual game logic, and leaderboard/statistics handling.

At a high level, the system starts from a Bash script, `main.sh`, which is responsible for user login and registration. Once both users are authenticated, control is passed to the Python game engine through:

```bash
python3 game.py <username1> <username2>
