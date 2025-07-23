import sys
import pygame
from pathlib import Path
from abc import ABC, abstractmethod

from src import pieces


class ScreenBase(ABC):
    """
    Abstract base class for managing UI elements in the game.
    """
    __slots__ = ("_screen", "_font", "_is_button_pressed", "_button_x", "_button_y", "_button_dy")
    
    MARGIN: int = 10
    BUTTON_HEIGHT: int = 70
    BUTTON_WIDTH: int = 300

    SQUARE_SIZE: int = 95
    BOARD_SIZE: int = SQUARE_SIZE * 8

    HEIGHT: int = BOARD_SIZE
    WIDTH: int = BOARD_SIZE + 2 * MARGIN + BUTTON_WIDTH
    
    IMG_DIR: Path = Path(sys.path[0]) / "src" / "project_assets" / "img"
    FONT_PATH: Path = Path(sys.path[0]) / "src" / "project_assets" / "pixel_font.ttf"

    BLACK: tuple[int, int, int] = (0, 0, 0)
    RED: tuple[int, int, int] = (255, 0, 0)
    BUTTON_RED: tuple[int, int, int] = (178, 34, 34)
    BUTTON_GREEN: tuple[int, int, int] = (34, 139, 34)
    BUTTON_PRESSED: tuple[int, int, int] = (100, 100, 100)
    GRAY: tuple[int, int, int, int] = (131, 139, 139, 255)
    WHITE: tuple[int, int, int, int] = (255, 255, 255, 255)
    BACKGROUND_GRAY: tuple[int, int, int, int] = (51, 51, 51, 255)
    PANEL_BACKGROUND: tuple[int, int, int, int] = (40, 40, 40, 210)
    
    @staticmethod
    def create_screen() -> pygame.surface.Surface:
        """
        Creates and returns the main game window surface based on class dimensions.

        :return: The main pygame screen surface.
        """
        return pygame.display.set_mode((ScreenBase.WIDTH, ScreenBase.HEIGHT))

    def __init__(self, screen: pygame.surface.Surface) -> None:
        """
        Initializes the Screen object with the screen surface and font.

        :param screen: The main pygame screen surface (pygame.Surface) to draw on.
        """
        self._screen: pygame.surface.Surface = screen
        self._font: pygame.font.Font = pygame.font.Font(ScreenBase.FONT_PATH, 20)
        
    def __getitem__(self, key: int) -> bool:
        """
        Gets the pressed state of a button at the specified index.

        :param key: The index of the button.
        :raises IndexError: If the index is out of range.
        :return: The pressed state (True or False).
        """
        if key >= len(self._is_button_pressed):
            raise IndexError("Button index out of range.")
        
        return self._is_button_pressed[key]
    
    def __setitem__(self, key: int, value: bool) -> None:
        """
        Sets the pressed state of a button at the specified index.

        :param key: The index of the button.
        :param value: The pressed state (True or False).
        :raise IndexError: If the index is out of range.
        :raises TypeError: If the provided value is not a boolean.
        """
        if key >= len(self._is_button_pressed):
            raise IndexError("Button index out of range.")
        
        if not isinstance(value, bool):
            raise TypeError("Invalid check value! Must be a boolean (True or False).")
        
        self._is_button_pressed[key] = value
    
    @abstractmethod
    def screen_initialization(self, height_margin: int = 0) -> tuple:
        """
        Abstract method for screen initialization in subclasses.
        
        :param height_margin: Optional vertical margin used for position calculations. Defaults to 0.
        :return: A tuple containing calculated button positions.
        """
        pass
    
    @abstractmethod
    def draw_buttons(self, height_margin: int = 0) -> None:
        """
        Abstract method responsible for drawing all specific buttons for a given screen.

        :param height_margin: Optional vertical margin used for position calculations. Defaults to 0.
        """
        pass
        
    def fill_background(self) -> None:
        """Fills the entire screen with the defined background color."""
        self._screen.fill(ScreenBase.BACKGROUND_GRAY)
    
    def reset_button_states(self) -> None:
        """Resets the pressed state of all buttons to False."""
        for i in range(len(self._is_button_pressed)):
            self._is_button_pressed[i] = False
    
    def draw_board(self, board_img: pygame.surface.Surface, chess_board: dict[tuple[int, int], pieces.Piece], valid_moves: list[tuple[int, int]]) -> None:
        """
        Draws the chessboard background, all pieces, and valid move indicators.

        :param board_img: The pre-rendered surface of the chessboard background.
        :param chess_board: The current state of the chessboard dictionary.
        :param valid_moves: A list storing currently displayed valid moves. Moves are indicated by circles (empty squares) or crosses (captures).
        """
        self._screen.blit(board_img, (0, 0))
        square_size: int = ScreenBase.SQUARE_SIZE
        
        for piece in chess_board.values():
            piece.draw(self._screen, square_size)
            
        if valid_moves:
            half_square: int = square_size // 2
            quarter_square: int = square_size // 4
            
            for move in valid_moves:
                x, y = move
                center_x = x * square_size + half_square
                center_y = y * square_size + half_square
                if chess_board.get((x, y)):
                    pygame.draw.line(self._screen, ScreenBase.RED, 
                                 (center_x - quarter_square, center_y - quarter_square), 
                                 (center_x + quarter_square, center_y + quarter_square), 3)
                    pygame.draw.line(self._screen, ScreenBase.RED, 
                                 (center_x + quarter_square, center_y - quarter_square), 
                                 (center_x - quarter_square, center_y + quarter_square), 3)
                else:
                    pygame.draw.circle(self._screen, ScreenBase.BLACK, (center_x, center_y), quarter_square, 5)

    def _button_initialization(self, height_margin: int,  reduction: float = 1) -> pygame.rect.Rect:
        """
        Calculates and returns the rectangle defining a button's area.

        :param height_margin: Vertical margin used for position calculations.
        :param reduction: Factor to reduce the button width. Defaults to 1 (no reduction).
        :return: A pygame.Rect object representing the button's area.
        """
        button_width: float = ScreenBase.BUTTON_WIDTH / reduction
        button_y: int = self._button_y - height_margin * self._button_dy
        
        return pygame.rect.Rect(self._button_x, button_y, button_width, ScreenBase.BUTTON_HEIGHT)
    
    def _draw_button(self, text: str, height_margin: int, is_pressed: bool, reduction: float = 1) -> None:
        """
        Draws a single button with text, border, and appropriate color based on pressed state.
        
        :param text: The text to be displayed on the button.
        :param height_margin: Vertical margin used for position calculations.
        :param is_pressed: Boolean indicating if the button is pressed.
        :param reduction: Factor to reduce the button width. Defaults to 1 (no reduction).
        """
        button_x: int = self._button_x
        button_hight: int = ScreenBase.BUTTON_HEIGHT
        button_width: float = ScreenBase.BUTTON_WIDTH / reduction
        button_y: int = self._button_y - height_margin * self._button_dy
        
        border_radius: int = 10
        border_thickness: int = 5
        inner_border_radius: int = 8
        rect: pygame.Rect = pygame.Rect(button_x, button_y, button_width, button_hight)
        
        pygame.draw.rect(self._screen, ScreenBase.BLACK, rect, border_radius=border_radius)
        inner_rect: pygame.Rect = pygame.Rect(button_x + border_thickness, button_y + border_thickness, button_width - 2 * border_thickness, button_hight - 2 * border_thickness)
        
        color: tuple = ScreenBase.BUTTON_PRESSED if is_pressed else ScreenBase.GRAY
        pygame.draw.rect(self._screen, color, inner_rect, border_radius=inner_border_radius)

        label: pygame.surface.Surface = self._font.render(text, True, ScreenBase.WHITE)
        self._screen.blit(label, (button_x + (button_width - label.get_width()) // 2, button_y + (button_hight - label.get_height()) // 2))