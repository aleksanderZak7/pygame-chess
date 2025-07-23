import sys
import pickle
import pygame
from pathlib import Path
from threading import Lock

from src import views, pieces
from .game_controller import GameController


class ChessBoard:
    """
    Represents and manages a single chess game instance, including board state, game logic delegation and game history tracking.
    """
    __slots__ = ("_info", "_game_over", "_winner", "_image_dir", "_index", "_save_lock", "_main_player", "_game_controller", 
                 "_valid_moves", "_pieces", "_game_history")
    
    def __init__(self) -> None:
        """Initializes the ChessBoard instance, setting default values and attempting to load a previously saved game state."""
        self._save_lock = Lock()
        self._main_player: int = -1
        self._game_controller = GameController()
        
        self._valid_moves: list[tuple[int, int]] = []
        self._pieces: dict[tuple[int, int], pieces.Piece] = {}
        self._game_history: list[tuple[dict[tuple[int, int], pieces.Piece], tuple]] = []
        
        self._load_board()
    
    def __len__(self) -> int:
        """Returns the number of moves made in the game."""
        return len(self._game_history)
    
    def draw_board(self, view: views.ScreenBase) -> None:
        """
        Draws the current state of the chessboard using the GameScreen.

        :param view: The ScreenBase instance used for rendering the board on the screen.
        :raises FileNotFoundError: If the board image file cannot be found in the current image directory.
        """
        if self._game_over:
            self.change_view()
            
        img: str = "board.png" if self._game_controller.current_player else "reverse_board.png"
        img_path: Path = Path(self._image_dir) / img
        
        if not img_path.is_file():
            raise FileNotFoundError(f"Required image file not found: {img_path}. Please check the image directory.")
        
        board_img: pygame.surface.Surface = pygame.image.load(img_path)
        view.draw_board(board_img, self._pieces, self._valid_moves)
        
    def handle_click(self, x: int, y: int) -> str | None:
        """
        Handles a mouse click event on the board at board coordinates (x, y). Delegates logic to GameController to select a piece or execute a move.
        If a move is made, updates game state, checks for check/checkmate/stalemate, rotates the board for the next player, updates history, and returns a sound key.

        :param x: The x-coordinate (column) of the clicked square (0-7).
        :param y: The y-coordinate (row) of the clicked square (0-7).
        :return: A string key representing the sound effect for the action (e.g., 'move', 'capture', 'check', 'checkmate'), or None if the click did not result in a move.
        """
        sound: str | None = None
        position: tuple[int, int] | None = self._game_controller.handle_click(x, y, self._pieces, self._valid_moves)
        if position:
            sound = self._game_controller.handle_move(*position, self._pieces)
            
            self._rotate_board()
            if self._game_controller.is_check(self._pieces):
                if not self._game_controller.any_valid_moves(self._pieces):
                    sound = "checkmate"
                    self._game_over = True
                    self._info = "Checkmate!"
                    self._winner = "Black" if self._game_controller.current_player else "White"
                else:
                    sound = "check"
                    self._info = "Check!"
                    
            elif self._is_stalemate():
                sound = "game_end"
                self._game_over = True
                self._info = "Stalemate!"
            
            else:
                self._info = "White's turn" if self._game_controller.current_player else "Black's turn"
            
            self._add_move()     
            if self._game_over:
                self._rotate_board()
                self._main_player = self._game_controller.current_player
        
        return sound
    
    def handle_surrender(self) -> str | None:
        """
        Handles the current player surrendering the game. Sets game over state, determines the winner, updates info, and returns a sound key.

        :return: The sound key "game_end", or None if the game was already over.
        """
        if self._game_over:
            return None
        self._game_over = True 
        self._valid_moves.clear()
        self._info = "Surrendered!"
        self._winner = "Black" if self._game_controller.current_player else "White"
        
        if not self._game_controller.check:
            self._game_controller.check_current_king(self._pieces, True)
            self._index -= 1
            self._game_history.pop()
            self._add_move()
        
        self._main_player = self._game_controller.current_player
        self._game_history = self._game_history[:self._index + 1]
        
        return "game_end"
    
    def change_view(self, change_player: bool = False) -> None:
        """
        Changes the board's visual orientation perspective, optionally toggling which player's view is shown (useful after game over).

        :param change_player: If True, toggles the perspective between white and black. Defaults to False.
        """
        if change_player:
            self._main_player = abs(self._main_player - 1)
        
        if self._game_controller.current_player != self._main_player:
            self._rotate_board()
    
    def first_move(self) -> str | None:
        """
        Navigates the game history to the initial board state.

        :return: The sound key "move", or None if already at the first move.
        """
        if self._index == 0:
            return None
        
        self._index = 0
        self._valid_moves.clear()
        self._load_move(self._index)
        
        if not self._game_over:
            self._info = "White's turn"
        return "move"
    
    def previous_move(self) -> str | None:
        """
        Navigates the game history one step backward.

        :return: The sound key ("move" or "check"), or None if already at the first move.
        """
        if self._index == 0:
            return None
        
        sound: str = ""
        self._index -= 1
        info: str | None = None
        self._valid_moves.clear()
        self._load_move(self._index)
        
        if self._game_controller.check:
            sound = "check"
            if not self._game_over:
                info = "Check!"
        else:
            sound = "move"
        
        if not self._game_over:
            info = "White's turn" if self._game_controller.current_player else "Black's turn"
        
        if info:
            self._info = info
        return sound
    
    def next_move(self, last_move: bool = False) -> str | None:
        """
        Navigates the game history one step forward, or jumps to the latest move.

        :param last_move: If True, jumps directly to the end of the history. Defaults to False.
        :return: The appropriate sound key, or None if already at the last move.
        """
        self._valid_moves.clear()
        if self._index == len(self._game_history) - 1:
            return None
        
        sound: str = ""
        self._index = (len(self._game_history) - 1) if last_move else self._index + 1
        
        self._load_move(self._index)
        if self._game_controller.check:
            self._info = "Check!" if not self._game_over else self._info
            sound = "checkmate" if self._index == len(self._game_history) - 1 and self._game_over else "check"
        
        elif self._info in ("Surrendered!", "Stalemate!") and self._index == len(self._game_history) - 1:
            sound = "game_end"
            if self._info == "Surrendered!":
                self._game_controller.check_current_king(self._pieces, True)
        
        else:
            sound = "capture" if len(self._game_history[self._index][0]) < len(self._game_history[self._index - 1][0]) else "move"
            
        if not self._game_over and self._info != "Check!":
            self._info = "White's turn" if self._game_controller.current_player else "Black's turn"
        
        return sound
    
    def reset(self) -> None:
        """Resets the game to the standard initial state."""
        self._index: int = -1
        self._game_over: bool = False
        self._winner: str | None = None
        self._info: str = "White's turn"
        
        self._pieces.clear()
        self._valid_moves.clear()
        self._game_history.clear()
        self._game_controller.reset()
        
        main_figures = [pieces.Rook, pieces.Knight, pieces.Bishop, pieces.Queen, pieces.King, pieces.Bishop, pieces.Knight, pieces.Rook]
        for i, Figure in enumerate(main_figures):
            self._pieces[(i, 0)] = Figure(0, self._image_dir, i, 0)
            self._pieces[(i, 7)] = Figure(1, self._image_dir, i, 7)

        for i in range(8):
            self._pieces[(i, 1)] = pieces.Pawn(0, self._image_dir, i, 1)
            self._pieces[(i, 6)] = pieces.Pawn(1, self._image_dir, i, 6)
        
        self._add_move()
    
    def save_board(self) -> None:
        """Saves the current game state to a pickle file."""
        self._valid_moves.clear()

        board_data = {
            "info" : self._info,
            "winner" : self._winner,
            "game_over" : self._game_over,
            "image_path" : self._image_dir,
            "main_player" : self._main_player,
            "game_history" : self._game_history,
                      }
        
        path: Path = Path(sys.path[0]) / "src" / "project_assets" / "board_data.pkl"
        
        with self._save_lock:
            with path.open("wb") as file:
                pickle.dump(board_data, file)
        
    def _load_board(self) -> None:
        """
        Attempts to load a saved game state from 'src/project_assets/board_data.pkl'. 
        If loading fails (file not found, invalid format), it resets the board to the initial state using the 'Classic' theme.

        :raises FileNotFoundError: If the default 'Classic' theme directory cannot be found during a reset triggered by load failure.
        """
        try:
            path: Path = Path(sys.path[0]) / "src" / "project_assets" / "board_data.pkl"
            with path.open("rb") as file:
                board_data = pickle.load(file)
                self._info: str = board_data["info"]
                self._winner: str | None = board_data["winner"]
                self._game_over: bool = board_data["game_over"]
                self._image_dir: Path = board_data["image_path"]
                self._main_player: int = board_data["main_player"]
                
                self._game_history = board_data["game_history"]
                self._index: int = len(self._game_history) - 1
                self._load_move()
                    
        except (FileNotFoundError, KeyError):
            self._image_dir = Path(sys.path[0]) / "src" / "project_assets" / "img" / "Classic"
            try:
                self.reset()
            except FileNotFoundError:
                raise FileNotFoundError(f"Image files not found in {self._image_dir}! Please check the img directory.")
    
    def _load_move(self, index: int = -1) -> None:
        """
        Loads the current board state and GameController state from the game history.
        
        :param index: The index of the move to load from the history. Defaults to -1 (last move).
        """
        self._pieces = self._copy_board(self._game_history[index][0])
        self._game_controller.restore_state(self._game_history[index][1])
    
    def _copy_board(self, piecies: dict[tuple[int, int], pieces.Piece] | None = None) -> dict[tuple[int, int], pieces.Piece]:
        """
        Creates a deep copy of a given board state dictionary.

        :param pieces_to_copy: The board state dictionary to copy. If None, copies the current `self._pieces`.
        :return: A new dictionary representing a deep copy of the board state.
        """
        if not piecies:
            piecies = self._pieces

        copied_state: dict[tuple[int, int], pieces.Piece] = {}
        for position, piece in piecies.items():
            copied_state[position] = piece.copy()     

        return copied_state
    
    def _add_move(self) -> None:
        """Adds the current board and GameController state to the history unless it is identical to the existing entry at the current index."""
        self._index += 1
        
        if self._index != len(self._game_history):
            if self._pieces == self._game_history[self._index][0]:
                return
            self._game_history = self._game_history[:self._index]

        self._game_history.append((self._copy_board(), self._game_controller.copy()))
    
    def _rotate_board(self) -> None:
        """Rotates the internal board representation by 180 degrees."""
        self._game_controller.switch_player()
        new_pieces: dict[tuple[int, int], pieces.Piece] = {}
        
        for (x, y), piece in self._pieces.items():
            new_x, new_y = 7 - x, 7 - y
            piece.position = (new_x, new_y)
            new_pieces[(new_x, new_y)] = piece
            
        self._pieces = new_pieces
    
    def _is_stalemate(self) -> bool:
        """
        Checks for stalemate conditions for the current player.

        Includes checks for:
        - Threefold repetition (same position occurs 3 times with the same player to move - simplified check here).
        - Insufficient mating material (e.g., King vs King, King vs King+Bishop/Knight).
        - No legal moves available while not being in check (delegated to GameController).

        :return: True if any stalemate condition is met, False otherwise.
        """
        if len(self._game_history) >= 6:
            if self._game_history[-1][0] == self._game_history[-5][0] and self._game_history[-2][0] == self._game_history[-6][0]:
                return True
            
        amount_of_pieces: int = len(self._pieces)
        if amount_of_pieces <= 4:
            if amount_of_pieces == 2:
                return True
            
            elif amount_of_pieces == 3:
                for piece in self._pieces.values():
                    if isinstance(piece, (pieces.Bishop, pieces.Knight)):
                        return True
            
            elif amount_of_pieces == 4:
                minor_pieces = [(piece.position, piece.color) for piece in self._pieces.values() 
                                if isinstance(piece, (pieces.Bishop, pieces.Knight))]
                if len(minor_pieces) == 2:
                    _, color1 = minor_pieces[0]
                    _, color2 = minor_pieces[1]

                    if color1 != color2:
                        return True
            
        return not self._game_controller.any_valid_moves(self._pieces)
        
    @property
    def info(self) -> str:
        """Returns the current informational message for the game status display."""
        return self._info
        
    @property
    def game_over(self) -> bool:
        """Returns True if the game is over, False otherwise."""
        return self._game_over
    
    @property
    def winner(self) -> str | None:
        """Returns the winner of the game (None if game is still ongoing or draw)."""
        return self._winner
    
    @property
    def image_dir(self) -> Path | None:
        """Returns the current directory path for loading piece/board images."""
        return self._image_dir
    
    @image_dir.setter
    def image_dir(self, value: Path) -> None:
        """
        Sets the directory for loading piece and board images (theme).

        :param value: The new directory path for images.
        :raises FileNotFoundError: If the provided directory path does not exist.
        """
        if self._image_dir == value:
            return
        
        if not value.is_dir():
            raise FileNotFoundError(f"Image directory '{value}' not found or is not a directory.")
        
        self._image_dir = value
        pieces.Piece.image_cache.clear()
        
        for board_state, _ in self._game_history:
            for piece in board_state.values():
                piece.image_dir = self._image_dir

        self._load_move(self._index)