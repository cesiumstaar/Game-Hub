"""
Connect Four -- a two-player vertical-grid coin-drop game.

Players alternate dropping coloured coins into a 7x7 grid.  Coins obey
gravity and fall to the lowest empty row in the chosen column.  The first
player to connect four coins in a row (horizontally, vertically, or
diagonally) wins.  If the board fills up with no winner the game is a draw.

Win detection uses pure NumPy operations (no Python loops).
"""

import sys
from typing import Tuple

import numpy as np
import pygame

from games.base_game import BoardGame

# ── visual constants ──────────────────────────────────────────────────
ROWS = 7
COLS = 7

CELL_SIZE = 90                       # pixel size of each board cell
RADIUS = CELL_SIZE // 2 - 6         # coin radius, slightly smaller than half-cell
TOP_MARGIN = 100                     # space above the board for the hover coin
BOARD_WIDTH = COLS * CELL_SIZE       # total pixel width of the board area
BOARD_HEIGHT = ROWS * CELL_SIZE      # total pixel height of the board area
STATUS_BAR = 50                      # height of the status text area at the bottom
WIN_WIDTH = BOARD_WIDTH              # window width  (~630 px for 7 cols)
WIN_HEIGHT = TOP_MARGIN + BOARD_HEIGHT + STATUS_BAR  # window height (~780 px)

# colours (R, G, B)
BLUE = (23, 93, 222)                 # board background
DARK_BLUE = (15, 62, 148)           # board border / grid accent
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
RED = (220, 40, 40)                  # player 1 coin
YELLOW = (240, 220, 30)             # player 2 coin
GREY = (180, 180, 180)              # empty hole colour
BG_COLOUR = (30, 30, 30)            # window background behind the board

FPS = 60                             # frame-rate cap
DROP_SPEED = 18                      # pixels per frame during coin-drop animation


class ConnectFour(BoardGame):
    """
    7x7 Connect Four with a Pygame GUI.

    Inherits board state and turn management from BoardGame.
    """

    def __init__(self, player1: str, player2: str) -> None:
        # Initialise the base class with a 7-row, 7-column board
        super().__init__(player1, player2, ROWS, COLS, "Connect Four")

    # ── core game logic ───────────────────────────────────────────────

    def get_lowest_empty_row(self, col: int) -> int:
        """
        Return the lowest (highest index) empty row in *col*, or -1 if full.

        The board stores 0.0 for empty cells, so we look from the bottom up.
        """
        # Column slice: self.board[:, col] is a 1-D array from top to bottom.
        # np.where gives indices of empty cells; we want the largest index.
        empty_rows = np.where(self.board[:, col] == 0)[0]
        if empty_rows.size == 0:
            return -1                # column is completely full
        return int(empty_rows[-1])   # lowest empty position (highest row index)

    def drop_coin(self, col: int) -> int:
        """
        Drop the current player's coin into *col*.

        Returns the row where the coin landed, or -1 if the column was full.
        """
        row = self.get_lowest_empty_row(col)
        if row == -1:
            return -1                # invalid move -- column full
        # Place the current player's marker on the board
        self.board[row, col] = self.current_player
        return row

    def is_draw(self) -> bool:
        """The game is a draw when every cell is occupied (no zeros remain)."""
        # np.all checks that no cell equals zero -- pure numpy, no loops
        return bool(np.all(self.board != 0))

    # ── win detection (numpy-only, no loops) ──────────────────────────

    def check_win(self) -> int:
        """
        Check the board for a four-in-a-row and return the winning player
        number (1 or 2), or 0 if nobody has won yet.

        Strategy
        --------
        For each player, create a boolean mask where only that player's cells
        are 1.  Then use NumPy slicing to sum every window of 4 consecutive
        cells in each direction.  A window sum of 4 on the boolean mask means
        four-in-a-row for that player.  This avoids the ambiguity of summing
        raw player values (where 2+2 could look like 1+1+1+1).
        """
        for player in (1, 2):
            # Boolean mask: True where this player has a coin
            mask = (self.board == player).astype(np.int8)

            # -- horizontal windows (each row, 4 consecutive columns) ----------
            h = mask[:, :-3] + mask[:, 1:-2] + mask[:, 2:-1] + mask[:, 3:]

            # -- vertical windows (each column, 4 consecutive rows) ------------
            v = mask[:-3, :] + mask[1:-2, :] + mask[2:-1, :] + mask[3:, :]

            # -- diagonal (top-left to bottom-right) ---------------------------
            d1 = mask[:-3, :-3] + mask[1:-2, 1:-2] + mask[2:-1, 2:-1] + mask[3:, 3:]

            # -- diagonal (top-right to bottom-left) ---------------------------
            d2 = mask[:-3, 3:] + mask[1:-2, 2:-1] + mask[2:-1, 1:-2] + mask[3:, :-3]

            # If any window sums to 4, this player has won
            if (np.any(h == 4) or np.any(v == 4)
                    or np.any(d1 == 4) or np.any(d2 == 4)):
                return player

        return 0                     # no winner yet

    # ── pygame rendering helpers ──────────────────────────────────────

    @staticmethod
    def _player_colour(player: int) -> Tuple[int, int, int]:
        """Return the RGB colour for a given player number."""
        return RED if player == 1 else YELLOW

    def _draw_board(self, surface: pygame.Surface) -> None:
        """Render the blue board with coins and empty holes."""
        # Board rectangle sits below the top margin
        board_rect = pygame.Rect(0, TOP_MARGIN, BOARD_WIDTH, BOARD_HEIGHT)
        pygame.draw.rect(surface, BLUE, board_rect)

        # Draw each cell as a circle (coin or empty hole)
        for r in range(ROWS):
            for c in range(COLS):
                # Centre of the circle within the board area
                cx = c * CELL_SIZE + CELL_SIZE // 2
                cy = TOP_MARGIN + r * CELL_SIZE + CELL_SIZE // 2
                cell = self.board[r, c]
                if cell == 0:
                    colour = GREY                       # empty hole
                else:
                    colour = self._player_colour(int(cell))
                pygame.draw.circle(surface, colour, (cx, cy), RADIUS)
                # Thin border around each hole for depth
                pygame.draw.circle(surface, DARK_BLUE, (cx, cy), RADIUS, 2)

    def _draw_hover(self, surface: pygame.Surface, col: int, player: int) -> None:
        """Draw a translucent coin above the board showing which column is targeted."""
        if 0 <= col < COLS:
            cx = col * CELL_SIZE + CELL_SIZE // 2
            cy = TOP_MARGIN // 2  # vertically centred in the top margin
            # Draw the hover coin with the current player's colour
            pygame.draw.circle(surface, self._player_colour(player), (cx, cy), RADIUS)

    def _draw_status(self, surface: pygame.Surface, text: str) -> None:
        """Render a one-line status message beneath the board."""
        font = pygame.font.SysFont("arial", 26, bold=True)
        label = font.render(text, True, WHITE)
        # Centre the text in the status bar area
        x = (WIN_WIDTH - label.get_width()) // 2
        y = TOP_MARGIN + BOARD_HEIGHT + (STATUS_BAR - label.get_height()) // 2
        surface.blit(label, (x, y))

    # ── coin-drop animation ───────────────────────────────────────────

    def _animate_drop(
        self,
        surface: pygame.Surface,
        clock: pygame.time.Clock,
        col: int,
        target_row: int,
        player: int,
    ) -> None:
        """
        Animate a coin falling from the top of the board to *target_row*.

        The coin's vertical position is incremented each frame until it
        reaches the target cell's centre.
        """
        cx = col * CELL_SIZE + CELL_SIZE // 2
        start_y = TOP_MARGIN + CELL_SIZE // 2           # top of the board grid
        end_y = TOP_MARGIN + target_row * CELL_SIZE + CELL_SIZE // 2
        current_y = start_y
        colour = self._player_colour(player)

        # Temporarily remove the coin from the board so _draw_board won't show it
        self.board[target_row, col] = 0

        while current_y < end_y:
            current_y = min(current_y + DROP_SPEED, end_y)

            # Redraw everything behind the falling coin
            surface.fill(BG_COLOUR)
            self._draw_board(surface)
            self._draw_status(surface, f"{self.get_current_player_name()}'s turn")

            # Draw the falling coin on top
            pygame.draw.circle(surface, colour, (cx, current_y), RADIUS)
            pygame.draw.circle(surface, DARK_BLUE, (cx, current_y), RADIUS, 2)

            pygame.display.flip()
            clock.tick(FPS)

        # Place the coin back on the board now that the animation is done
        self.board[target_row, col] = player

    # ── main game loop ────────────────────────────────────────────────

    def run(self) -> Tuple[str, str]:
        """
        Launch the Pygame window and run the game until someone wins or it
        is a draw.

        Returns
        -------
        tuple[str, str]
            (winner_name, loser_name) or ("draw", "draw").
        """
        pygame.init()
        surface = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        pygame.display.set_caption("Connect Four")
        clock = pygame.time.Clock()

        game_over = False
        result: Tuple[str, str] = ("draw", "draw")
        hover_col = -1                     # column the mouse is hovering over

        # ---- event loop ------------------------------------------------------
        while True:
            for event in pygame.event.get():
                # Handle window close or Escape key
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return result

                # Track which column the mouse is over (for the hover indicator)
                if event.type == pygame.MOUSEMOVE:
                    hover_col = event.pos[0] // CELL_SIZE

                # Process a click only while the game is still active
                if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                    col = event.pos[0] // CELL_SIZE  # column derived from x-position
                    if 0 <= col < COLS:
                        row = self.get_lowest_empty_row(col)
                        if row == -1:
                            continue  # column full -- ignore click

                        player = self.current_player

                        # Animate the coin falling, then finalise the placement
                        self._animate_drop(surface, clock, col, row, player)

                        # --- check for win or draw after the move ---
                        winner = self.check_win()
                        if winner:
                            game_over = True
                            winner_name = self.get_current_player_name()
                            loser_name = (
                                self.player2_name
                                if winner == 1
                                else self.player1_name
                            )
                            result = (winner_name, loser_name)
                        elif self.is_draw():
                            game_over = True
                            result = ("draw", "draw")
                        else:
                            # No winner yet -- next player's turn
                            self.switch_turn()

            # ---- drawing ─────────────────────────────────────────────────────
            surface.fill(BG_COLOUR)
            self._draw_board(surface)

            if game_over:
                # Show the final result in the status bar
                if result[0] == "draw":
                    self._draw_status(surface, "It's a draw!  Press ESC to exit.")
                else:
                    self._draw_status(
                        surface,
                        f"{result[0]} wins!  Press ESC to exit.",
                    )
            else:
                # Show whose turn it is and the hover indicator
                self._draw_hover(surface, hover_col, self.current_player)
                self._draw_status(
                    surface, f"{self.get_current_player_name()}'s turn"
                )

            pygame.display.flip()
            clock.tick(FPS)
