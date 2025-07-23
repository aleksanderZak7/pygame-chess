import pygame
from pathlib import Path
from abc import ABC, abstractmethod


class Piece(ABC):
    """
    Abstract base class for all chess pieces.
    """
    image_cache: dict[tuple[str, int, bool | None], pygame.surface.Surface] = {}

    __slots__ = ("_color", "_image_dir", "_position", "_image")

    def __init__(self, color: int, path: Path, x: int, y: int) -> None:
        """
        Initializes a piece with color, image path and position.

        :param color: 0 for black, 1 for white.
        :param path: Directory where piece images are stored.
        :param x: Initial x-position on the board.
        :param y: Initial y-position on the board.
        """
        self._color: int = color
        self._image_dir: Path = path
        self._position: tuple[int, int] = (x, y)
        self._image: pygame.surface.Surface | None = None

        self._load_image()
    
    def __getstate__(self) -> dict:
        """
        Used for object serialization with pickle.

        :return: Serializable state.
        """
        return {
            "color": self._color,
            "image_dir": self._image_dir,
            "position": self._position,
        }

    def __setstate__(self, state: dict) -> None:
        """
        Used for object deserialization.

        :param state: Restored state.
        """
        self._image = None
        self._color = state["color"]
        self._position = state["position"]
        self._image_dir = state["image_dir"]
        self._load_image()

    def __eq__(self, other: object) -> bool:
        """
        Compares two pieces by type, color, and position.

        :param other: Another chess piece.
        :return: True if pieces are equivalent.
        """
        if not isinstance(other, Piece):
            return NotImplemented
        return (self._color == other.color and self._position == other.position and self.__class__ == other.__class__)

    @abstractmethod
    def valid_moves(self, piece_board: dict[tuple[int, int], "Piece"], defend_moves: bool = False) -> list[tuple[int, int]]:
        """
        Calculates all valid move positions for this piece.

        :param piece_board: A dictionary representing all pieces on the board with their positions as keys.
        :param defend_moves: If True, includes squares this piece *could* attack, even if blocked or illegal in standard move logic. Defaults to False.
        :return: A list of coordinate tuples indicating possible target squares.
        """
        pass

    def draw(self, screen: pygame.surface.Surface, square_size: int) -> None:
        """
        Draws the piece on the screen at its current position.

        :param screen: The surface to draw the piece on.
        :param square_size: The size of each square on the chessboard.
        :raises ValueError: If the image is not loaded.
        """
        x, y = self._position
        if not self._image:
            raise ValueError("Image not loaded! Cannot draw piece on the screen.")
        screen.blit(self._image, (x * square_size, y * square_size))

    def move(self, x: int, y: int) -> None:
        """
        Updates the piece's position.

        :param x: New x-position.
        :param y: New y-position.
        """
        self._position = (x, y)

    def copy(self) -> "Piece":
        """
        Creates a copy of this piece.

        :return: New instance of the same piece.
        """
        return self.__class__(self._color, self._image_dir, *self._position)

    def _load_image(self) -> None:
        """
        Loads the image from disk and caches it for reuse.
        
        :raises FileNotFoundError: If the piece image file is not found.
        """
        key = (self.__class__.__name__, self._color, None)
        if key not in Piece.image_cache:
            color_str = "white" if self._color == 1 else "black"
            filename: str = f"{color_str}_{self.__class__.__name__}.png".lower()
            
            image_path: Path = self._image_dir / filename
            if not image_path.is_file():
                raise FileNotFoundError(f"Required image file not found: {image_path}. Please check the image directory.")
            
            image = pygame.image.load(image_path).convert_alpha()
            Piece.image_cache[key] = image
            
        self._image = Piece.image_cache[key]

    @property
    def color(self) -> int:
        """Returns the piece's color."""
        return self._color

    @property
    def image_dir(self) -> Path:
        """Returns the directory for this piece's image."""
        return self._image_dir

    @image_dir.setter
    def image_dir(self, value: Path) -> None:
        """
        Updates image directory and reloads the image.

        :param value: New directory path.
        """
        assert value.is_dir(), "Invalid path for image dir!"
        self._image_dir = value
        self._load_image()

    @property
    def position(self) -> tuple[int, int]:
        """Returns the current position of the piece."""
        return self._position

    @position.setter
    def position(self, value: tuple[int, int]) -> None:
        """
        Sets the position of the piece.

        :param value: New position (x, y).
        """
        assert 0 <= value[0] < 8 and 0 <= value[1] < 8, "Invalid position! Position must be within the board."
        self._position = value
    
    @property
    def image(self) -> pygame.surface.Surface | None:
        """Returns the image surface of the piece."""
        return self._image


class SpecialPiece(Piece):
    """
    A subclass of Piece with special movement properties (pawn, king, rook).
    Tracks whether it's the first move and stores temporary special moves.
    """
    __slots__ = ("_first_move", "_special_moves")

    def __init__(self, color: int, path: Path, x: int, y: int) -> None:
        """
        Initializes a special piece with first-move and special-move tracking.

        :param color: 0 for black, 1 for white.
        :param path: Directory where piece images are stored.
        :param x: Initial x-position.
        :param y: Initial y-position.
        """
        super().__init__(color, path, x, y)
        self._first_move: bool = True
        self._special_moves: list[tuple[int, int]] = []
    
    def __getstate__(self) -> dict:
        """
        Serializes the special piece state.

        :return: Dictionary representing the internal state.
        """
        state = super().__getstate__()
        state["first_move"] = self._first_move
        state["special_moves"] = self._special_moves
        return state

    def __setstate__(self, state: dict) -> None:
        """
        Restores the special piece state.

        :param state: Saved internal state.
        """
        super().__setstate__(state)
        self._first_move = state["first_move"]
        self._special_moves = state["special_moves"]

    def move(self, x: int, y: int) -> None:
        """
        Overrides the move method to reset special state after moving.

        :param x: New x-position.
        :param y: New y-position.
        """
        super().move(x, y)
        if self._special_moves:
            self._special_moves.clear()
        if self._first_move:
            self._first_move = False

    def copy(self) -> "SpecialPiece":
        """
        Creates a deep copy of the special piece, including special state.

        :return: Copied SpecialPiece instance.
        """
        new_piece = self.__class__(self._color, self._image_dir, *self._position)
        new_piece._first_move = self._first_move
        new_piece._special_moves = self._special_moves.copy()
        return new_piece

    @property
    def first_move(self) -> bool:
        """Returns whether the piece has moved before."""
        return self._first_move

    @property
    def special_moves(self) -> list[tuple[int, int]]:
        """Returns the list of temporary special moves."""
        return self._special_moves