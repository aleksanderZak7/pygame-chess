import pygame
from pathlib import Path

from . import ScreenBase


class GameScreen(ScreenBase):
    """
    Manages UI elements specific to the game loop screen.
    """
    __slots__ = ("_btn_size", "_label_x", "_label_y")
    
    @staticmethod
    def draw_promotion_panel(images: list[pygame.surface.Surface]) -> tuple[int, int, int, int]:
        """
        Draws the pawn promotion selection panel overlaid on the center board.

        :param images: A list of four pygame.Surface objects representing the pieces a pawn can be promoted to (Knight, Queen, Rook, Bishop).
        :return: A tuple containing the panel's (width, height, x-coordinate, y-coordinate).
        """
        screen: pygame.surface.Surface = pygame.display.get_surface()
        
        panel_width, panel_height = ScreenBase.HEIGHT // 2, ScreenBase.HEIGHT // 8
        panel_x = (ScreenBase.HEIGHT - panel_width) // 2
        panel_y = (ScreenBase.HEIGHT - panel_height) // 2
        square_size = panel_width // 4
        
        panel = pygame.surface.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill(ScreenBase.PANEL_BACKGROUND)
        pygame.draw.rect(panel, ScreenBase.RED, panel.get_rect(), 4)

        square_size = panel_width // 4
        for i in range(4):
            image = pygame.transform.scale(images[i], (square_size, panel_height))
            panel.blit(image, (i * square_size, 0))

        screen.blit(panel, (panel_x, panel_y))
        return panel_width, panel_height, panel_x, panel_y
    
    def __init__(self, screen: pygame.surface.Surface) -> None:
        """
        Initializes the GameScreen, setting up side panel button states, sizes, and positions.

        :param screen: The main pygame screen surface (pygame.Surface) to draw on.
        """
        super().__init__(screen)
        self._is_button_pressed: list[bool] = [False, False, False]
        
        self._button_dy: int = ScreenBase.BUTTON_HEIGHT + ScreenBase.MARGIN
        self._button_y: int = ScreenBase.HEIGHT - ScreenBase.BUTTON_HEIGHT - 4 * ScreenBase.MARGIN
        self._button_x: int = ScreenBase.BOARD_SIZE + ((ScreenBase.WIDTH - ScreenBase.BOARD_SIZE - ScreenBase.BUTTON_WIDTH) // 2)
        
        self._btn_size = ScreenBase.BUTTON_WIDTH // 4
        self._label_y: float = 3 * ScreenBase.SQUARE_SIZE / 2
        self._label_x: int = self._button_x + ScreenBase.BUTTON_WIDTH // 2
    
    def screen_initialization(self, height_margin: int = 0, game_over: bool = False, winner: str| None = None) \
    -> tuple[pygame.rect.Rect, pygame.rect.Rect, pygame.rect.Rect, list[tuple[pygame.surface.Surface, pygame.rect.Rect, str]], pygame.rect.Rect | None]:
        """
        Initializes side panel elements and returns Rects for interaction.

        :param height_margin: Optional vertical margin used for position calculations. Defaults to 0.
        :param game_over: Boolean indicating if the game has ended (to show the turn around button). Defaults to False.
        :param winner: A string "White" or "Black", or None if the game ended in a draw or is still in progress. Defaults to None.
        :return: A tuple containing:
        - Rect for the return button.
        - Rect for the restart button.
        - Rect for the surrender button.
        - List of tuples for move history buttons: (image_surface, rect, action_string).
        - Rect for the turn around button, or None if game is not over.
        """
        self.fill_background()
        
        if game_over:
            self.draw_winner_info(winner)
        
        return_button: pygame.rect.Rect = self._button_initialization(height_margin)
        height_margin += 1
        restart_button: pygame.rect.Rect = self._button_initialization(height_margin)
        height_margin += 1
        surrender_button: pygame.rect.Rect = self._button_initialization(height_margin)
        height_margin += 2
        
        move_buttons: list[tuple[pygame.surface.Surface, pygame.rect.Rect, str]] = self._image_buttons_initialization(height_margin)
        self.draw_image_buttons(move_buttons)
        height_margin += 1
                                
        turn_around_button: pygame.rect.Rect | None = self.draw_rotate_button(height_margin) if game_over else None
        
        return return_button, restart_button, surrender_button, move_buttons, turn_around_button
    
    def draw_buttons(self, height_margin: int = 0) -> None:
        """
        Draws the main action buttons ('Return', 'Restart', 'Surrender') in the side panel.

        :param height_margin: Optional vertical margin used for position calculations. Defaults to 0.
        """
        self._draw_button("Return to Menu", height_margin, self._is_button_pressed[height_margin])
        height_margin += 1
        self._draw_button("Restart Game", height_margin, self._is_button_pressed[height_margin])
        height_margin += 1
        self._draw_button("Surrender", height_margin, self._is_button_pressed[height_margin])
    
    def draw_image_buttons(self, move_buttons: list[tuple[pygame.surface.Surface, pygame.rect.Rect, str]]) -> None:
        """
        Draws the small image-based buttons used for move history navigation (first, prev, next, last).

        :param move_buttons: The list of tuples for move history buttons.
        """
        for image, btn_rect, _ in move_buttons:
            self._screen.blit(image, btn_rect.topleft)
    
    def draw_rotate_button(self, height_margin: int = 5) -> pygame.Rect:
        """
        Draws a single, centered image button in the side panel, typically used after game over.

        :param height_margin: Optional vertical margin used for position calculations. Defaults to 5.
        :raises FileNotFoundError: If the button image file is not found.
        :return: The pygame.Rect representing the drawn button's area.
        """
        button_x: int = ScreenBase.BOARD_SIZE + ((ScreenBase.WIDTH - ScreenBase.BOARD_SIZE - ScreenBase.BUTTON_WIDTH // 2) // 2 + self._btn_size // 2)
        button_y: int = self._button_y - height_margin * self._button_dy
        
        img_path: Path = Path(ScreenBase.IMG_DIR) / "buttons" / "rotate.png"
            
        if not img_path.is_file():
            raise FileNotFoundError(f"Required image file not found: {img_path}. Please check the image directory.")
        image = pygame.image.load(img_path)
        image = pygame.transform.scale(image, (self._btn_size, self._btn_size))


        rect = pygame.Rect(button_x, button_y, self._btn_size, self._btn_size)
        self._screen.blit(image, rect.topleft)

        return rect
    
    def draw_info(self, info: str) -> None: 
        """
        Draws an informational text label (e.g., 'White's Turn', 'Check!') centered within a bordered box in the side panel.

        :param info: The string message to display.
        """
        text_surface: pygame.surface.Surface = self._font.render(info, True, ScreenBase.WHITE)
        text_rect: pygame.rect.Rect = text_surface.get_rect(center=(self._label_x, self._label_y))

        background_x: int = ScreenBase.BOARD_SIZE + ScreenBase.MARGIN
        background_width: int = ScreenBase.WIDTH - ScreenBase.BOARD_SIZE - 2 * ScreenBase.MARGIN
        background_height: int = text_rect.height + 5 * ScreenBase.MARGIN
        background_y: int = text_rect.centery - background_height // 2

        background_rect: pygame.Rect = pygame.Rect(background_x, background_y, background_width, background_height)

        pygame.draw.rect(self._screen, ScreenBase.BLACK, background_rect, border_radius=6)
        
        inner_rect: pygame.rect.Rect = background_rect.inflate(-4, -4)
        pygame.draw.rect(self._screen, ScreenBase.BACKGROUND_GRAY, inner_rect, border_radius=4)

        self._screen.blit(text_surface, text_rect)
    
    def draw_winner_info(self, winner: str | None) -> None:
        """
        Displays the winner of the game ('White won!' or 'Black won!') in the side panel if a winner is provided.

        :param winner: A string "White" or "Black", or None if the game ended in a draw.
        """
        if not winner:
            return
        y_label: float = self._label_y - self._button_dy // 2 - ScreenBase.MARGIN
        
        winner_font = pygame.font.Font(ScreenBase.FONT_PATH, 15)
        winner_surface: pygame.surface.Surface = winner_font.render(f"{winner} won!", True, ScreenBase.WHITE)
        winner_rect: pygame.rect.Rect = winner_surface.get_rect(center=(self._label_x, y_label))
        
        self._screen.blit(winner_surface, winner_rect.topleft)
    
    def _image_buttons_initialization(self, height_margin: int = 4) -> list[tuple[pygame.surface.Surface, pygame.rect.Rect, str]]:
        """
        Loads images, creates Rects, and prepares data for the small image-based buttons used for move history navigation (first, prev, next, last).

        :param height_margin: Optional vertical margin used for position calculations. Defaults to 4.
        :raises FileNotFoundError: If any required button image file is not found.
        :return: A list of tuples, where each tuple contains: (image_surface, button_rect, action_string).
        """
        button_x: int = self._button_x
        button_y: int = self._button_y - height_margin * self._button_dy
        button_actions: tuple[str, str, str, str] = ("first_move", "previous_move", "next_move", "last_move")
        
        dir_path: Path = Path(ScreenBase.IMG_DIR) / "buttons"
        buttons:list[tuple[pygame.surface.Surface, pygame.rect.Rect, str]] = []
        
        for i, action in enumerate(button_actions):
            filename: str = action + ".png"
            img_path: Path = dir_path / filename
            x: int = button_x + i * (self._btn_size)
            rect = pygame.Rect(x, button_y, self._btn_size, self._btn_size)
            
            if not img_path.is_file():
                raise FileNotFoundError(f"Required image file not found: {img_path}. Please check the image directory.")
            image = pygame.image.load(img_path)
            image = pygame.transform.scale(image, (self._btn_size, self._btn_size))

            buttons.append((image, rect, action))
        
        return buttons