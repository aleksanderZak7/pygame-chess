from pathlib import Path
from . import Piece, SpecialPiece


class Pawn(SpecialPiece):
    """
    Class representing a pawn chess piece.
    """
    __slots__ = ()

    def __init__(self, color: int, path: Path, x: int, y: int) -> None:
        super().__init__(color, path, x, y)

    def valid_moves(self, piece_board: dict[tuple[int, int], Piece], defend_moves: bool = False) -> list[tuple[int, int]]:
        x, y = self._position
        moves: list[tuple[int, int]] = []

        if (x, y - 1) not in piece_board and not defend_moves:
            moves.append((x, y - 1))

            if self._first_move and (x, y - 2) not in piece_board:
                moves.append((x, y - 2))

        for dx in (-1, 1):
            if defend_moves:
                moves.append((x + dx, y + 1))
            else:
                target_pos = (x + dx, y - 1)
                target = piece_board.get(target_pos)
                if target and target.color != self._color:
                    moves.append(target_pos)

        return moves

    def en_passant(self, moves: list[tuple[int, int]], last_pawn_position: tuple[int, int]) -> None:
        """
        Adds a valid en passant move if conditions are met.

        :param moves: List of current valid moves (modified in-place).
        :param last_pawn: Position of the last moved pawn (used for en passant).
        """
        x, y = self._position
        enemy_x, enemy_y = last_pawn_position

        if y != 3 or enemy_y != y:
            return

        for dx in [-1, 1]:
            if x + dx == enemy_x:
                move = (x + dx, y - 1)
                moves.append(move)
                self._special_moves.append(move)
                return