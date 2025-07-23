import pygame
from pathlib import Path

from . import ScreenBase


class CustomizeScreen(ScreenBase):
    """
    Manages the display and interaction for the theme customization menu,
    allowing users to select different visual themes for the game.
    """
    __slots__ = ("_theme_button_x",)
    
    def __init__(self, screen: pygame.surface.Surface) -> None:
        """
        Initializes the CustomizeScreen, setting up button state and positions for the return button and the theme selection area.

        :param screen: The main pygame screen surface (pygame.Surface) to draw on.
        """
        super().__init__(screen)
        self._is_button_pressed: list [bool] = [False]
        
        self._button_dy: int = ScreenBase.BUTTON_HEIGHT + ScreenBase.MARGIN
        self._button_y: int = ScreenBase.HEIGHT - ScreenBase.BUTTON_HEIGHT - 4 * ScreenBase.MARGIN
        self._button_x: int = ScreenBase.BOARD_SIZE + ((ScreenBase.WIDTH - ScreenBase.BOARD_SIZE - ScreenBase.BUTTON_WIDTH) // 2)
        
        self._theme_button_x: int = ScreenBase.BOARD_SIZE + (ScreenBase.WIDTH - ScreenBase.BOARD_SIZE - ScreenBase.BUTTON_WIDTH) // 2
    
    def screen_initialization(self, height_margin = 0) -> tuple[pygame.rect.Rect, list[tuple[pygame.rect.Rect, str]]]:
        """
        Initializes side panel elements and returns Rects for interaction.

        :param height_margin: Optional vertical margin used for position calculations. Defaults to 0.
        :return: A tuple containing:
        - The pygame.Rect for the 'Return to Menu' button.
        - A list of tuples [(theme_button_rect, theme_name)] for each available theme.
        """
        self.fill_background()
        
        return_button: pygame.rect.Rect = self._button_initialization(height_margin)
        themes: list[tuple[pygame.rect.Rect, str]] = self._themes_initialization()
        
        return return_button, themes
    
    def draw_buttons(self, height_margin = 0) -> None:
        """
        Draws the 'Return to Menu' button in the side panel.

        :param height_margin: Optional vertical margin used for position calculations. Defaults to 0.
        """
        self._draw_button("Return to Menu", height_margin, self._is_button_pressed[height_margin])
        
    def _themes_initialization(self) -> list[tuple[pygame.rect.Rect, str]]:
        """
        Identifies available themes by scanning directories, draws a button for each and returns data needed for click detection.

        :return: A list of tuples, where each tuple contains (button_rect, theme_name)
                 for each theme found and drawn. Returns an empty list if no themes are found.
        """
        img_dir: Path = ScreenBase.IMG_DIR
        themes: list[str] = [d.name for d in img_dir.iterdir() if d.name != "buttons"] if img_dir.exists() else []
        
        return [(self._draw_image_button(theme, self._theme_button_x, ScreenBase.MARGIN + i * self._button_dy)) for i, theme in enumerate(themes)]
    
    def _draw_image_button(self, theme: str, x: int, y: int) -> tuple[pygame.rect.Rect, str]:
        """
        Helper method to draw a button specifically for theme selection.
        Displays a preview image of the theme's board alongside the theme name.

        :param theme: The name of the theme (used to find the image and display text).
        :param x: The x-coordinate of the top-left corner of the button.
        :param y: The y-coordinate of the top-left corner of the button.
        
        :raises FileNotFoundError: If the theme's board preview image is not found.
        :return: The pygame.Rect representing the drawn button's area.
        """
        height: int = ScreenBase.BUTTON_HEIGHT
        rect: pygame.rect.Rect = pygame.rect.Rect(x, y, ScreenBase.BUTTON_WIDTH, height)
        pygame.draw.rect(self._screen, ScreenBase.BACKGROUND_GRAY, rect, border_radius=10)

        image_size: int = 75
        img_path: Path = Path(ScreenBase.IMG_DIR) / theme / "board.png"
        if not img_path.is_file():
            raise FileNotFoundError(f"Required image file not found: {img_path}. Please check the image directory.")
            
        board_img: pygame.surface.Surface = pygame.image.load(img_path)
        board_img = pygame.transform.scale(board_img, (image_size, image_size))
        self._screen.blit(board_img, (x + 10 , y + (height - image_size) // 2))
            
        label: pygame.surface.Surface = self._font.render(theme, True, ScreenBase.WHITE)
        self._screen.blit(label, (x + image_size + 30, y + (height - label.get_height()) // 2))
            
        return rect, theme