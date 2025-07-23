from . import Piece
from pathlib import Path


class Bishop(Piece):
    """
    Class representing a bishop chess piece.
    """
    def __init__(self, color: int, path: Path, x: int, y: int) -> None:
        super().__init__(color, path, x, y)
    
    def valid_moves(self, piece_board: dict[tuple[int, int], Piece], defend_moves: bool = False) -> list[tuple[int, int]]:
        x, y = self._position
        moves: list[tuple[int, int]] = []
        
        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        for dx, dy in directions:
            new_x, new_y = x, y
            while True:
                new_x += dx
                new_y += dy
                if 0 > new_x or new_x > 7 or 0 > new_y or new_y > 7:
                    break
                target = piece_board.get((new_x, new_y))
                if target:
                    if target.color == self._color:
                        if defend_moves:
                            moves.append((new_x, new_y))
                        break
                    moves.append((new_x, new_y))
                    break
                moves.append((new_x, new_y))
                
        return moves