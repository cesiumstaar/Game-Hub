#!/usr/bin/env python3
"""
game.py – Main game engine for Mini Game Hub.
Receives two authenticated usernames from main.sh and manages game
selection, launching, result recording, leaderboard display, and
Matplotlib visualizations.
"""

import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path

import pygame
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from games.tictactoe import TicTacToe
from games.othello import Othello
from games.connect4 import ConnectFour

SCREEN_WIDTH = 700
SCREEN_HEIGHT = 640
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (200, 200, 200)
BLUE = (41, 128, 185)
GREEN = (39, 174, 96)
RED = (231, 76, 60)
ORANGE = (243, 156, 18)
PURPLE = (142, 68, 173)
TEAL = (22, 160, 133)
HOVER_COLOR = (230, 230, 250)

SCRIPT_DIR = Path(__file__).parent.resolve()
HISTORY_FILE = SCRIPT_DIR / "history.csv"
LEADERBOARD_SCRIPT = SCRIPT_DIR / "leaderboard.sh"


def ensure_history_file():
    if not HISTORY_FILE.exists():
        with open(HISTORY_FILE, "w") as f:
            f.write("Winner,Loser,Date,Game\n")


def record_result(winner: str, loser: str, game_name: str):
    ensure_history_file()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{winner},{loser},{date_str},{game_name}\n")


def call_leaderboard(sort_metric: str = "wins"):
    if LEADERBOARD_SCRIPT.exists():
        try:
            subprocess.run(
                ["bash", str(LEADERBOARD_SCRIPT), str(HISTORY_FILE), sort_metric],
                cwd=str(SCRIPT_DIR)
            )
        except Exception as e:
            print(f"Error calling leaderboard: {e}")


def show_visualizations():
    """Generate bar + pie charts and save to stats.png. Returns file path."""
    if not HISTORY_FILE.exists():
        return

    all_players: set[str] = set()
    win_counts: dict[str, int] = {}
    games_played = []
    with open(HISTORY_FILE, "r") as f:
        lines = f.read().splitlines()
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split(",")
        if len(parts) < 4:
            continue
        winner, loser = parts[0].strip(), parts[1].strip()
        if winner != "draw":
            all_players.add(winner)
            win_counts[winner] = win_counts.get(winner, 0) + 1
        if loser != "draw":
            all_players.add(loser)
            win_counts.setdefault(loser, 0)
        games_played.append(parts[3].strip())

    if not all_players and not games_played:
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Game Hub Statistics", fontsize=16, fontweight="bold")

    if all_players:
        top5 = sorted(win_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        names = [item[0] for item in top5]
        counts = [item[1] for item in top5]
        colors = [BLUE, GREEN, RED, ORANGE, PURPLE][:len(names)]
        colors_norm = [(r/255, g/255, b/255) for r, g, b in colors]
        axes[0].bar(names, counts, color=colors_norm)
        axes[0].set_title("Top 5 Players by Wins")
        axes[0].set_xlabel("Player")
        axes[0].set_ylabel("Wins")
        axes[0].set_ylim(bottom=0)
    else:
        axes[0].text(0.5, 0.5, "No wins recorded yet", ha="center", va="center")
        axes[0].set_title("Top 5 Players by Wins")

    if games_played:
        game_counts: dict[str, int] = {}
        for gp in games_played:
            game_counts[gp] = game_counts.get(gp, 0) + 1
        labels = list(game_counts.keys())
        sizes = list(game_counts.values())
        pie_colors = [(r/255, g/255, b/255) for r, g, b in
                      [BLUE, GREEN, RED, ORANGE, PURPLE, TEAL][:len(labels)]]
        axes[1].pie(sizes, labels=labels, colors=pie_colors, autopct="%1.1f%%", startangle=90)
        axes[1].set_title("Most Played Games")
    else:
        axes[1].text(0.5, 0.5, "No games played yet", ha="center", va="center")
        axes[1].set_title("Most Played Games")

    plt.tight_layout()
    plt.savefig(str(SCRIPT_DIR / "stats.png"), dpi=100)
    plt.close()
    return str(SCRIPT_DIR / "stats.png")


def draw_text(screen, text, x, y, font, color=BLACK, center=False):
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surface, rect)
    return rect


def ai_player_select(screen, player1: str, player2: str):
    """Show selection screen for which player challenges the AI.
    Returns chosen player name or None if cancelled."""
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("Arial", 36, bold=True)
    subtitle_font = pygame.font.SysFont("Arial", 22)
    button_font = pygame.font.SysFont("Arial", 26, bold=True)
    small_font = pygame.font.SysFont("Arial", 18)

    players = [player1, player2]

    while True:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(WHITE)

        draw_text(screen, "Tic-Tac-Toe vs AI", SCREEN_WIDTH // 2, 80, title_font, PURPLE, center=True)
        draw_text(screen, "Who wants to challenge the Computer?", SCREEN_WIDTH // 2, 140, subtitle_font, DARK_GRAY, center=True)

        btn_rects = []
        for i, name in enumerate(players):
            btn_y = 230 + i * 110
            btn_rect = pygame.Rect(150, btn_y, 400, 80)
            btn_rects.append((btn_rect, name))

            if btn_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, PURPLE, btn_rect, border_radius=12)
                draw_text(screen, name, SCREEN_WIDTH // 2, btn_y + 28, button_font, WHITE, center=True)
                draw_text(screen, f"{name} vs Computer", SCREEN_WIDTH // 2, btn_y + 58, small_font, WHITE, center=True)
            else:
                pygame.draw.rect(screen, PURPLE, btn_rect, width=3, border_radius=12)
                draw_text(screen, name, SCREEN_WIDTH // 2, btn_y + 28, button_font, PURPLE, center=True)
                draw_text(screen, f"{name} vs Computer", SCREEN_WIDTH // 2, btn_y + 58, small_font, DARK_GRAY, center=True)

        back_rect = pygame.Rect(250, 480, 200, 45)
        if back_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, RED, back_rect, border_radius=8)
            draw_text(screen, "Back", SCREEN_WIDTH // 2, 502, button_font, WHITE, center=True)
        else:
            pygame.draw.rect(screen, RED, back_rect, width=2, border_radius=8)
            draw_text(screen, "Back", SCREEN_WIDTH // 2, 502, button_font, RED, center=True)

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, name in btn_rects:
                    if rect.collidepoint(event.pos):
                        return name
                if back_rect.collidepoint(event.pos):
                    return None

    return None


def game_menu(screen, player1: str, player2: str):
    """Display game selection menu. Returns game name or 'quit'."""
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("Arial", 42, bold=True)
    subtitle_font = pygame.font.SysFont("Arial", 22)
    button_font = pygame.font.SysFont("Arial", 28, bold=True)
    small_font = pygame.font.SysFont("Arial", 18)

    games = [
        {"name": "Tic-Tac-Toe", "desc": "10x10 board, 5 in a row", "color": BLUE},
        {"name": "Tic-Tac-Toe vs AI", "desc": "Challenge the computer!", "color": PURPLE},
        {"name": "Othello", "desc": "8x8 Reversi board", "color": GREEN},
        {"name": "Connect Four", "desc": "7x7 grid, 4 in a row", "color": RED},
    ]

    sort_options = ["wins", "losses", "ratio"]
    sort_labels = ["Sort by Wins", "Sort by Losses", "Sort by W/L Ratio"]

    while True:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(WHITE)

        draw_text(screen, "Mini Game Hub", SCREEN_WIDTH // 2, 60, title_font, DARK_GRAY, center=True)
        draw_text(screen, f"Player 1: {player1}  |  Player 2: {player2}",
                  SCREEN_WIDTH // 2, 110, subtitle_font, BLUE, center=True)

        button_rects = []
        for i, game in enumerate(games):
            btn_y = 150 + i * 85
            btn_rect = pygame.Rect(150, btn_y, 400, 70)
            button_rects.append((btn_rect, game["name"]))

            if btn_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, game["color"], btn_rect, border_radius=12)
                draw_text(screen, game["name"], SCREEN_WIDTH // 2, btn_y + 22, button_font, WHITE, center=True)
                draw_text(screen, game["desc"], SCREEN_WIDTH // 2, btn_y + 50, small_font, WHITE, center=True)
            else:
                pygame.draw.rect(screen, game["color"], btn_rect, width=3, border_radius=12)
                draw_text(screen, game["name"], SCREEN_WIDTH // 2, btn_y + 22, button_font, game["color"], center=True)
                draw_text(screen, game["desc"], SCREEN_WIDTH // 2, btn_y + 50, small_font, DARK_GRAY, center=True)

        draw_text(screen, "View Leaderboard:", SCREEN_WIDTH // 2, 505, subtitle_font, DARK_GRAY, center=True)
        sort_rects = []
        for i, (opt, label) in enumerate(zip(sort_options, sort_labels)):
            sx = 100 + i * 200
            sr = pygame.Rect(sx, 530, 170, 35)
            sort_rects.append((sr, opt))
            if sr.collidepoint(mouse_pos):
                pygame.draw.rect(screen, TEAL, sr, border_radius=8)
                draw_text(screen, label, sx + 85, 547, small_font, WHITE, center=True)
            else:
                pygame.draw.rect(screen, TEAL, sr, width=2, border_radius=8)
                draw_text(screen, label, sx + 85, 547, small_font, TEAL, center=True)

        quit_rect = pygame.Rect(280, 580, 140, 40)
        if quit_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, RED, quit_rect, border_radius=8)
            draw_text(screen, "Quit", SCREEN_WIDTH // 2, 600, button_font, WHITE, center=True)
        else:
            pygame.draw.rect(screen, RED, quit_rect, width=2, border_radius=8)
            draw_text(screen, "Quit", SCREEN_WIDTH // 2, 600, button_font, RED, center=True)

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, name in button_rects:
                    if rect.collidepoint(event.pos):
                        return name
                for rect, opt in sort_rects:
                    if rect.collidepoint(event.pos):
                        call_leaderboard(opt)
                if quit_rect.collidepoint(event.pos):
                    return "quit"

    return "quit"


def post_game_screen(screen, winner: str, loser: str, game_name: str):
    """Show post-game screen. Returns True to play again, False to quit."""
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("Arial", 36, bold=True)
    body_font = pygame.font.SysFont("Arial", 24)
    button_font = pygame.font.SysFont("Arial", 26, bold=True)

    stats_img_path = show_visualizations()
    stats_surface = None
    if stats_img_path and os.path.exists(stats_img_path):
        try:
            stats_surface = pygame.image.load(stats_img_path)
            img_w, img_h = stats_surface.get_size()
            scale = min(650 / img_w, 300 / img_h)
            new_w, new_h = int(img_w * scale), int(img_h * scale)
            stats_surface = pygame.transform.scale(stats_surface, (new_w, new_h))
        except Exception:
            stats_surface = None

    while True:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(WHITE)

        if winner == "draw":
            draw_text(screen, f"{game_name} - It's a Draw!", SCREEN_WIDTH // 2, 40, title_font, ORANGE, center=True)
        else:
            draw_text(screen, f"{game_name} - {winner} Wins!", SCREEN_WIDTH // 2, 40, title_font, GREEN, center=True)

        if stats_surface:
            img_rect = stats_surface.get_rect(center=(SCREEN_WIDTH // 2, 250))
            screen.blit(stats_surface, img_rect)
        else:
            draw_text(screen, "No statistics available yet.", SCREEN_WIDTH // 2, 250, body_font, DARK_GRAY, center=True)

        again_rect = pygame.Rect(120, 440, 200, 50)
        if again_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, GREEN, again_rect, border_radius=10)
            draw_text(screen, "Play Again", 220, 465, button_font, WHITE, center=True)
        else:
            pygame.draw.rect(screen, GREEN, again_rect, width=3, border_radius=10)
            draw_text(screen, "Play Again", 220, 465, button_font, GREEN, center=True)

        quit_rect = pygame.Rect(380, 440, 200, 50)
        if quit_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, RED, quit_rect, border_radius=10)
            draw_text(screen, "Quit", 480, 465, button_font, WHITE, center=True)
        else:
            pygame.draw.rect(screen, RED, quit_rect, width=3, border_radius=10)
            draw_text(screen, "Quit", 480, 465, button_font, RED, center=True)

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if again_rect.collidepoint(event.pos):
                    return True
                if quit_rect.collidepoint(event.pos):
                    return False

    return False


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 game.py <username1> <username2>")
        sys.exit(1)

    player1 = sys.argv[1]
    player2 = sys.argv[2]
    ensure_history_file()

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Mini Game Hub")

    playing = True
    while playing:
        pygame.event.clear()
        choice = game_menu(screen, player1, player2)

        if choice == "quit":
            break

        winner, loser = None, None
        game_record_name = choice

        if choice == "Tic-Tac-Toe":
            game = TicTacToe(player1, player2, vs_ai=False)
            winner, loser = game.run()
        elif choice == "Tic-Tac-Toe vs AI":
            pygame.event.clear()
            chosen_player = ai_player_select(screen, player1, player2)
            if chosen_player is None:
                continue
            game = TicTacToe(chosen_player, "Computer", vs_ai=True)
            winner, loser = game.run()
            game_record_name = "Tic-Tac-Toe"
        elif choice == "Othello":
            game = Othello(player1, player2)
            winner, loser = game.run()
        elif choice == "Connect Four":
            game = ConnectFour(player1, player2)
            winner, loser = game.run()

        if winner is not None:
            record_result(winner, loser, game_record_name)
            call_leaderboard("wins")

        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mini Game Hub")

        if winner is not None:
            pygame.event.clear()
            playing = post_game_screen(screen, winner, loser, game_record_name)
        else:
            playing = False

    pygame.quit()
    print("Thanks for playing Mini Game Hub!")
    sys.exit(0)


if __name__ == "__main__":
    main()
