import sys
import pygame
from pathlib import Path
from threading import Thread

from .chess_board import ChessBoard
from src import ScreenBase, MainMenuScreen, GameScreen, CustomizeScreen


class ChessGame:
    """
    Main application class for the Chess Game. Initializes pygame, manages screen views, handles main event loops and coordinates game state through the ChessBoard instance.
    """
    __slots__ = ("_fps", "_running", "_screen", "_audio_dir", "_board", "_start_game_sound", "_menu_return_sound", "_custom_menu_sound", "_change_theme_sound")

    def __init__(self, fps: int = 20) -> None:
        """
        Initializes the ChessGame application, including pygame, the display window, audio mixer and the main ChessBoard instance.

        :param fps: The target frames per second for the game loops. Defaults to 20.
        """
        self._fps: int = fps
        self._running: bool = True
              
        pygame.init()
        pygame.mixer.init()
        pygame.display.set_caption("Pygame Chess")
        pygame.display.set_icon(self._load_game_icon())
        self._screen: pygame.surface.Surface = ScreenBase.create_screen()
        self._audio_dir: Path = Path(sys.path[0]) / "src" / "project_assets" / "audio"

        self._board = ChessBoard()
        self._start_game_sound: str = "game_start"
        self._menu_return_sound: str = "menu_return"
        self._custom_menu_sound: str = "custom_menu"
        self._change_theme_sound: str = "change_theme"

    def main_menu(self) -> None:
        """Runs the main menu loop, handling user interaction for starting the game, entering the customization menu, or quitting."""
        first_launch: bool = True
        menu_view = MainMenuScreen(self._screen)
        customize_button, play_button = menu_view.screen_initialization()
        
        menu_view.draw_menu()
        menu_view.draw_buttons()
        
        clock = pygame.time.Clock()
        while self._running:
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    cursor: tuple[int, int] = event.pos
                        
                    if customize_button.collidepoint(cursor):
                        menu_view[0] = True
                    
                    elif play_button.collidepoint(cursor):
                        menu_view[1] = True
                        
                elif event.type == pygame.MOUSEBUTTONUP:
                    cursor: tuple[int, int] = event.pos
                    
                    if menu_view[0] or menu_view[1]:
                        menu_view.reset_button_states()
                        
                        if play_button.collidepoint(cursor) or customize_button.collidepoint(cursor):
                            if first_launch:
                                first_launch = False
                                self._handle_game_reload(menu_view)
                                if not self._running:
                                    break
                                
                            self._game_loop() if play_button.collidepoint(cursor) else self._customize_menu()
                            
                menu_view.draw_menu()
                menu_view.draw_buttons()

            clock.tick(self._fps)

        pygame.quit()

    def _game_loop(self) -> None:
        """Runs the main game loop, handling gameplay events like board clicks, button presses (Return, Restart, Surrender, History), 
        drawing the board and managing game state updates via the ChessBoard instance."""
        Thread(target=self._play_sound, args=(self._start_game_sound,)).start()
        
        game_view = GameScreen(self._screen)
        return_button, restart_button, surrender_button, move_buttons, turn_around_button = game_view.screen_initialization(game_over=self._board.game_over, winner=self._board.winner)
        
        game_view.draw_buttons()
        self._board.draw_board(game_view)
        game_view.draw_info(self._board.info)
        
        clock = pygame.time.Clock()
        while True:
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    Thread(target=self._board.save_board).start()
                    return

                if event.type == pygame.MOUSEBUTTONDOWN:
                    cursor: tuple[int, int] = event.pos
                    if return_button.collidepoint(cursor):
                        game_view[0] = True
                        
                    elif restart_button.collidepoint(cursor):
                        game_view[1] = True
                        
                    elif surrender_button.collidepoint(cursor):
                        game_view[2] = True
                                           
                    elif turn_around_button and turn_around_button.collidepoint(cursor):
                        Thread(target=self._play_sound, args=(self._change_theme_sound,)).start()
                        self._board.change_view(change_player=True)
                        
                    for _, btn_rect, action in move_buttons:
                        if btn_rect.collidepoint(cursor):
                            self._handle_move_action(action)
                            break

                    self._handle_board_click(cursor)

                elif event.type == pygame.MOUSEBUTTONUP:
                    cursor: tuple[int, int] = event.pos
                    
                    if game_view[0] or game_view[1] or game_view[2]:
                        game_view.reset_button_states()

                        if return_button.collidepoint(cursor):
                            Thread(target=self._board.save_board).start()
                            Thread(target=self._play_sound, args=(self._menu_return_sound,)).start()
                            return
                        
                        elif restart_button.collidepoint(cursor):
                            self._board.reset()
                            turn_around_button = None
                            Thread(target=self._play_sound, args=(self._start_game_sound,)).start()
                            
                            game_view.fill_background()
                            game_view.draw_image_buttons(move_buttons)
                        
                        elif surrender_button.collidepoint(cursor):
                            self._play_sound(self._board.handle_surrender())
                        
                if self._board.game_over:
                    game_view.draw_winner_info(self._board.winner)
                    turn_around_button = game_view.draw_rotate_button()
                
                game_view.draw_buttons()
                self._board.draw_board(game_view)
                game_view.draw_info(self._board.info)
                    
            clock.tick(self._fps)

    def _customize_menu(self) -> None:
        """Runs the theme customization menu loop, allowing the user to select a theme by clicking on theme buttons."""
        Thread(target=self._play_sound, args=(self._custom_menu_sound,)).start()
        img_dir: Path = ScreenBase.IMG_DIR
        customize_menu_view = CustomizeScreen(self._screen)
        return_button, theme_buttons = customize_menu_view.screen_initialization()
        
        customize_menu_view.draw_buttons()
        self._board.draw_board(customize_menu_view)
        
        clock = pygame.time.Clock()
        while True:
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    Thread(target=self._board.save_board).start()
                    return
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if return_button.collidepoint(event.pos):
                        customize_menu_view[0] = True
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    cursor: tuple[int, int] = event.pos
                    
                    if customize_menu_view[0]:
                        customize_menu_view[0] = False
                        
                        if return_button.collidepoint(cursor):
                            Thread(target=self._board.save_board).start()
                            Thread(target=self._play_sound, args=(self._menu_return_sound,)).start()
                            return
                    
                    for rect, theme_name in theme_buttons:
                        if rect.collidepoint(cursor):
                            Thread(target=self._play_sound, args=(self._change_theme_sound,)).start()
                            self._board.image_dir = img_dir / theme_name
                            
                            self._board.draw_board(customize_menu_view)
                    
                customize_menu_view.draw_buttons()
                            
            clock.tick(self._fps)
    
    def _load_game_icon(self) -> pygame.surface.Surface:
        """ 
        Loads the game icon image from the project assets directory.
        
        :raises FileNotFoundError: If the game icon image file is not found in the expected directory.
        :return: The loaded pygame surface for the game icon."""
        path: Path = Path(sys.path[0]) / "src" / "project_assets" / "img" / "Classic" / "white_knight.png"
        
        if not path.is_file():
            raise FileNotFoundError(f"Image file not found: {path}! Please check the image directory.")
        return pygame.image.load(path)
    
    def _handle_game_reload(self, menu_view: MainMenuScreen) -> None:
        """ 
        Displays a blocking panel asking the user if they want to load the previous game. Resets the board if the user clicks 'No'. Continues with loaded state otherwise.
        
        :param menu_view: The MainMenuScreen instance used to display the reload game panel.
        """
        if len(self._board) == 1 and not self._board.game_over:
            return
        
        no_rect: pygame.Rect = menu_view.draw_reload_game_panel()
        
        pygame.display.flip()
        clock = pygame.time.Clock()
        while True:
            for panel_event in pygame.event.get():
                if panel_event.type == pygame.QUIT:
                    self._running = False
                    return
                
                if panel_event.type == pygame.MOUSEBUTTONDOWN:
                    if no_rect.collidepoint(panel_event.pos):
                        self._board.reset()
                    return
            
            clock.tick(self._fps)
    
    def _handle_board_click(self, cursor: tuple[int, int]) -> None:
        """
        Translates screen pixel coordinates from a mouse click into board coordinates (0-7) and passes them to the ChessBoard's handle_click method.

        :param cursor: The (x, y) pixel coordinates of the mouse click from pygame.event.
        """
        if self._board.game_over:
            return

        mouse_x, mouse_y = cursor
        square_size: int = ScreenBase.SQUARE_SIZE
        
        square_x = mouse_x // square_size
        square_y = mouse_y // square_size

        if 0 <= square_x < 8 and 0 <= square_y < 8:
            sound = self._board.handle_click(square_x, square_y)
            if sound:
                Thread(target=self._play_sound, args=(sound,)).start()
            
    def _handle_move_action(self, action: str) -> None:
        """
        Handles clicks on the history navigation buttons by calling the corresponding method on the ChessBoard instance and playing the sound.

        :param action: A string identifier for the history action to perform.
        """
        sound: str | None = None

        if action == "first_move":
            sound = self._board.first_move()
        elif action == "previous_move":
            sound = self._board.previous_move()
        else:
            last_move = (action == "last_move")
            sound = self._board.next_move(last_move)

        Thread(target=self._play_sound, args=(sound,)).start()
    
    def _play_sound(self, sound_key: str | None = None) -> None:
        """
        Plays a sound effect based on the provided key. Looks for '.wav' files in the utils/audio/ directory.

        :param sound_key: A string key identifying the sound file (without extension) or None to play a default 'incorrect' sound. Defaults to None.
        :raises FileNotFoundError: if the sound file is not found in the audio directory.
        """ 
        if not sound_key:
            sound_key = "incorrect"
             
        elif sound_key == "checkmate":
            sound_path: Path = self._audio_dir / "check.wav"
            
            if not sound_path.is_file():
                raise FileNotFoundError(f"Required sound file not found: {sound_path}. Please check the audio directory.")
            
            pygame.mixer.Sound(sound_path).play()
            pygame.time.delay(100)
            sound_key = "game_end"
            
        sound_path: Path = self._audio_dir / (sound_key + ".wav")
        
        if not sound_path.is_file():
            raise FileNotFoundError(f"Required sound file not found: {sound_path}. Please check the audio directory.")
        
        pygame.mixer.Sound(sound_path).play()