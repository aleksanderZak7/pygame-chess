import pygame
from pathlib import Path

from . import Piece, SpecialPiece, Rook


class King(SpecialPiece):
    """
    Class representing a king chess piece.
    """
    __slots__ = ("_checked", "_castling_rook")

    def __init__(self, color: int, path: Path, x: int, y: int) -> None:
        """
        Initializes the King piece with the following parameters:
        
        :param color: The color of the King (1 for white, 0 for black).
        :param path: The path to the directory containing the images for the King piece.
        :param x: The initial x-coordinate of the King on the chessboard (0 to 7).
        :param y: The initial y-coordinate of the King on the chessboard (0 to 7).
        
        Initializes the `_checked` status as False and the `_castling_rook` dictionary for managing castling.
        """
        self._checked: bool = False
        self._castling_rook: dict[tuple[int, int], tuple[tuple[int, int], tuple[int, int]]] = {}
        super().__init__(color, path, x, y)
    
    def __getstate__(self) -> dict:
        """
        Serializes the King's state (including checked status and castling rook).
        
        :return: A dictionary representing the King's state.
        """
        state = super().__getstate__()
        state["checked"] = self._checked
        state["castling_rook"] = self._castling_rook
        return state

    def __setstate__(self, state: dict) -> None:
        """
        Restores the King's state from a serialized dictionary.
        
        :param state: A dictionary representing the saved state of the King.
        """
        self._checked = bool(state.get("checked", False))
        self._castling_rook = state.get("castling_rook") or {}
        super().__setstate__(state)

    def valid_moves(self, piece_board: dict[tuple[int, int], Piece], defend_moves: bool = False) -> list[tuple[int, int]]:
        x, y = self._position
        moves: list[tuple[int, int]] = []
        
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dx, dy in directions:
            new_x, new_y = x + dx, y + dy
            if 0 > new_x or new_x > 7 or 0 > new_y or new_y > 7:
                continue
            target = piece_board.get((new_x, new_y))
            if target and target.color == self._color:
                continue
                
            moves.append((new_x, new_y))
        
        if self._first_move and not self._checked:
            self._castling(moves, piece_board)
        
        return moves
    
    def copy(self) -> "King":
        """
        Creates a copy of the King piece, including its checked status and castling rook.
        
        :return: A new instance of the King piece with the same attributes.
        """
        new_king = super().copy()
        assert isinstance(new_king, King)
        new_king._checked = self._checked
        new_king._castling_rook = self._castling_rook.copy()
        
        new_king._update_image()
        return new_king

    def check(self) -> None:
        """
        Toggles the King's check status (whether it's in check or not).
        
        Changes the checked status and updates the King's image accordingly.
        """
        self._checked = not self._checked
        self._update_image()

    def _castling(self, moves: list[tuple[int, int]], piece_board: dict[tuple[int, int], Piece]) -> None:
        """
        Calculates potential castling moves (both short and long).

        :param moves: The list of valid moves for the King to be updated with castling moves.
        :param piece_board: A dictionary representing the current state of the chessboard.
        """
        self._long_castle(moves, piece_board)
        self._short_castle(moves, piece_board)

    def _long_castle(self, moves: list[tuple[int, int]], piece_board: dict[tuple[int, int], Piece]) -> None:
        """
        Checks and adds the long castling move to the list of valid moves if conditions are met.
        
        :param moves: The list of valid moves for the King to be updated with long castling moves.
        :param piece_board: A dictionary representing the current state of the chessboard.
        """
        x, y = self._position
        dx = -1 if self._color else 1
        if (x + dx, y) in piece_board or (x + 2 * dx, y) in piece_board or (x + 3 * dx, y) in piece_board:
            return 
        potential_rook: Piece | None = piece_board.get((x + 4 * dx, y))
        if potential_rook and isinstance(potential_rook, Rook) and potential_rook.first_move:
            new_x = x + 2 * dx
            moves.append((new_x, y))
            self._special_moves.append((new_x, y))
            
            self._castling_rook[(new_x, y)] = (potential_rook.position, (new_x - dx, y))

    def _short_castle(self, moves: list[tuple[int, int]], piece_board: dict[tuple[int, int], Piece]) -> None:
        """
        Checks and adds the short castling move to the list of valid moves if conditions are met.
        
        :param moves: The list of valid moves for the King to be updated with short castling moves.
        :param piece_board: A dictionary representing the current state of the chessboard.
        """
        x, y = self._position
        dx = 1 if self._color else -1
        if (x + dx, y) in piece_board or (x + 2 * dx, y) in piece_board:
            return 
        potential_rook: Piece | None = piece_board.get((x + 3 * dx, y))
        if potential_rook and isinstance(potential_rook, Rook) and potential_rook.first_move:
            new_x = x + 2 * dx
            moves.append((new_x, y))
            self._special_moves.append((new_x, y))
            
            self._castling_rook[(new_x, y)] = (potential_rook.position, (new_x - dx, y))
        
    def _load_image(self) -> None:
        """Loads the image of the King based on whether it is in check or not."""
        color_name = "white" if self._color else "black"
        image_states_to_load = [(f"{color_name}_king.png", False), (f"checked_{color_name}_king.png", True)]

        for filename, is_checked in image_states_to_load:
            king_key = ("King", self._color, is_checked)

            if king_key not in Piece.image_cache:
                image_path: Path = self._image_dir / filename

                if not image_path.is_file():
                    raise FileNotFoundError(f"Required image file not found: {image_path}. Please check the image directory.")
                
                loaded_image = pygame.image.load(image_path).convert_alpha()
                Piece.image_cache[king_key] = loaded_image

        self._update_image()

    def _update_image(self) -> None:
        """Updates the King's image based on its current check status."""
        key = ("King", self._color, self._checked)
        self._image = Piece.image_cache[key]

    @property
    def checked(self) -> bool:
        """Returns the checked status of the King."""
        return self._checked
    
    @property
    def castling_rook(self) -> dict[tuple[int, int], tuple[tuple[int, int], tuple[int, int]]]:
        """Returns the castling rook dictionary, mapping the King's castling destination to the corresponding rook's position."""
        return self._castling_rook