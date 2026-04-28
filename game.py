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
import subprocess
from datetime import datetime
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
SCREEN_HEIGHT = 640
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
        with open(HISTORY_FILE, "w") as f:
            f.write("Winner,Loser,Date,Game\n")


def record_result(winner: str, loser: str, game_name: str):
    """Append a game result row to history.csv."""
    ensure_history_file()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{winner},{loser},{date_str},{game_name}\n")


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


def _short_label(text: str, max_len: int = 16) -> str:
    """Shorten long labels so they stay readable in charts and stat cards."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def load_stats_data() -> dict[str, object] | None:
    """Load history.csv and return aggregated winner/game statistics."""
    if not HISTORY_FILE.exists():
        return None

    winners = []
    games_played = []
    with open(HISTORY_FILE, "r") as f:
        lines = f.read().splitlines()

    for line in lines[1:]:  # skip header row
        if not line.strip():
            continue
        parts = line.split(",")
        if len(parts) < 4:
            continue
        winner_val = parts[0]
        game_val = parts[3]
        if winner_val != "draw":
            winners.append(winner_val)
        games_played.append(game_val)

    if not winners and not games_played:
        return None

    win_counts: dict[str, int] = {}
    for w in winners:
        win_counts[w] = win_counts.get(w, 0) + 1

    game_counts: dict[str, int] = {}
    for gp in games_played:
        game_counts[gp] = game_counts.get(gp, 0) + 1

    return {
        "winners": winners,
        "games_played": games_played,
        "win_counts": win_counts,
        "game_counts": game_counts,
    }


def show_visualizations(stats_data: dict[str, object] | None = None):
    """Create a compact, post-game-friendly statistics image."""
    stats_data = stats_data or load_stats_data()
    if not stats_data:
        return None

    winners = stats_data["winners"]
    games_played = stats_data["games_played"]
    win_counts = stats_data["win_counts"]
    game_counts = stats_data["game_counts"]

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(10.5, 4.1),
        dpi=140,
        constrained_layout=True,
    )
    fig.patch.set_facecolor("white")

    for ax in axes:
        ax.set_facecolor("#fafafa")

    if winners:
        top5 = sorted(win_counts.items(), key=lambda x: (-x[1], x[0]))[:5]
        top5.reverse()
        names = [_short_label(item[0], 14) for item in top5]
        counts = [item[1] for item in top5]
        colors = [BLUE, GREEN, RED, ORANGE, PURPLE][:len(names)]
        colors.reverse()
        colors_norm = [(r/255, g/255, b/255) for r, g, b in colors]
        bars = axes[0].barh(names, counts, color=colors_norm)
        for bar, count in zip(bars, counts):
            axes[0].text(
                bar.get_width() + 0.08,
                bar.get_y() + bar.get_height() / 2,
                str(count),
                va="center",
                fontsize=10,
                color="#2f2f2f",
                fontweight="bold",
            )
        axes[0].set_title("Top Winners", fontsize=12, fontweight="bold")
        axes[0].set_xlabel("Wins", fontsize=10)
        axes[0].tick_params(axis="both", labelsize=10)
        axes[0].grid(axis="x", linestyle="--", alpha=0.25)
        axes[0].set_axisbelow(True)
        axes[0].set_xlim(0, max(counts) + max(1, int(max(counts) * 0.35)))
        axes[0].spines["top"].set_visible(False)
        axes[0].spines["right"].set_visible(False)
    else:
        axes[0].text(
            0.5,
            0.5,
            "No wins recorded yet",
            ha="center",
            va="center",
            fontsize=12,
            color="#4a4a4a",
        )
        axes[0].set_title("Top Winners", fontsize=12, fontweight="bold")
        axes[0].set_xticks([])
        axes[0].set_yticks([])

    if games_played:
        top_games = sorted(game_counts.items(), key=lambda x: (-x[1], x[0]))[:5]
        labels = [_short_label(item[0], 14) for item in top_games]
        sizes = [item[1] for item in top_games]
        pie_colors = [(r/255, g/255, b/255) for r, g, b in
                      [BLUE, GREEN, RED, ORANGE, PURPLE, TEAL][:len(labels)]]
        wedges, _, autotexts = axes[1].pie(
            sizes,
            colors=pie_colors,
            startangle=90,
            autopct=lambda pct: f"{pct:.0f}%" if pct >= 8 else "",
            pctdistance=0.72,
            wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 2},
            textprops={"fontsize": 10, "color": "#2f2f2f", "fontweight": "bold"},
        )
        for autotext in autotexts:
            autotext.set_color("#2f2f2f")
        legend_labels = [f"{label} ({count})" for label, count in zip(labels, sizes)]
        axes[1].legend(
            wedges,
            legend_labels,
            loc="center left",
            bbox_to_anchor=(0.88, 0.5),
            frameon=False,
            fontsize=9,
        )
        axes[1].set_title("Most Played Games", fontsize=12, fontweight="bold")
        axes[1].set_aspect("equal")
    else:
        axes[1].text(
            0.5,
            0.5,
            "No games played yet",
            ha="center",
            va="center",
            fontsize=12,
            color="#4a4a4a",
        )
        axes[1].set_title("Most Played Games", fontsize=12, fontweight="bold")
        axes[1].set_xticks([])
        axes[1].set_yticks([])

    plt.savefig(
        str(SCRIPT_DIR / "stats.png"),
        dpi=140,
        bbox_inches="tight",
        pad_inches=0.18,
    )
    plt.close()

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


def draw_stat_card(
    screen,
    rect: pygame.Rect,
    label: str,
    value: str,
    accent,
    subtitle: str | None = None,
):
    """Render a compact stat card for the post-game summary."""
    pygame.draw.rect(screen, (250, 250, 250), rect, border_radius=14)
    pygame.draw.rect(screen, accent, rect, width=3, border_radius=14)

    label_font = pygame.font.SysFont("Arial", 16, bold=True)
    value_font = pygame.font.SysFont("Arial", 24, bold=True)
    sub_font = pygame.font.SysFont("Arial", 14)

    draw_text(screen, label, rect.centerx, rect.y + 18, label_font, accent, center=True)
    draw_text(screen, _short_label(value, 18), rect.centerx, rect.y + 47, value_font, DARK_GRAY, center=True)
    if subtitle:
        draw_text(screen, _short_label(subtitle, 22), rect.centerx, rect.y + 73, sub_font, DARK_GRAY, center=True)


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
    title_font = pygame.font.SysFont("Arial", 32, bold=True)
    subtitle_font = pygame.font.SysFont("Arial", 18)
    body_font = pygame.font.SysFont("Arial", 22)
    button_font = pygame.font.SysFont("Arial", 26, bold=True)

    stats_data = load_stats_data()
    win_counts = stats_data["win_counts"] if stats_data else {}
    game_counts = stats_data["game_counts"] if stats_data else {}
    games_played = stats_data["games_played"] if stats_data else []

    stats_img_path = show_visualizations(stats_data)
    stats_surface = None
    if stats_img_path and os.path.exists(stats_img_path):
        try:
            stats_surface = pygame.image.load(stats_img_path).convert_alpha()
            img_w, img_h = stats_surface.get_size()
            scale = min(620 / img_w, 250 / img_h)
            new_w, new_h = int(img_w * scale), int(img_h * scale)
            stats_surface = pygame.transform.smoothscale(stats_surface, (new_w, new_h))
        except Exception:
            stats_surface = None

    total_games = len(games_played)
    if win_counts:
        top_winner_name, top_winner_count = sorted(
            win_counts.items(), key=lambda x: (-x[1], x[0])
        )[0]
    else:
        top_winner_name, top_winner_count = ("No wins yet", 0)

    if game_counts:
        top_game_name, top_game_count = sorted(
            game_counts.items(), key=lambda x: (-x[1], x[0])
        )[0]
    else:
        top_game_name, top_game_count = ("No games yet", 0)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill((248, 248, 248))

        if winner == "draw":
            draw_text(screen, f"{game_name} - It's a Draw!", SCREEN_WIDTH // 2, 42, title_font, ORANGE, center=True)
        else:
            draw_text(screen, f"{game_name} - {winner} Wins!", SCREEN_WIDTH // 2, 42, title_font, GREEN, center=True)
        draw_text(
            screen,
            "Latest result plus lifetime hub stats",
            SCREEN_WIDTH // 2,
            82,
            subtitle_font,
            DARK_GRAY,
            center=True,
        )

        chart_rect = pygame.Rect(40, 112, 620, 250)
        pygame.draw.rect(screen, WHITE, chart_rect, border_radius=18)
        pygame.draw.rect(screen, LIGHT_GRAY, chart_rect, width=2, border_radius=18)
        if stats_surface:
            img_rect = stats_surface.get_rect(center=chart_rect.center)
            screen.blit(stats_surface, img_rect)
        else:
            draw_text(screen, "No statistics available yet.", SCREEN_WIDTH // 2, chart_rect.centery, body_font, DARK_GRAY, center=True)

        card_y = 386
        card_w = 180
        card_h = 96
        gap = 20
        start_x = 60
        total_rect = pygame.Rect(start_x, card_y, card_w, card_h)
        winner_rect = pygame.Rect(start_x + card_w + gap, card_y, card_w, card_h)
        game_rect = pygame.Rect(start_x + 2 * (card_w + gap), card_y, card_w, card_h)

        draw_stat_card(
            screen,
            total_rect,
            "Matches Played",
            str(total_games),
            TEAL,
            "Across all games",
        )
        draw_stat_card(
            screen,
            winner_rect,
            "Top Winner",
            top_winner_name,
            GREEN,
            f"{top_winner_count} win(s)",
        )
        draw_stat_card(
            screen,
            game_rect,
            "Most Played",
            top_game_name,
            ORANGE,
            f"{top_game_count} match(es)",
        )

        again_rect = pygame.Rect(110, 530, 210, 52)
        if again_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, GREEN, again_rect, border_radius=10)
            draw_text(screen, "Play Again", again_rect.centerx, again_rect.centery, button_font, WHITE, center=True)
        else:
            pygame.draw.rect(screen, GREEN, again_rect, width=3, border_radius=10)
            draw_text(screen, "Play Again", again_rect.centerx, again_rect.centery, button_font, GREEN, center=True)

        quit_rect = pygame.Rect(380, 530, 210, 52)
        if quit_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, RED, quit_rect, border_radius=10)
            draw_text(screen, "Quit", quit_rect.centerx, quit_rect.centery, button_font, WHITE, center=True)
        else:
            pygame.draw.rect(screen, RED, quit_rect, width=3, border_radius=10)
            draw_text(screen, "Quit", quit_rect.centerx, quit_rect.centery, button_font, RED, center=True)

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
        pygame.event.clear()
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
            pygame.event.clear()
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
