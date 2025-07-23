from . import Piece
from pathlib import Path


class Knight(Piece):
    """
    Class representing a knight chess piece.
    """
    def __init__(self, color: int, path: Path, x: int, y: int) -> None:
        super().__init__(color, path, x, y)
    
    def valid_moves(self, piece_board: dict[tuple[int, int], Piece], defend_moves: bool = False) -> list[tuple[int, int]]:
        x, y = self._position
        moves: list[tuple[int, int]] = []
        
        potential_moves = (
            (x + 2, y + 1), (x + 2, y - 1),
            (x - 2, y + 1), (x - 2, y - 1),
            (x + 1, y + 2), (x + 1, y - 2),
            (x - 1, y + 2), (x - 1, y - 2),
        )
        
        for new_x, new_y in potential_moves:
            if 0 <= new_x < 8 and 0 <= new_y < 8:
                target = piece_board.get((new_x, new_y))
                if target is None or target.color != self._color:
                    moves.append((new_x, new_y))
                elif defend_moves:
                    moves.append((new_x, new_y))
        
        return moves