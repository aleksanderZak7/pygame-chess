import pygame
from pathlib import Path

from . import ScreenBase


class MainMenuScreen(ScreenBase):
    """
    Manages the display and interaction for the main menu screen.
    """

    def __init__(self, screen: pygame.surface.Surface) -> None:
        """
        Initializes the MainMenuScreen, setting up button states and positions.

        :param screen: The main pygame screen surface (pygame.Surface) to draw on.
        """
        super().__init__(screen)
        self._is_button_pressed: list[bool] = [False, False]
        
        self._button_dy: int = ScreenBase.BUTTON_HEIGHT + ScreenBase.MARGIN
        self._button_x: float = ScreenBase.WIDTH // 2 - ScreenBase.BUTTON_WIDTH / 2.4
        self._button_y: int = ScreenBase.HEIGHT // 2 - ScreenBase.BUTTON_HEIGHT // 4
    
    def screen_initialization(self, height_margin: int = 0) -> tuple[pygame.rect.Rect, pygame.rect.Rect]:
        """
        Initializes and returns the Rect objects for the menu buttons.

        :param height_margin: Optional vertical margin used for position calculations. Defaults to 0.
        :return: A tuple containing the pygame.Rect objects for the 'Customize' and 'Play' buttons.
        """
        customize_button: pygame.rect.Rect = self._button_initialization(height_margin)
        height_margin += 1
        play_button: pygame.rect.Rect = self._button_initialization(height_margin)
        
        return customize_button, play_button
    
    def draw_buttons(self, height_margin: int = 0) -> None:
        """
        Draws the 'Customize' and 'Play' buttons on the screen.

        :param height_margin: Optional vertical margin used for position calculations. Defaults to 0.
        """
        self._draw_button("Customize", height_margin, self._is_button_pressed[height_margin], reduction=1.2)
        height_margin += 1
        self._draw_button("Play", height_margin, self._is_button_pressed[height_margin], reduction=1.2)

    def draw_menu(self) -> None:
        """Draws all elements of the main menu screen, including background, title, subtitle, and decorative images."""
        self.fill_background()
        menu_images = self._prepare_menu_images()
        title_surface, title_pos, subtitle_surface, subtitle_pos = self._prepare_title()
        self._screen.blit(title_surface, title_pos)
        self._screen.blit(subtitle_surface, subtitle_pos)

        for image, pos in menu_images:
            self._screen.blit(image, pos)

    def draw_reload_game_panel(self) -> pygame.Rect:
        """
        Draws a semi-transparent panel asking the user if they want to load the previous game.

        :return: The pygame.Rect object for the 'No' button.
        """
        panel_width = ScreenBase.BUTTON_WIDTH * 2
        panel_height = ScreenBase.BUTTON_HEIGHT * 3
        panel_x = (ScreenBase.WIDTH - panel_width) // 2
        panel_y = (ScreenBase.HEIGHT - panel_height) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill(ScreenBase.PANEL_BACKGROUND)
        self._screen.blit(panel_surface, (panel_x, panel_y))

        pygame.draw.rect(self._screen, ScreenBase.WHITE, panel_rect, 2, border_radius=10)

        question_font = pygame.font.Font(ScreenBase.FONT_PATH, 24)
        question_label = question_font.render("Load previous game?", True, ScreenBase.WHITE)
        question_pos_x = panel_x + (panel_width - question_label.get_width()) // 2
        question_pos_y = panel_y + 3 * ScreenBase.MARGIN
        self._screen.blit(question_label, (question_pos_x, question_pos_y))

        item_w = ScreenBase.BUTTON_WIDTH // 2
        item_h = ScreenBase.BUTTON_HEIGHT - 2 * ScreenBase.MARGIN
        item_y = panel_y + panel_height - ScreenBase.SQUARE_SIZE

        gap = 30
        border_thickness: int = 5
        yes_x = panel_x + (panel_width // 2) - item_w - (gap // 2)
        yes_outer_rect = pygame.Rect(yes_x, item_y, item_w, item_h)
        pygame.draw.rect(self._screen, ScreenBase.BLACK, yes_outer_rect, border_radius=10)

        yes_inner_rect: pygame.Rect = pygame.Rect(yes_x + border_thickness, item_y + border_thickness,
                                                 item_w - 2 * border_thickness, item_h - 2 * border_thickness
                                                 )
        pygame.draw.rect(self._screen, ScreenBase.BUTTON_GREEN, yes_inner_rect, border_radius=8)

        yes_text_surface = self._font.render("Yes", True, ScreenBase.WHITE)
        yes_text_x = yes_x + (item_w - yes_text_surface.get_width()) // 2
        yes_text_y = item_y + (item_h - yes_text_surface.get_height()) // 2
        self._screen.blit(yes_text_surface, (yes_text_x, yes_text_y))

        no_x = panel_x + (panel_width // 2) + (gap // 2)
        no_rect = pygame.Rect(no_x, item_y, item_w, item_h)
        pygame.draw.rect(self._screen, ScreenBase.BLACK, no_rect, border_radius=10)

        no_inner_rect: pygame.Rect = pygame.Rect(no_x + border_thickness, item_y + border_thickness,
                                                item_w - 2 * border_thickness, item_h - 2 * border_thickness
                                                )
        pygame.draw.rect(self._screen, ScreenBase.BUTTON_RED, no_inner_rect, border_radius=8)

        no_label_surface: pygame.surface.Surface = self._font.render("No", True, ScreenBase.WHITE)
        no_label_x = no_x + (item_w - no_label_surface.get_width()) // 2
        no_label_y = item_y + (item_h - no_label_surface.get_height()) // 2
        self._screen.blit(no_label_surface, (no_label_x, no_label_y))

        return no_rect

    def _prepare_title(self) -> tuple[pygame.surface.Surface, tuple[int, int], pygame.surface.Surface, tuple[int, int]]:
        """
        Renders the main title and subtitle surfaces and calculates their positions.
        
        :return: A tuple containing:
                 (title surface, title position, subtitle surface, subtitle position).
        """
        title_font = pygame.font.Font(ScreenBase.FONT_PATH, 80)
        subtitle_font = pygame.font.Font(ScreenBase.FONT_PATH, 15)

        title_surface: pygame.surface.Surface = title_font.render("ChessGame", True, ScreenBase.WHITE)
        
        title_x: int = (ScreenBase.WIDTH - title_surface.get_width()) // 2
        title_y: int = 100
        subtitle_surface: pygame.surface.Surface = subtitle_font.render("pixelart", True, ScreenBase.WHITE)

        subtitle_x = title_x + title_surface.get_width() + 10
        subtitle_y = title_y + (title_surface.get_height() - subtitle_surface.get_height()) // 2
        
        return title_surface, (title_x, title_y), subtitle_surface, (subtitle_x - subtitle_x // 10, subtitle_y + subtitle_y // 2)

    def _prepare_menu_images(self) -> list[tuple[pygame.surface.Surface, tuple[int, int]]]:
        """
        Loads, scales, optionally rotates, and positions decorative chess piece images for the main menu background.

        :raises FileNotFoundError: If any required image file is not found in the expected directory ('utils/img/Classic/').
        :return: A list of tuples, each containing a transformed image surface and its calculated (x, y) position.
        """
        image_size: int = 200
        img_path = Path(ScreenBase.IMG_DIR) / "Classic"
        try:
            paths = {
                "rook": "white_rook.png",
                "king": "white_king.png",
                "queen": "black_queen.png",
                "bishop": "black_bishop.png",
                "knight": "white_knight.png",
                "checked_king": "checked_black_king.png"
            }
            images = {name: pygame.image.load(img_path / path) for name, path in paths.items()}
        except FileNotFoundError:
            raise FileNotFoundError("Image files not found! Please check the img directory.")

        transformations = {"rook": (0, 0), "king": (0, 0), "queen": (330, 0), "bishop": (330, 0), "knight": (30, 0), "checked_king": (300, 0)}

        for name, (rotation, _) in transformations.items():
            images[name] = pygame.transform.scale(images[name], (image_size, image_size))
            if rotation != 0:
                images[name] = pygame.transform.rotate(images[name], rotation)

        left_x = ScreenBase.MARGIN
        left_y = ScreenBase.HEIGHT // 2
        right_x = ScreenBase.WIDTH // 2 + image_size // 2
        right_y = ScreenBase.HEIGHT // 4 + image_size // 4

        return [
            (images["rook"], (left_x, left_y)),
            (images["rook"], (left_x + image_size, left_y)),
            (images["queen"], (left_x - image_size // 2, ScreenBase.HEIGHT // 8)),
            (images["bishop"], (left_x - image_size // 2 - ScreenBase.MARGIN, ScreenBase.HEIGHT // 10 - image_size // 2)),
            (images["king"], (left_x + image_size // 2, left_y + image_size // 4)),
            (images["knight"], (right_x, right_y)),
            (images["checked_king"], (right_x + image_size // 2, left_y + image_size // 4))
        ]