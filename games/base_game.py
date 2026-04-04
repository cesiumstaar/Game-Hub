"""
Abstract base class for two-player turn-based board games.

Provides the shared skeleton (board state, turn management, reset)
that every concrete game inherits.
"""

from abc import ABC, abstractmethod
import numpy as np


class BoardGame(ABC):
    """
    Base class for a 2-player board game backed by a NumPy array.

    Attributes
    ----------
    player1_name : str
        Display name of player 1.
    player2_name : str
        Display name of player 2.
    current_player : int
        1 or 2 -- whose turn it is right now.
    board : np.ndarray
        The game board stored as a 2-D NumPy array of floats.
    board_size : tuple[int, int]
        (rows, cols) dimensions of the board.
    game_name : str
        Human-readable name shown in window titles, etc.
    """

    def __init__(
        self,
        player1: str,
        player2: str,
        board_rows: int,
        board_cols: int,
        game_name: str,
    ) -> None:
        # Store player names for later display / result reporting
        self.player1_name: str = player1
        self.player2_name: str = player2

        # Player 1 always goes first
        self.current_player: int = 1

        # Board dimensions kept as a tuple for convenience
        self.board_size: tuple[int, int] = (board_rows, board_cols)

        # Human-readable title for the game
        self.game_name: str = game_name

        # Initialise the board as an array of zeros (empty cells)
        self.board: np.ndarray = np.zeros(
            (board_rows, board_cols), dtype=np.float64
        )

    # ------------------------------------------------------------------
    # Turn management
    # ------------------------------------------------------------------

    def switch_turn(self) -> None:
        """Toggle current_player between 1 and 2."""
        # Simple toggle: 1 -> 2, 2 -> 1
        self.current_player = 2 if self.current_player == 1 else 1

    def get_current_player_name(self) -> str:
        """Return the display name of whoever's turn it is."""
        # Map numeric id to the stored name string
        if self.current_player == 1:
            return self.player1_name
        return self.player2_name

    # ------------------------------------------------------------------
    # Board helpers
    # ------------------------------------------------------------------

    def reset_board(self) -> None:
        """Clear the board back to all zeros and reset to player 1's turn."""
        # np.zeros re-creates a fresh empty board
        self.board = np.zeros(self.board_size, dtype=np.float64)
        # Player 1 always starts after a reset
        self.current_player = 1

    # ------------------------------------------------------------------
    # Abstract interface -- subclasses MUST implement these
    # ------------------------------------------------------------------

    @abstractmethod
    def check_win(self) -> int:
        """
        Evaluate the board and return the winner.

        Returns
        -------
        int
            0  -- no winner yet (game continues or draw must be checked
                  separately).
            1  -- player 1 wins.
            2  -- player 2 wins.
        """
        ...
