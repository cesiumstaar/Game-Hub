#!/usr/bin/env python3
"""
game.py - Main game engine for Mini Game Hub
Receives two authenticated usernames from main.sh and manages:
- Game selection menu (Pygame GUI)
- Launching selected games
- Recording results to history.csv
- Calling leaderboard.sh for stats display
- Displaying Matplotlib visualizations
- Post-game loop (play again or quit)
"""

import sys
import os
import csv
import subprocess
from datetime import datetime
from collections import Counter
from pathlib import Path

import pygame
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to avoid conflicts with pygame
import matplotlib.pyplot as plt

# Import game classes from games package
from games.tictactoe import TicTacToe
from games.othello import Othello
from games.connect4 import ConnectFour

# ---- Constants ----
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 600
FPS = 60

# Color definitions
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

# Paths
SCRIPT_DIR = Path(__file__).parent.resolve()
HISTORY_FILE = SCRIPT_DIR / "history.csv"
LEADERBOARD_SCRIPT = SCRIPT_DIR / "leaderboard.sh"


def ensure_history_file():
    """Create history.csv with header if it doesn't exist."""
    if not HISTORY_FILE.exists():
        with open(HISTORY_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Winner", "Loser", "Date", "Game"])


def record_result(winner: str, loser: str, game_name: str):
    """Append a game result row to history.csv."""
    ensure_history_file()
    with open(HISTORY_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([winner, loser, date_str, game_name])


def call_leaderboard(sort_metric: str = "wins"):
    """Call leaderboard.sh to display stats in terminal."""
    if LEADERBOARD_SCRIPT.exists():
        try:
            subprocess.run(
                ["bash", str(LEADERBOARD_SCRIPT), str(HISTORY_FILE), sort_metric],
                cwd=str(SCRIPT_DIR)
            )
        except Exception as e:
            print(f"Error calling leaderboard: {e}")


def show_visualizations():
    """Display Matplotlib charts: top 5 players bar chart and most played games pie chart."""
    if not HISTORY_FILE.exists():
        return

    # Read history data
    winners = []
    games_played = []
    with open(HISTORY_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Winner"] != "draw":
                winners.append(row["Winner"])
            games_played.append(row["Game"])

    if not winners and not games_played:
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Game Hub Statistics", fontsize=16, fontweight="bold")

    # Bar chart - Top 5 Players by total win count
    if winners:
        win_counts = Counter(winners)
        top5 = win_counts.most_common(5)
        names = [item[0] for item in top5]
        counts = [item[1] for item in top5]
        colors = [BLUE, GREEN, RED, ORANGE, PURPLE][:len(names)]
        # Normalize colors to 0-1 range for matplotlib
        colors_norm = [(r/255, g/255, b/255) for r, g, b in colors]
        axes[0].bar(names, counts, color=colors_norm)
        axes[0].set_title("Top 5 Players by Wins")
        axes[0].set_xlabel("Player")
        axes[0].set_ylabel("Wins")
        axes[0].set_ylim(bottom=0)
    else:
        axes[0].text(0.5, 0.5, "No wins recorded yet", ha="center", va="center")
        axes[0].set_title("Top 5 Players by Wins")

    # Pie chart - Most Played Games by frequency
    if games_played:
        game_counts = Counter(games_played)
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

    # Display the saved chart image in pygame
    return str(SCRIPT_DIR / "stats.png")


def draw_text(screen, text, x, y, font, color=BLACK, center=False):
    """Helper to render text on a pygame surface."""
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surface, rect)
    return rect


def game_menu(screen, player1: str, player2: str):
    """
    Display the game selection menu with Pygame GUI.
    Returns the selected game name string or 'quit'.
    """
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("Arial", 42, bold=True)
    subtitle_font = pygame.font.SysFont("Arial", 22)
    button_font = pygame.font.SysFont("Arial", 28, bold=True)
    small_font = pygame.font.SysFont("Arial", 18)

    # Define game buttons
    games = [
        {"name": "Tic-Tac-Toe", "desc": "10x10 board, 5 in a row", "color": BLUE},
        {"name": "Othello", "desc": "8x8 Reversi board", "color": GREEN},
        {"name": "Connect Four", "desc": "7x7 grid, 4 in a row", "color": RED},
    ]

    # Leaderboard sort options
    sort_options = ["wins", "losses", "ratio"]
    sort_labels = ["Sort by Wins", "Sort by Losses", "Sort by W/L Ratio"]

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(WHITE)

        # Title
        draw_text(screen, "Mini Game Hub", SCREEN_WIDTH // 2, 60, title_font, DARK_GRAY, center=True)
        draw_text(screen, f"Player 1: {player1}  |  Player 2: {player2}",
                  SCREEN_WIDTH // 2, 110, subtitle_font, BLUE, center=True)

        # Game buttons
        button_rects = []
        for i, game in enumerate(games):
            btn_y = 180 + i * 100
            btn_rect = pygame.Rect(150, btn_y, 400, 75)
            button_rects.append((btn_rect, game["name"]))

            # Hover effect
            if btn_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, game["color"], btn_rect, border_radius=12)
                draw_text(screen, game["name"], SCREEN_WIDTH // 2, btn_y + 25, button_font, WHITE, center=True)
                draw_text(screen, game["desc"], SCREEN_WIDTH // 2, btn_y + 55, small_font, WHITE, center=True)
            else:
                pygame.draw.rect(screen, game["color"], btn_rect, width=3, border_radius=12)
                draw_text(screen, game["name"], SCREEN_WIDTH // 2, btn_y + 25, button_font, game["color"], center=True)
                draw_text(screen, game["desc"], SCREEN_WIDTH // 2, btn_y + 55, small_font, DARK_GRAY, center=True)

        # Leaderboard sort buttons
        draw_text(screen, "View Leaderboard:", SCREEN_WIDTH // 2, 500, subtitle_font, DARK_GRAY, center=True)
        sort_rects = []
        for i, (opt, label) in enumerate(zip(sort_options, sort_labels)):
            sx = 100 + i * 200
            sr = pygame.Rect(sx, 525, 170, 35)
            sort_rects.append((sr, opt))
            if sr.collidepoint(mouse_pos):
                pygame.draw.rect(screen, TEAL, sr, border_radius=8)
                draw_text(screen, label, sx + 85, 542, small_font, WHITE, center=True)
            else:
                pygame.draw.rect(screen, TEAL, sr, width=2, border_radius=8)
                draw_text(screen, label, sx + 85, 542, small_font, TEAL, center=True)

        # Quit button
        quit_rect = pygame.Rect(280, 575, 140, 40)
        if quit_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, RED, quit_rect, border_radius=8)
            draw_text(screen, "Quit", SCREEN_WIDTH // 2, 595, button_font, WHITE, center=True)
        else:
            pygame.draw.rect(screen, RED, quit_rect, width=2, border_radius=8)
            draw_text(screen, "Quit", SCREEN_WIDTH // 2, 595, button_font, RED, center=True)

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check game buttons
                for rect, name in button_rects:
                    if rect.collidepoint(event.pos):
                        return name
                # Check sort buttons
                for rect, opt in sort_rects:
                    if rect.collidepoint(event.pos):
                        call_leaderboard(opt)
                # Check quit
                if quit_rect.collidepoint(event.pos):
                    return "quit"

    return "quit"


def post_game_screen(screen, winner: str, loser: str, game_name: str):
    """
    Show post-game screen with result, stats image, and play again / quit options.
    Returns True to play again, False to quit.
    """
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("Arial", 36, bold=True)
    body_font = pygame.font.SysFont("Arial", 24)
    button_font = pygame.font.SysFont("Arial", 26, bold=True)

    # Generate stats image
    stats_img_path = show_visualizations()
    stats_surface = None
    if stats_img_path and os.path.exists(stats_img_path):
        try:
            stats_surface = pygame.image.load(stats_img_path)
            # Scale to fit the screen
            img_w, img_h = stats_surface.get_size()
            scale = min(650 / img_w, 300 / img_h)
            new_w, new_h = int(img_w * scale), int(img_h * scale)
            stats_surface = pygame.transform.scale(stats_surface, (new_w, new_h))
        except Exception:
            stats_surface = None

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(WHITE)

        # Result text
        if winner == "draw":
            draw_text(screen, f"{game_name} - It's a Draw!", SCREEN_WIDTH // 2, 40, title_font, ORANGE, center=True)
        else:
            draw_text(screen, f"{game_name} - {winner} Wins!", SCREEN_WIDTH // 2, 40, title_font, GREEN, center=True)

        # Stats image
        if stats_surface:
            img_rect = stats_surface.get_rect(center=(SCREEN_WIDTH // 2, 250))
            screen.blit(stats_surface, img_rect)
        else:
            draw_text(screen, "No statistics available yet.", SCREEN_WIDTH // 2, 250, body_font, DARK_GRAY, center=True)

        # Play Again button
        again_rect = pygame.Rect(120, 440, 200, 50)
        if again_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, GREEN, again_rect, border_radius=10)
            draw_text(screen, "Play Again", 220, 465, button_font, WHITE, center=True)
        else:
            pygame.draw.rect(screen, GREEN, again_rect, width=3, border_radius=10)
            draw_text(screen, "Play Again", 220, 465, button_font, GREEN, center=True)

        # Quit button
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
    """Main entry point - validates args, runs game loop."""
    # Validate command line arguments
    if len(sys.argv) != 3:
        print("Usage: python3 game.py <username1> <username2>")
        sys.exit(1)

    player1 = sys.argv[1]
    player2 = sys.argv[2]

    # Ensure history file exists
    ensure_history_file()

    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Mini Game Hub")

    # Main game loop
    playing = True
    while playing:
        # Show game selection menu
        choice = game_menu(screen, player1, player2)

        if choice == "quit":
            break

        # Launch the selected game
        winner, loser = None, None
        if choice == "Tic-Tac-Toe":
            game = TicTacToe(player1, player2)
            winner, loser = game.run()
        elif choice == "Othello":
            game = Othello(player1, player2)
            winner, loser = game.run()
        elif choice == "Connect Four":
            game = ConnectFour(player1, player2)
            winner, loser = game.run()

        # Record the result if a game was played
        if winner is not None:
            record_result(winner, loser, choice)
            # Call leaderboard in terminal
            call_leaderboard("wins")

        # Resize screen back for menu/post-game
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mini Game Hub")

        # Post-game screen with stats
        if winner is not None:
            playing = post_game_screen(screen, winner, loser, choice)
        else:
            # Game was closed without finishing
            playing = False

    # Clean shutdown
    pygame.quit()
    print("Thanks for playing Mini Game Hub!")
    sys.exit(0)


if __name__ == "__main__":
    main()
