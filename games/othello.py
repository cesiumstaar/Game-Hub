"""
Othello (Reversi) – an 8x8 disc-flipping board game.

Two players take turns placing discs. A move is legal only when it traps
opponent discs between the new disc and an existing friendly disc. The
game ends when neither player can move; the player with more discs wins.
"""
from __future__ import annotations

import numpy as np
import pygame
from games.base_game import BoardGame

DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),          ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1),
]

BOARD_GREEN  = (34, 139, 34)
LINE_COLOUR  = (0, 0, 0)
BLACK_DISC   = (10, 10, 10)
WHITE_DISC   = (240, 240, 240)
HINT_COLOUR  = (180, 180, 180, 160)
BG_COLOUR    = (30, 30, 30)
TEXT_COLOUR  = (255, 255, 255)


class Othello(BoardGame):
    """Full Othello (Reversi) game with a Pygame GUI."""

    BOARD_SIZE   = 8
    CELL_SIZE    = 80
    BOARD_PX     = CELL_SIZE * BOARD_SIZE
    MARGIN       = 30
    INFO_HEIGHT  = 110
    WIN_W        = BOARD_PX + 2 * MARGIN
    WIN_H        = BOARD_PX + 2 * MARGIN + INFO_HEIGHT

    def __init__(self, player1: str, player2: str) -> None:
        super().__init__(player1, player2, self.BOARD_SIZE, self.BOARD_SIZE, "Othello")
        # Standard starting position
        self.board[3][3] = 2
        self.board[3][4] = 1
        self.board[4][3] = 1
        self.board[4][4] = 2

    def _discs_to_flip(self, row: int, col: int, player: int) -> list[tuple[int, int]]:
        """Return positions that would be flipped if player places at (row, col)."""
        if self.board[row][col] != 0:
            return []

        opponent = 2 if player == 1 else 1
        flips: list[tuple[int, int]] = []

        for dr, dc in DIRECTIONS:
            candidates: list[tuple[int, int]] = []
            r, c = row + dr, col + dc

            while 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and self.board[r][c] == opponent:
                candidates.append((r, c))
                r += dr
                c += dc

            if candidates and 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and self.board[r][c] == player:
                flips.extend(candidates)

        return flips

    def get_valid_moves(self, player: int) -> dict[tuple[int, int], list[tuple[int, int]]]:
        moves: dict[tuple[int, int], list[tuple[int, int]]] = {}
        for r in range(self.BOARD_SIZE):
            for c in range(self.BOARD_SIZE):
                flips = self._discs_to_flip(r, c, player)
                if flips:
                    moves[(r, c)] = flips
        return moves

    def make_move(self, row: int, col: int) -> bool:
        flips = self._discs_to_flip(row, col, self.current_player)
        if not flips:
            return False
        self.board[row][col] = self.current_player
        for r, c in flips:
            self.board[r][c] = self.current_player
        return True

    def check_win(self) -> int:
        """Returns 0 (ongoing), 1 (black wins), 2 (white wins), or -1 (draw).
        Uses numpy for disc counting."""
        if self.get_valid_moves(1) or self.get_valid_moves(2):
            return 0
        black_count = int(np.count_nonzero(self.board == 1))
        white_count = int(np.count_nonzero(self.board == 2))
        if black_count > white_count:
            return 1
        elif white_count > black_count:
            return 2
        return -1

    def _get_scores(self) -> tuple[int, int]:
        return int(np.sum(self.board == 1)), int(np.sum(self.board == 2))

    # ── Pygame drawing ───────────────────────────────────────────────

    def _draw_board(self, surface: pygame.Surface) -> None:
        mx, my = self.MARGIN, self.MARGIN
        pygame.draw.rect(surface, BOARD_GREEN, (mx, my, self.BOARD_PX, self.BOARD_PX))

        for i in range(self.BOARD_SIZE + 1):
            pygame.draw.line(surface, LINE_COLOUR,
                (mx, my + i * self.CELL_SIZE), (mx + self.BOARD_PX, my + i * self.CELL_SIZE), 2)
            pygame.draw.line(surface, LINE_COLOUR,
                (mx + i * self.CELL_SIZE, my), (mx + i * self.CELL_SIZE, my + self.BOARD_PX), 2)

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
        mx, my = self.MARGIN, self.MARGIN
        for (r, c) in valid_moves:
            cx = mx + c * self.CELL_SIZE + self.CELL_SIZE // 2
            cy = my + r * self.CELL_SIZE + self.CELL_SIZE // 2
            pygame.draw.circle(surface, HINT_COLOUR[:3], (cx, cy), 6)

    def _draw_info(self, surface: pygame.Surface, valid_moves: dict, game_over: bool, winner: int) -> None:
        font_big   = pygame.font.SysFont("Arial", 28, bold=True)
        font_small = pygame.font.SysFont("Arial", 22)
        black_score, white_score = self._get_scores()
        info_y = self.MARGIN + self.BOARD_PX + 12

        p1_label = font_small.render(f"{self.player1_name} (Black)", True, TEXT_COLOUR)
        p1_score = font_big.render(str(black_score), True, TEXT_COLOUR)
        surface.blit(p1_label, (self.MARGIN, info_y))
        surface.blit(p1_score, (self.MARGIN, info_y + 28))

        p2_label = font_small.render(f"{self.player2_name} (White)", True, TEXT_COLOUR)
        p2_score = font_big.render(str(white_score), True, TEXT_COLOUR)
        surface.blit(p2_label, (self.WIN_W - self.MARGIN - p2_label.get_width(), info_y))
        surface.blit(p2_score, (self.WIN_W - self.MARGIN - p2_score.get_width(), info_y + 28))

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
                status_text = f"{name} ({colour_label}) has no moves -- skipping"

        status_surf = font_small.render(status_text, True, TEXT_COLOUR)
        surface.blit(status_surf, ((self.WIN_W - status_surf.get_width()) // 2, info_y + 66))

    # ── Main loop ────────────────────────────────────────────────────

    def run(self) -> tuple[str, str]:
        screen = pygame.display.set_mode((self.WIN_W, self.WIN_H))
        pygame.display.set_caption("Othello")
        clock = pygame.time.Clock()

        game_over = False
        winner = 0
        skip_delay = 0

        running = True
        while running:
            valid_moves = self.get_valid_moves(self.current_player) if not game_over else {}

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    break
                if game_over and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    running = False
                    break

                if event.type == pygame.MOUSEBUTTONDOWN and not game_over and skip_delay == 0:
                    x, y = event.pos
                    col = (x - self.MARGIN) // self.CELL_SIZE
                    row = (y - self.MARGIN) // self.CELL_SIZE

                    if 0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE:
                        if (row, col) in valid_moves:
                            self.make_move(row, col)
                            winner = self.check_win()
                            if winner != 0:
                                game_over = True
                            else:
                                self.switch_turn()
                                next_moves = self.get_valid_moves(self.current_player)
                                if not next_moves:
                                    skip_delay = 45

            if skip_delay > 0 and not game_over:
                skip_delay -= 1
                if skip_delay == 0:
                    self.switch_turn()
                    winner = self.check_win()
                    if winner != 0:
                        game_over = True

            screen.fill(BG_COLOUR)
            self._draw_board(screen)
            if not game_over and skip_delay == 0:
                self._draw_hints(screen, valid_moves)
            self._draw_info(screen, valid_moves, game_over, winner)
            pygame.display.flip()
            clock.tick(60)

        if winner == 1:
            return (self.player1_name, self.player2_name)
        elif winner == 2:
            return (self.player2_name, self.player1_name)
        return ("draw", "draw")
