"""
10x10 Tic-Tac-Toe (5-in-a-row) with Pygame GUI.

Win detection uses pure NumPy operations -- no Python-level loops over
individual cells.  Player 1 places +1, Player 2 places -1; a window of
five cells that sums to +5 or -5 indicates a win.
"""
from __future__ import annotations

import numpy as np
import pygame

from games.base_game import BoardGame


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
BLUE   = (30,  80,  220)      # X marks (player 1)
RED    = (220, 40,  40)       # O marks (player 2)
GRAY   = (180, 180, 180)
GREEN  = (50,  200, 80)       # winning-line highlight
OVERLAY_BG = (240, 240, 240)  # game-over dialog background


# ---------------------------------------------------------------------------
# Game class
# ---------------------------------------------------------------------------
class TicTacToe(BoardGame):
    """
    10x10 Tic-Tac-Toe where 5 marks in a row wins.

    Inherits board state and turn logic from BoardGame.
    Adds Pygame rendering, click handling, and win highlighting.
    """

    # Board & win constants
    ROWS = 10
    COLS = 10
    WIN_LENGTH = 5

    # Layout constants
    BOARD_PX   = 700          # board area is 700x700 pixels
    STATUS_H   = 50           # status bar height below the board
    WINDOW_W   = BOARD_PX
    WINDOW_H   = BOARD_PX + STATUS_H
    CELL_PX    = BOARD_PX // COLS   # 70 px per cell
    MARK_PAD   = 12           # padding inside a cell for drawing marks
    LINE_WIDTH = 2            # grid line thickness
    UNDO_W     = 96
    UNDO_H     = 34

    def __init__(self, player1: str = "Player 1", player2: str = "Player 2") -> None:
        # Initialise the base class with a 10x10 board
        super().__init__(player1, player2, self.ROWS, self.COLS, "Tic-Tac-Toe 10x10")

        # Winning line coordinates (list of (row, col) tuples) -- filled
        # when a winner is detected so the GUI can highlight them.
        self._win_cells: list[tuple[int, int]] = []

    # ------------------------------------------------------------------
    # NumPy-only win detection
    # ------------------------------------------------------------------

    def check_win(self) -> int:
        """
        Check all possible 5-cell windows on the board using NumPy slicing.

        Strategy
        --------
        For each of the four directions (horizontal, vertical, and both
        diagonals) we extract every contiguous window of length 5 by
        slicing.  If the sum of any window equals +5, player 1 wins;
        if it equals -5, player 2 wins.

        Returns 0 if no winner yet, 1 for player 1, 2 for player 2.
        Also populates self._win_cells for the GUI highlight.
        """
        b = self.board
        n = self.WIN_LENGTH  # 5

        # --- Horizontal windows ---
        # For every row, slide a window of width n across the columns.
        # h_windows has shape (ROWS, COLS - n + 1, n).
        h_windows = np.lib.stride_tricks.sliding_window_view(b, n, axis=1)
        h_sums = h_windows.sum(axis=2)  # sum each window

        # Check player 1 win (sum == +5)
        loc = np.argwhere(h_sums == n)
        if loc.size:
            r, c = int(loc[0, 0]), int(loc[0, 1])
            # The winning cells span columns c .. c+n-1 in row r
            self._win_cells = [(r, c + k) for k in range(n)]
            return 1

        # Check player 2 win (sum == -5)
        loc = np.argwhere(h_sums == -n)
        if loc.size:
            r, c = int(loc[0, 0]), int(loc[0, 1])
            self._win_cells = [(r, c + k) for k in range(n)]
            return 2

        # --- Vertical windows ---
        # Slide a window of height n down the rows.
        v_windows = np.lib.stride_tricks.sliding_window_view(b, n, axis=0)
        v_sums = v_windows.sum(axis=2)  # shape (ROWS - n + 1, COLS)

        loc = np.argwhere(v_sums == n)
        if loc.size:
            r, c = int(loc[0, 0]), int(loc[0, 1])
            self._win_cells = [(r + k, c) for k in range(n)]
            return 1

        loc = np.argwhere(v_sums == -n)
        if loc.size:
            r, c = int(loc[0, 0]), int(loc[0, 1])
            self._win_cells = [(r + k, c) for k in range(n)]
            return 2

        # --- Diagonal windows (top-left to bottom-right: "\" direction) ---
        # Extract every 5x5 sub-block, then take the main diagonal of each.
        # sliding_window_view with window shape (n, n) gives all sub-blocks.
        blocks = np.lib.stride_tricks.sliding_window_view(b, (n, n))
        # blocks shape: (ROWS-n+1, COLS-n+1, n, n)

        # Main diagonal of each block: indices [i, i] for i in 0..n-1
        # Use np.diagonal on the last two axes.
        diag_main = np.diagonal(blocks, axis1=2, axis2=3)  # shape (..., n)
        d_sums = diag_main.sum(axis=2)

        loc = np.argwhere(d_sums == n)
        if loc.size:
            r, c = int(loc[0, 0]), int(loc[0, 1])
            self._win_cells = [(r + k, c + k) for k in range(n)]
            return 1

        loc = np.argwhere(d_sums == -n)
        if loc.size:
            r, c = int(loc[0, 0]), int(loc[0, 1])
            self._win_cells = [(r + k, c + k) for k in range(n)]
            return 2

        # --- Anti-diagonal windows (top-right to bottom-left: "/" direction) ---
        # Flip the board horizontally, then the main diagonal of flipped
        # blocks corresponds to the anti-diagonal of the original board.
        b_flip = np.fliplr(b)
        blocks_flip = np.lib.stride_tricks.sliding_window_view(b_flip, (n, n))
        anti_diag = np.diagonal(blocks_flip, axis1=2, axis2=3)
        a_sums = anti_diag.sum(axis=2)

        loc = np.argwhere(a_sums == n)
        if loc.size:
            r, c_flip = int(loc[0, 0]), int(loc[0, 1])
            # Map flipped column index back to original coordinates
            # In the flipped board the starting column c_flip corresponds to
            # original column (COLS - 1 - c_flip).  The diagonal goes
            # down-right in the flipped board, which is down-left in the
            # original.
            orig_c = self.COLS - 1 - c_flip
            self._win_cells = [(r + k, orig_c - k) for k in range(n)]
            return 1

        loc = np.argwhere(a_sums == -n)
        if loc.size:
            r, c_flip = int(loc[0, 0]), int(loc[0, 1])
            orig_c = self.COLS - 1 - c_flip
            self._win_cells = [(r + k, orig_c - k) for k in range(n)]
            return 2

        # No winner found
        self._win_cells = []
        return 0

    # ------------------------------------------------------------------
    # Board-full (draw) check
    # ------------------------------------------------------------------

    def _is_draw(self) -> bool:
        """Return True when every cell is occupied (no zeros left)."""
        # numpy.count_nonzero is O(1)-ish and avoids a Python loop
        return int(np.count_nonzero(self.board == 0)) == 0

    # ------------------------------------------------------------------
    # Pygame drawing helpers
    # ------------------------------------------------------------------

    def _draw_grid(self, surface: pygame.Surface) -> None:
        """Draw the 10x10 grid lines on the board area."""
        # Vertical lines
        for col in range(self.COLS + 1):
            x = col * self.CELL_PX
            pygame.draw.line(surface, BLACK, (x, 0), (x, self.BOARD_PX), self.LINE_WIDTH)
        # Horizontal lines
        for row in range(self.ROWS + 1):
            y = row * self.CELL_PX
            pygame.draw.line(surface, BLACK, (0, y), (self.BOARD_PX, y), self.LINE_WIDTH)

    def _draw_marks(self, surface: pygame.Surface) -> None:
        """Draw X (player 1) and O (player 2) marks using numpy.where to
        find occupied cells -- avoids a manual nested loop over each cell."""
        # Get arrays of row/col indices where each player has marks
        p1_rows, p1_cols = np.where(self.board == 1)
        p2_rows, p2_cols = np.where(self.board == -1)

        pad = self.MARK_PAD

        # Draw all X marks for player 1 (blue)
        for r, c in zip(p1_rows, p1_cols):
            x1 = int(c) * self.CELL_PX + pad
            y1 = int(r) * self.CELL_PX + pad
            x2 = (int(c) + 1) * self.CELL_PX - pad
            y2 = (int(r) + 1) * self.CELL_PX - pad
            # Two diagonal lines form an "X"
            pygame.draw.line(surface, BLUE, (x1, y1), (x2, y2), 3)
            pygame.draw.line(surface, BLUE, (x2, y1), (x1, y2), 3)

        # Draw all O marks for player 2 (red)
        for r, c in zip(p2_rows, p2_cols):
            cx = int(c) * self.CELL_PX + self.CELL_PX // 2
            cy = int(r) * self.CELL_PX + self.CELL_PX // 2
            radius = self.CELL_PX // 2 - pad
            pygame.draw.circle(surface, RED, (cx, cy), radius, 3)

    def _highlight_win(self, surface: pygame.Surface) -> None:
        """Draw a translucent green rectangle over each winning cell."""
        for r, c in self._win_cells:
            rect = pygame.Rect(
                c * self.CELL_PX + 1,
                r * self.CELL_PX + 1,
                self.CELL_PX - 2,
                self.CELL_PX - 2,
            )
            # Semi-transparent highlight via a temporary surface
            highlight = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            highlight.fill((*GREEN, 90))  # RGBA -- 90/255 opacity
            surface.blit(highlight, rect.topleft)

    def _draw_status(self, surface: pygame.Surface, text: str) -> None:
        """Render a one-line status message in the bar below the board."""
        font = pygame.font.SysFont("arial", 24)
        label = font.render(text, True, BLACK)
        # Leave space for the undo button on the right side of the bar.
        x = max(12, (self._undo_button_rect().left - label.get_width()) // 2)
        y = self.BOARD_PX + (self.STATUS_H - label.get_height()) // 2
        surface.blit(label, (x, y))

    def _undo_button_rect(self) -> pygame.Rect:
        """Return the fixed rectangle used for the one-step undo button."""
        return pygame.Rect(
            self.WINDOW_W - self.UNDO_W - 14,
            self.BOARD_PX + (self.STATUS_H - self.UNDO_H) // 2,
            self.UNDO_W,
            self.UNDO_H,
        )

    def _draw_undo_button(self, surface: pygame.Surface, enabled: bool) -> None:
        """Draw the one-step undo button in the status bar."""
        rect = self._undo_button_rect()
        fill = BLUE if enabled else (220, 220, 220)
        text_colour = WHITE if enabled else (110, 110, 110)
        pygame.draw.rect(surface, fill, rect, border_radius=8)
        pygame.draw.rect(surface, BLACK, rect, width=2, border_radius=8)

        font = pygame.font.SysFont("arial", 18, bold=True)
        label = font.render("Undo", True, text_colour)
        surface.blit(
            label,
            (
                rect.x + (rect.width - label.get_width()) // 2,
                rect.y + (rect.height - label.get_height()) // 2,
            ),
        )

    def _draw_game_over_dialog(self, surface: pygame.Surface, message: str) -> None:
        """Draw a centred dialog box announcing the game result."""
        # Semi-transparent dark overlay behind the dialog
        overlay = pygame.Surface((self.WINDOW_W, self.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        # Dialog box dimensions
        dw, dh = 420, 160
        dx = (self.WINDOW_W - dw) // 2
        dy = (self.WINDOW_H - dh) // 2
        pygame.draw.rect(surface, OVERLAY_BG, (dx, dy, dw, dh), border_radius=12)
        pygame.draw.rect(surface, BLACK, (dx, dy, dw, dh), width=2, border_radius=12)

        # Winner / draw text
        font_big = pygame.font.SysFont("arial", 28, bold=True)
        lbl = font_big.render(message, True, BLACK)
        surface.blit(lbl, (dx + (dw - lbl.get_width()) // 2, dy + 30))

        # Instruction text
        font_sm = pygame.font.SysFont("arial", 18)
        hint = font_sm.render("Click anywhere or press Q to continue", True, GRAY)
        surface.blit(hint, (dx + (dw - hint.get_width()) // 2, dy + 90))

    # ------------------------------------------------------------------
    # Click -> board coordinate conversion
    # ------------------------------------------------------------------

    def _cell_from_pixel(self, mx: int, my: int) -> tuple[int, int] | None:
        """Convert a mouse click position to (row, col) on the board.

        Returns None if the click is outside the board area."""
        if my >= self.BOARD_PX or mx >= self.BOARD_PX:
            return None
        col = mx // self.CELL_PX
        row = my // self.CELL_PX
        # Clamp to valid range (safety net for edge pixels)
        row = min(row, self.ROWS - 1)
        col = min(col, self.COLS - 1)
        return (row, col)

    # ------------------------------------------------------------------
    # Main game loop
    # ------------------------------------------------------------------

    def run(self) -> tuple[str, str]:
        """
        Launch the Pygame window and run the event loop.

        Returns
        -------
        tuple[str, str]
            (winner_name, loser_name) if someone won, or
            ("draw", "draw") on a draw.
        """
        screen = pygame.display.set_mode((self.WINDOW_W, self.WINDOW_H))
        pygame.display.set_caption(self.game_name)
        clock = pygame.time.Clock()

        winner: int = 0       # 0 = ongoing, 1 or 2 = that player won
        draw: bool = False     # True when the board is full with no winner
        game_over: bool = False

        # Result strings built at the end
        result: tuple[str, str] = ("draw", "draw")
        undo_rect = self._undo_button_rect()

        def undo_last_move() -> bool:
            nonlocal winner, draw, game_over, result
            state = self.restore_undo_state()
            if state is None:
                return False

            winner = int(state["winner"])
            draw = bool(state["draw"])
            game_over = bool(state["game_over"])
            result = state["result"]
            self._win_cells = list(state["win_cells"])
            return True

        running = True
        while running:
            # --- Event handling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                        break
                    if event.key == pygame.K_u and undo_last_move():
                        continue

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if undo_rect.collidepoint(event.pos):
                        undo_last_move()
                        continue

                # Any click or key dismisses the game-over dialog
                if game_over and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    running = False
                    break

                if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                    cell = self._cell_from_pixel(*event.pos)
                    if cell is None:
                        continue
                    r, c = cell

                    # Only allow placement on empty cells
                    if self.board[r, c] != 0:
                        continue

                    self.remember_undo_state(
                        winner=winner,
                        draw=draw,
                        game_over=game_over,
                        result=result,
                        win_cells=list(self._win_cells),
                    )

                    # Place the mark: +1 for player 1, -1 for player 2
                    self.board[r, c] = 1 if self.current_player == 1 else -1

                    # Check for a winner after every move
                    winner = self.check_win()
                    if winner:
                        game_over = True
                        if winner == 1:
                            result = (self.player1_name, self.player2_name)
                        else:
                            result = (self.player2_name, self.player1_name)
                    elif self._is_draw():
                        draw = True
                        game_over = True
                        result = ("draw", "draw")
                    else:
                        # No winner and board not full -- next player's turn
                        self.switch_turn()

            # --- Drawing ---
            screen.fill(WHITE)
            self._draw_grid(screen)
            self._draw_marks(screen)

            if winner:
                # Highlight the five winning cells in green
                self._highlight_win(screen)

            if game_over:
                if winner:
                    msg = f"{result[0]} wins!"
                else:
                    msg = "It's a draw!"
                self._draw_status(screen, msg)
                self._draw_game_over_dialog(screen, msg)
            else:
                # Show whose turn it is
                self._draw_status(screen, f"{self.get_current_player_name()}'s turn  (X)" if self.current_player == 1 else f"{self.get_current_player_name()}'s turn  (O)")

            self._draw_undo_button(screen, self.has_undo())
            pygame.display.flip()
            clock.tick(30)  # cap at 30 FPS -- plenty for a board game

        return result


# ---------------------------------------------------------------------------
# Allow running the game directly for quick testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    game = TicTacToe("Alice", "Bob")
    winner_name, loser_name = game.run()
    if winner_name == "draw":
        print("The game ended in a draw.")
    else:
        print(f"{winner_name} defeated {loser_name}!")
