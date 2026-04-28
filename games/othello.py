"""
Othello (Reversi) -- an 8x8 disc-flipping board game.

Two players (black and white) take turns placing discs.  A move is legal
only when it traps one or more opponent discs in a straight line between
the newly placed disc and an existing friendly disc.  All trapped discs
are flipped.  The game ends when neither player can move; the player with
more discs wins.
"""

from __future__ import annotations

import sys
import numpy as np
import pygame
from games.base_game import BoardGame

# ---------------------------------------------------------------------------
# 8 compass directions used for line scanning (row_delta, col_delta)
# ---------------------------------------------------------------------------
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),          ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1),
]

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
BOARD_GREEN  = (34, 139, 34)
LINE_COLOUR  = (0, 0, 0)
BLACK_DISC   = (10, 10, 10)
WHITE_DISC   = (240, 240, 240)
HINT_COLOUR  = (180, 180, 180, 160)   # translucent grey for valid-move dots
BG_COLOUR    = (30, 30, 30)
TEXT_COLOUR  = (255, 255, 255)
SCORE_P1     = (60, 60, 60)           # dark badge behind black's score
SCORE_P2     = (200, 200, 200)        # light badge behind white's score


class Othello(BoardGame):
    """Full Othello (Reversi) game with a Pygame GUI."""

    # Board / window geometry
    BOARD_SIZE   = 8
    CELL_SIZE    = 80                  # pixels per cell
    BOARD_PX     = CELL_SIZE * BOARD_SIZE  # 640 px
    MARGIN       = 30                  # left/top margin so the board is centred
    INFO_HEIGHT  = 110                 # space below the board for scores / status
    WIN_W        = BOARD_PX + 2 * MARGIN       # ~700
    WIN_H        = BOARD_PX + 2 * MARGIN + INFO_HEIGHT  # ~750
    UNDO_W       = 96
    UNDO_H       = 36

    # ------------------------------------------------------------------ init
    def __init__(self, player1: str, player2: str) -> None:
        # Initialise the base class with an 8x8 board
        super().__init__(player1, player2, self.BOARD_SIZE, self.BOARD_SIZE, "Othello")

        # Place the four starting discs in the centre (standard Othello layout)
        # Black (1) on d5/e4, White (2) on d4/e5  (0-indexed: row 3-4, col 3-4)
        self.board[3][3] = 2  # white
        self.board[3][4] = 1  # black
        self.board[4][3] = 1  # black
        self.board[4][4] = 2  # white

    # -------------------------------------------------- move-validation logic

    def _discs_to_flip(self, row: int, col: int, player: int) -> list[tuple[int, int]]:
        """Return a list of all opponent disc positions that would be flipped
        if *player* places a disc at (row, col).  An empty list means the
        move is invalid."""
        # The cell must be empty for a move to be possible
        if self.board[row][col] != 0:
            return []

        opponent = 2 if player == 1 else 1
        flips: list[tuple[int, int]] = []

        # Scan every direction from the candidate cell
        for dr, dc in DIRECTIONS:
            candidates: list[tuple[int, int]] = []
            r, c = row + dr, col + dc

            # Walk along opponent discs
            while 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and self.board[r][c] == opponent:
                candidates.append((r, c))
                r += dr
                c += dc

            # If the line ends with one of our own discs, all candidates flip
            if candidates and 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and self.board[r][c] == player:
                flips.extend(candidates)

        return flips

    def get_valid_moves(self, player: int) -> dict[tuple[int, int], list[tuple[int, int]]]:
        """Return a dict mapping each valid (row, col) to its flip list for
        the given *player*."""
        moves: dict[tuple[int, int], list[tuple[int, int]]] = {}
        for r in range(self.BOARD_SIZE):
            for c in range(self.BOARD_SIZE):
                flips = self._discs_to_flip(r, c, player)
                if flips:
                    moves[(r, c)] = flips
        return moves

    def make_move(self, row: int, col: int) -> bool:
        """Place a disc for the current player and flip trapped opponents.
        Returns True if the move was successfully applied."""
        flips = self._discs_to_flip(row, col, self.current_player)
        if not flips:
            return False  # illegal move

        # Place the new disc
        self.board[row][col] = self.current_player

        # Flip all trapped discs
        for r, c in flips:
            self.board[r][c] = self.current_player

        return True

    # --------------------------------------------- win / game-over detection

    def check_win(self) -> int:
        """Use numpy operations (no manual loops) to count discs and decide
        the winner.

        Returns 0 while the game is still in progress, 1 if player 1 (black)
        wins, 2 if player 2 (white) wins, or -1 for a draw."""

        # If either player can still move, the game isn't over yet
        if self.get_valid_moves(1) or self.get_valid_moves(2):
            return 0

        # --- numpy-based disc counting (no loops) ---
        black_count: int = int(np.count_nonzero(self.board == 1))
        white_count: int = int(np.count_nonzero(self.board == 2))

        if black_count > white_count:
            return 1   # player 1 (black) wins
        elif white_count > black_count:
            return 2   # player 2 (white) wins
        else:
            return -1  # exact tie

    def _get_scores(self) -> tuple[int, int]:
        """Return (black_count, white_count) using numpy -- no manual loops."""
        black = int(np.sum(self.board == 1))
        white = int(np.sum(self.board == 2))
        return black, white

    # --------------------------------------------------------- Pygame drawing

    def _draw_board(self, surface: pygame.Surface) -> None:
        """Render the green board, grid lines, and all discs."""
        mx, my = self.MARGIN, self.MARGIN  # offset so the board is centred

        # Fill the board area with green
        pygame.draw.rect(
            surface, BOARD_GREEN,
            (mx, my, self.BOARD_PX, self.BOARD_PX),
        )

        # Draw grid lines
        for i in range(self.BOARD_SIZE + 1):
            # Horizontal
            pygame.draw.line(
                surface, LINE_COLOUR,
                (mx, my + i * self.CELL_SIZE),
                (mx + self.BOARD_PX, my + i * self.CELL_SIZE),
                2,
            )
            # Vertical
            pygame.draw.line(
                surface, LINE_COLOUR,
                (mx + i * self.CELL_SIZE, my),
                (mx + i * self.CELL_SIZE, my + self.BOARD_PX),
                2,
            )

        # Draw discs currently on the board
        radius = self.CELL_SIZE // 2 - 4
        for r in range(self.BOARD_SIZE):
            for c in range(self.BOARD_SIZE):
                if self.board[r][c] == 1:
                    colour = BLACK_DISC
                elif self.board[r][c] == 2:
                    colour = WHITE_DISC
                else:
                    continue
                cx = mx + c * self.CELL_SIZE + self.CELL_SIZE // 2
                cy = my + r * self.CELL_SIZE + self.CELL_SIZE // 2
                pygame.draw.circle(surface, colour, (cx, cy), radius)

    def _draw_hints(self, surface: pygame.Surface, valid_moves: dict) -> None:
        """Draw small dots on cells where the current player may move."""
        mx, my = self.MARGIN, self.MARGIN
        dot_radius = 6
        for (r, c) in valid_moves:
            cx = mx + c * self.CELL_SIZE + self.CELL_SIZE // 2
            cy = my + r * self.CELL_SIZE + self.CELL_SIZE // 2
            pygame.draw.circle(surface, HINT_COLOUR[:3], (cx, cy), dot_radius)

    def _undo_button_rect(self) -> pygame.Rect:
        """Return the fixed rectangle used for the one-step undo button."""
        return pygame.Rect(
            self.WIN_W - self.UNDO_W - self.MARGIN,
            self.WIN_H - self.UNDO_H - 14,
            self.UNDO_W,
            self.UNDO_H,
        )

    def _draw_undo_button(self, surface: pygame.Surface, enabled: bool) -> None:
        """Draw the one-step undo button in the lower-right info area."""
        rect = self._undo_button_rect()
        fill = (76, 175, 80) if enabled else (105, 105, 105)
        text_colour = WHITE_DISC if enabled else (200, 200, 200)
        pygame.draw.rect(surface, fill, rect, border_radius=8)
        pygame.draw.rect(surface, TEXT_COLOUR, rect, width=2, border_radius=8)

        font = pygame.font.SysFont("Arial", 18, bold=True)
        label = font.render("Undo", True, text_colour)
        surface.blit(
            label,
            (
                rect.x + (rect.width - label.get_width()) // 2,
                rect.y + (rect.height - label.get_height()) // 2,
            ),
        )

    def _draw_info(
        self,
        surface: pygame.Surface,
        valid_moves: dict,
        game_over: bool,
        winner: int,
        undo_enabled: bool,
    ) -> None:
        """Draw the score bar and status text below the board."""
        font_big   = pygame.font.SysFont("Arial", 28, bold=True)
        font_small = pygame.font.SysFont("Arial", 22)

        black_score, white_score = self._get_scores()

        # Y position for the info panel (just below the board)
        info_y = self.MARGIN + self.BOARD_PX + 12

        # --- Player 1 (black) score on the left ---
        p1_label = font_small.render(f"{self.player1_name} (Black)", True, TEXT_COLOUR)
        p1_score = font_big.render(str(black_score), True, TEXT_COLOUR)
        surface.blit(p1_label, (self.MARGIN, info_y))
        surface.blit(p1_score, (self.MARGIN, info_y + 28))

        # --- Player 2 (white) score on the right ---
        p2_label = font_small.render(f"{self.player2_name} (White)", True, TEXT_COLOUR)
        p2_score = font_big.render(str(white_score), True, TEXT_COLOUR)
        # Right-align
        p2_label_x = self.WIN_W - self.MARGIN - p2_label.get_width()
        p2_score_x = self.WIN_W - self.MARGIN - p2_score.get_width()
        surface.blit(p2_label, (p2_label_x, info_y))
        surface.blit(p2_score, (p2_score_x, info_y + 28))

        # --- Status line (centred) ---
        if game_over:
            if winner == -1:
                status_text = "Draw!  Click or press ESC to continue"
            elif winner == 1:
                status_text = f"{self.player1_name} wins!  Click or press ESC to continue"
            else:
                status_text = f"{self.player2_name} wins!  Click or press ESC to continue"
        else:
            name = self.get_current_player_name()
            colour_label = "Black" if self.current_player == 1 else "White"
            if valid_moves:
                status_text = f"{name}'s turn ({colour_label})"
            else:
                # Current player has no moves -- turn will be skipped
                status_text = f"{name} ({colour_label}) has no moves -- skipping"

        status_surf = font_small.render(status_text, True, TEXT_COLOUR)
        sx = max(12, (self._undo_button_rect().left - status_surf.get_width()) // 2)
        surface.blit(status_surf, (sx, info_y + 66))
        self._draw_undo_button(surface, undo_enabled)

    # ------------------------------------------------------------ main loop

    def run(self) -> tuple[str, str]:
        """Run the Pygame event loop and return the result.

        Returns
        -------
        tuple[str, str]
            (winner_name, loser_name) or ("draw", "draw").
        """
        screen = pygame.display.set_mode((self.WIN_W, self.WIN_H))
        pygame.display.set_caption("Othello")
        clock = pygame.time.Clock()

        game_over = False
        winner = 0          # 0 = ongoing, 1 / 2 = winner, -1 = draw
        skip_delay = 0      # countdown frames when a turn is auto-skipped
        undo_rect = self._undo_button_rect()

        def undo_last_move() -> bool:
            nonlocal game_over, winner, skip_delay
            state = self.restore_undo_state()
            if state is None:
                return False

            game_over = bool(state["game_over"])
            winner = int(state["winner"])
            skip_delay = int(state["skip_delay"])
            return True

        running = True
        while running:
            # Compute valid moves for the current player each frame
            valid_moves = self.get_valid_moves(self.current_player) if not game_over else {}

            # --- handle events ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_u and undo_last_move():
                        continue
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        break

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if undo_rect.collidepoint(event.pos):
                        undo_last_move()
                        continue

                # Any key or click after game over returns to menu
                if game_over and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    running = False
                    break

                # Only process clicks when the game is still going and not
                # in the middle of a skip-delay animation.
                if event.type == pygame.MOUSEBUTTONDOWN and not game_over and skip_delay == 0:
                    mx_off, my_off = self.MARGIN, self.MARGIN
                    x, y = event.pos
                    # Convert pixel position to board coordinates
                    col = (x - mx_off) // self.CELL_SIZE
                    row = (y - my_off) // self.CELL_SIZE

                    # Bounds check
                    if 0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE:
                        if (row, col) in valid_moves:
                            self.remember_undo_state(
                                game_over=game_over,
                                winner=winner,
                                skip_delay=skip_delay,
                            )
                            self.make_move(row, col)

                            # Check whether the game has ended
                            winner = self.check_win()
                            if winner != 0:
                                game_over = True
                            else:
                                # Switch turn to the other player
                                self.switch_turn()

                                # If the next player also has no moves, skip
                                # back (handled below via skip_delay).
                                next_moves = self.get_valid_moves(self.current_player)
                                if not next_moves:
                                    # This player must pass; set a short visual
                                    # delay so the user sees the "no moves" text
                                    skip_delay = 45  # ~0.75 s at 60 fps

            # --- auto-skip logic ---
            if skip_delay > 0 and not game_over:
                skip_delay -= 1
                if skip_delay == 0:
                    # Skip the current player's turn
                    self.switch_turn()

                    # Re-check: if STILL no moves for the new player, game over
                    winner = self.check_win()
                    if winner != 0:
                        game_over = True

            # --- drawing ---
            screen.fill(BG_COLOUR)
            self._draw_board(screen)

            # Only show move hints when it's a human's turn and game is active
            if not game_over and skip_delay == 0:
                self._draw_hints(screen, valid_moves)

            self._draw_info(screen, valid_moves, game_over, winner, self.has_undo())
            pygame.display.flip()
            clock.tick(60)

        # --- build result tuple ---
        if winner == 1:
            return (self.player1_name, self.player2_name)
        elif winner == 2:
            return (self.player2_name, self.player1_name)
        else:
            # Draw, or the window was closed before a conclusion
            return ("draw", "draw")
