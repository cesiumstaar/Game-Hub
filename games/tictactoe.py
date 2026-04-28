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

WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
BLUE   = (30,  80,  220)    # player 1 (X)
RED    = (220, 40,  40)     # player 2 (O)
GRAY   = (180, 180, 180)
GREEN  = (50,  200, 80)     # win highlight
OVERLAY_BG = (240, 240, 240)


class TicTacToe(BoardGame):
    """10x10 Tic-Tac-Toe where 5 marks in a row wins."""

    ROWS = 10
    COLS = 10
    WIN_LENGTH = 5

    BOARD_PX   = 700
    STATUS_H   = 50
    WINDOW_W   = BOARD_PX
    WINDOW_H   = BOARD_PX + STATUS_H
    CELL_PX    = BOARD_PX // COLS
    MARK_PAD   = 12
    LINE_WIDTH = 2

    def __init__(self, player1: str = "Player 1", player2: str = "Player 2", vs_ai: bool = False) -> None:
        super().__init__(player1, player2, self.ROWS, self.COLS, "Tic-Tac-Toe 10x10")
        self._win_cells: list[tuple[int, int]] = []  # filled when someone wins
        self.vs_ai = vs_ai

    # ── Win detection using NumPy sliding windows ────────────────────

    def check_win(self) -> int:
        """Slide a window of 5 across every row, column, and diagonal.
        If the sum is +5 -> player 1 wins, -5 -> player 2 wins."""
        b = self.board
        n = self.WIN_LENGTH

        # horizontal
        h_windows = np.lib.stride_tricks.sliding_window_view(b, n, axis=1)
        h_sums = h_windows.sum(axis=2)

        loc = np.argwhere(h_sums == n)
        if loc.size:
            r, c = int(loc[0, 0]), int(loc[0, 1])
            self._win_cells = [(r, c + k) for k in range(n)]
            return 1
        loc = np.argwhere(h_sums == -n)
        if loc.size:
            r, c = int(loc[0, 0]), int(loc[0, 1])
            self._win_cells = [(r, c + k) for k in range(n)]
            return 2

        # vertical
        v_windows = np.lib.stride_tricks.sliding_window_view(b, n, axis=0)
        v_sums = v_windows.sum(axis=2)

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

        # diagonal (\) -- extract every 5x5 block, take its main diagonal
        blocks = np.lib.stride_tricks.sliding_window_view(b, (n, n))
        diag_main = np.diagonal(blocks, axis1=2, axis2=3)
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

        # anti-diagonal (/) -- flip board, then main diagonal = anti-diagonal
        b_flip = np.fliplr(b)
        blocks_flip = np.lib.stride_tricks.sliding_window_view(b_flip, (n, n))
        anti_diag = np.diagonal(blocks_flip, axis1=2, axis2=3)
        a_sums = anti_diag.sum(axis=2)

        loc = np.argwhere(a_sums == n)
        if loc.size:
            r, c_flip = int(loc[0, 0]), int(loc[0, 1])
            orig_c = self.COLS - 1 - c_flip  # map flipped index back
            self._win_cells = [(r + k, orig_c - k) for k in range(n)]
            return 1
        loc = np.argwhere(a_sums == -n)
        if loc.size:
            r, c_flip = int(loc[0, 0]), int(loc[0, 1])
            orig_c = self.COLS - 1 - c_flip
            self._win_cells = [(r + k, orig_c - k) for k in range(n)]
            return 2

        self._win_cells = []
        return 0

    def _is_draw(self) -> bool:
        return int(np.count_nonzero(self.board == 0)) == 0

    # ── AI opponent (heuristic scoring) ──────────────────────────────

    def _ai_score_board(self) -> np.ndarray:
        """Give each empty cell a score based on how useful it is.
        Higher weight = more urgent (e.g. completing 5 or blocking opponent)."""
        n = self.WIN_LENGTH
        scores = np.zeros((self.ROWS, self.COLS), dtype=np.float32)

        # boolean masks for AI pieces, opponent pieces, empty cells
        ai_mask = (self.board == -1).astype(np.int8)
        opp_mask = (self.board == 1).astype(np.int8)
        empty_mask = (self.board == 0).astype(np.int8)

        def score_windows(windows_ai, windows_opp, windows_empty, coords):
            """Look at every 5-cell window and assign weights to empty cells."""
            for idx in range(windows_ai.shape[0] * windows_ai.shape[1]):
                r_start = idx // windows_ai.shape[1]
                c_start = idx % windows_ai.shape[1]

                ai_count = windows_ai[r_start, c_start]
                opp_count = windows_opp[r_start, c_start]

                # window has pieces from both sides -- can't be completed by either
                if ai_count > 0 and opp_count > 0:
                    continue

                # weight depends on how close to a winning/losing 5
                if ai_count == 4 and opp_count == 0:
                    weight = 10000   # can win right now
                elif opp_count == 4 and ai_count == 0:
                    weight = 9000    # must block or we lose
                elif ai_count == 3 and opp_count == 0:
                    weight = 100
                elif opp_count == 3 and ai_count == 0:
                    weight = 80
                elif ai_count == 2 and opp_count == 0:
                    weight = 10
                elif opp_count == 2 and ai_count == 0:
                    weight = 8
                elif ai_count == 1 and opp_count == 0:
                    weight = 1
                elif opp_count == 1 and ai_count == 0:
                    weight = 1
                else:
                    weight = 0

                # spread this weight to every empty cell in the window
                for k in range(n):
                    cell_r, cell_c = coords(r_start, c_start, k)
                    if 0 <= cell_r < self.ROWS and 0 <= cell_c < self.COLS:
                        if self.board[cell_r, cell_c] == 0:
                            scores[cell_r, cell_c] += weight

        # check all four directions using sliding windows
        # horizontal
        h_ai = np.lib.stride_tricks.sliding_window_view(ai_mask, n, axis=1).sum(axis=2)
        h_opp = np.lib.stride_tricks.sliding_window_view(opp_mask, n, axis=1).sum(axis=2)
        h_empty = np.lib.stride_tricks.sliding_window_view(empty_mask, n, axis=1).sum(axis=2)
        score_windows(h_ai, h_opp, h_empty, lambda r, c, k: (r, c + k))

        # vertical
        v_ai = np.lib.stride_tricks.sliding_window_view(ai_mask, n, axis=0).sum(axis=2)
        v_opp = np.lib.stride_tricks.sliding_window_view(opp_mask, n, axis=0).sum(axis=2)
        v_empty = np.lib.stride_tricks.sliding_window_view(empty_mask, n, axis=0).sum(axis=2)
        score_windows(v_ai, v_opp, v_empty, lambda r, c, k: (r + k, c))

        # diagonal (\)
        blocks_ai = np.lib.stride_tricks.sliding_window_view(ai_mask, (n, n))
        blocks_opp = np.lib.stride_tricks.sliding_window_view(opp_mask, (n, n))
        blocks_empty = np.lib.stride_tricks.sliding_window_view(empty_mask, (n, n))
        diag_ai = np.diagonal(blocks_ai, axis1=2, axis2=3).sum(axis=2)
        diag_opp = np.diagonal(blocks_opp, axis1=2, axis2=3).sum(axis=2)
        diag_empty = np.diagonal(blocks_empty, axis1=2, axis2=3).sum(axis=2)
        score_windows(diag_ai, diag_opp, diag_empty, lambda r, c, k: (r + k, c + k))

        # anti-diagonal (/)
        ai_flip = np.fliplr(ai_mask)
        opp_flip = np.fliplr(opp_mask)
        empty_flip = np.fliplr(empty_mask)
        blocks_ai_flip = np.lib.stride_tricks.sliding_window_view(ai_flip, (n, n))
        blocks_opp_flip = np.lib.stride_tricks.sliding_window_view(opp_flip, (n, n))
        blocks_empty_flip = np.lib.stride_tricks.sliding_window_view(empty_flip, (n, n))
        anti_ai = np.diagonal(blocks_ai_flip, axis1=2, axis2=3).sum(axis=2)
        anti_opp = np.diagonal(blocks_opp_flip, axis1=2, axis2=3).sum(axis=2)
        anti_empty = np.diagonal(blocks_empty_flip, axis1=2, axis2=3).sum(axis=2)
        score_windows(anti_ai, anti_opp, anti_empty, lambda r, c_flip, k: (r + k, self.COLS - 1 - c_flip - k))

        return scores

    def ai_best_move(self) -> tuple[int, int]:
        """Pick the highest-scoring empty cell. Slightly prefer centre."""
        scores = self._ai_score_board()

        # nudge towards centre to break ties on empty boards
        centre_r, centre_c = self.ROWS // 2, self.COLS // 2
        for r in range(self.ROWS):
            for c in range(self.COLS):
                if self.board[r, c] == 0:
                    dist = abs(r - centre_r) + abs(c - centre_c)
                    scores[r, c] += max(0, 2.0 - dist * 0.1)

        best_idx = np.argmax(scores)
        return (best_idx // self.COLS, best_idx % self.COLS)

    # ── Pygame drawing ───────────────────────────────────────────────

    def _draw_grid(self, surface: pygame.Surface) -> None:
        """Draw the 10x10 grid lines."""
        for col in range(self.COLS + 1):
            x = col * self.CELL_PX
            pygame.draw.line(surface, BLACK, (x, 0), (x, self.BOARD_PX), self.LINE_WIDTH)
        for row in range(self.ROWS + 1):
            y = row * self.CELL_PX
            pygame.draw.line(surface, BLACK, (0, y), (self.BOARD_PX, y), self.LINE_WIDTH)

    def _draw_marks(self, surface: pygame.Surface) -> None:
        """Draw X and O marks using np.where to find occupied cells."""
        p1_rows, p1_cols = np.where(self.board == 1)
        p2_rows, p2_cols = np.where(self.board == -1)
        pad = self.MARK_PAD

        # X marks for player 1
        for r, c in zip(p1_rows, p1_cols):
            x1 = int(c) * self.CELL_PX + pad
            y1 = int(r) * self.CELL_PX + pad
            x2 = (int(c) + 1) * self.CELL_PX - pad
            y2 = (int(r) + 1) * self.CELL_PX - pad
            pygame.draw.line(surface, BLUE, (x1, y1), (x2, y2), 3)
            pygame.draw.line(surface, BLUE, (x2, y1), (x1, y2), 3)

        # O marks for player 2
        for r, c in zip(p2_rows, p2_cols):
            cx = int(c) * self.CELL_PX + self.CELL_PX // 2
            cy = int(r) * self.CELL_PX + self.CELL_PX // 2
            radius = self.CELL_PX // 2 - pad
            pygame.draw.circle(surface, RED, (cx, cy), radius, 3)

    def _highlight_win(self, surface: pygame.Surface) -> None:
        """Green semi-transparent overlay on winning cells."""
        for r, c in self._win_cells:
            rect = pygame.Rect(
                c * self.CELL_PX + 1, r * self.CELL_PX + 1,
                self.CELL_PX - 2, self.CELL_PX - 2,
            )
            highlight = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            highlight.fill((*GREEN, 90))
            surface.blit(highlight, rect.topleft)

    def _draw_status(self, surface: pygame.Surface, text: str) -> None:
        font = pygame.font.SysFont("arial", 24)
        label = font.render(text, True, BLACK)
        x = (self.WINDOW_W - label.get_width()) // 2
        y = self.BOARD_PX + (self.STATUS_H - label.get_height()) // 2
        surface.blit(label, (x, y))

    def _draw_game_over_dialog(self, surface: pygame.Surface, message: str) -> None:
        overlay = pygame.Surface((self.WINDOW_W, self.WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        dw, dh = 420, 160
        dx = (self.WINDOW_W - dw) // 2
        dy = (self.WINDOW_H - dh) // 2
        pygame.draw.rect(surface, OVERLAY_BG, (dx, dy, dw, dh), border_radius=12)
        pygame.draw.rect(surface, BLACK, (dx, dy, dw, dh), width=2, border_radius=12)

        font_big = pygame.font.SysFont("arial", 28, bold=True)
        lbl = font_big.render(message, True, BLACK)
        surface.blit(lbl, (dx + (dw - lbl.get_width()) // 2, dy + 30))

        font_sm = pygame.font.SysFont("arial", 18)
        hint = font_sm.render("Click anywhere or press Q to continue", True, GRAY)
        surface.blit(hint, (dx + (dw - hint.get_width()) // 2, dy + 90))

    def _cell_from_pixel(self, mx: int, my: int) -> tuple[int, int] | None:
        """Convert pixel click position to (row, col). None if outside board."""
        if my >= self.BOARD_PX or mx >= self.BOARD_PX:
            return None
        col = mx // self.CELL_PX
        row = my // self.CELL_PX
        row = min(row, self.ROWS - 1)
        col = min(col, self.COLS - 1)
        return (row, col)

    # ── Main game loop ───────────────────────────────────────────────

    def run(self) -> tuple[str, str]:
        screen = pygame.display.set_mode((self.WINDOW_W, self.WINDOW_H))
        pygame.display.set_caption(self.game_name)
        clock = pygame.time.Clock()

        winner: int = 0
        draw: bool = False
        game_over: bool = False
        ai_thinking = False
        ai_think_start = 0

        result: tuple[str, str] = ("draw", "draw")

        running = True
        while running:
            # if it's AI's turn, start a short delay then auto-play
            if self.vs_ai and self.current_player == 2 and not game_over and not ai_thinking:
                ai_thinking = True
                ai_think_start = pygame.time.get_ticks()

            if ai_thinking and pygame.time.get_ticks() - ai_think_start >= 400:
                ai_thinking = False
                r, c = self.ai_best_move()
                self.board[r, c] = -1  # place AI's mark

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
                    self.switch_turn()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    running = False
                    break

                if game_over and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    running = False
                    break

                if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                    # in AI mode, ignore clicks when it's not the human's turn
                    if self.vs_ai and self.current_player != 1:
                        continue

                    cell = self._cell_from_pixel(*event.pos)
                    if cell is None:
                        continue
                    r, c = cell

                    if self.board[r, c] != 0:
                        continue

                    self.board[r, c] = 1 if self.current_player == 1 else -1

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
                        self.switch_turn()

            # Drawing
            screen.fill(WHITE)
            self._draw_grid(screen)
            self._draw_marks(screen)

            if winner:
                self._highlight_win(screen)

            if game_over:
                msg = f"{result[0]} wins!" if winner else "It's a draw!"
                self._draw_status(screen, msg)
                self._draw_game_over_dialog(screen, msg)
            elif ai_thinking:
                self._draw_status(screen, f"{self.get_current_player_name()} is thinking...")
            else:
                turn_label = "(X)" if self.current_player == 1 else "(O)"
                self._draw_status(screen, f"{self.get_current_player_name()}'s turn  {turn_label}")

            pygame.display.flip()
            clock.tick(30)

        return result


if __name__ == "__main__":
    game = TicTacToe("Alice", "Bob")
    winner_name, loser_name = game.run()
    if winner_name == "draw":
        print("The game ended in a draw.")
    else:
        print(f"{winner_name} defeated {loser_name}!")
