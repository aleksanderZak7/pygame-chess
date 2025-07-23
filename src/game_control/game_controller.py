import sys
import pygame

from src import pieces, GameScreen


class GameController:
    """
    Manages the core game logic and state of a chess match.
    """
    __slots__ = ("_check", "_current_player", "_white_king", "_black_king", "_last_piece", "_last_moved_piece")
    
    def __init__(self) -> None:
        """Initializes the game controller with default starting values for a new game."""
        self._check: bool = False
        self._current_player: int = 1
        
        self._white_king: tuple[int, int] = (4, 7)
        self._black_king: tuple[int, int] = (3, 7)
         
        self._last_moved_piece: pieces.Piece | None = None
    
    def switch_player(self) -> None:
        """Switches the current player between white (1) and black (0)."""
        self._current_player = abs(self._current_player - 1)
    
    def reset(self) -> None:
        """Resets the game controller state to the initial default values for a new game."""
        self._check = False
        self._current_player = 1
        self._white_king = (4, 7)
        self._black_king = (3, 7)
        self._last_moved_piece = None
        
    def copy(self) -> tuple:
        """
        Creates a shallow copy of the controller's current state attributes.
        
        :return: A tuple containing the values of the attributes defined in __slots__ in the order they are defined, excluding '_last_piece'.
        """
        attribute_tuple = tuple(getattr(self, attr) for attr in self.__slots__ if attr != "_last_piece")
        return attribute_tuple
    
    def restore_state(self, state_tuple: tuple) -> None:
        """
        Restores the controller's state from a previously saved tuple.

        :param state_tuple: A tuple containing the state values in the same order as __slots__, excluding '_last_piece'.
        :raises ValueError: If the provided tuple has an incorrect number of elements.
        """
        slots_lenght: int = len(self.__slots__) - 1
        if len(state_tuple) != slots_lenght:
            raise ValueError(f"Expected state tuple of length {slots_lenght}, got {len(state_tuple)}")
            
        for attr_name, value in zip(self.__slots__, state_tuple):
            if attr_name == "_last_piece":
                continue
            setattr(self, attr_name, value)
    
    def handle_click(self, x: int, y: int, piece_board: dict[tuple[int, int], pieces.Piece], 
                     valid_moves: list[tuple[int, int]]) -> tuple[int, int] | None:
        """
        Handles a mouse click event on the board. If a piece was previously selected, checks if the click is on a valid move square. If no piece was selected,
        or the click is not on a valid move, selects the piece at (x, y) if it belongs to the current player and calculates its valid moves, considering checks.

        :param x: The x-coordinate (column) of the clicked square (0-7).
        :param y: The y-coordinate (row) of the clicked square (0-7).
        :param piece_board: The current state of the chessboard dictionary.
        :param valid_moves: A list (mutated by this method) storing currently displayed valid moves. It's cleared and repopulated based on the click.
        :return: The coordinates (x, y) of the target square if a valid move is selected, otherwise None.
        """
        if valid_moves:
            if (x, y) in valid_moves:
                valid_moves.clear()
                return (x, y)
            
        valid_moves.clear() 
        moves: list[tuple[int, int]] = []  
        piece: pieces.Piece | None = piece_board.get((x, y))
        
        if piece and piece.color == self._current_player:
            self._last_piece: pieces.Piece = piece
            moves = self._last_piece.valid_moves(piece_board)
            
            if isinstance(self._last_piece, pieces.Pawn) and isinstance(self._last_moved_piece, pieces.Pawn):
                self._last_piece.en_passant(moves, self._last_moved_piece.position)
            
        if moves:
            king_position: tuple[int, int] = self._white_king if self._current_player else self._black_king
            for move in moves:
                virtual_board: dict[tuple[int, int], pieces.Piece] = self._create_virtual_board(piece_board, move, self._last_piece)     
                if not self._is_king_in_check(virtual_board):
                    valid_moves.append(move)
            if isinstance(self._last_piece, pieces.King):
                if self._last_piece.first_move and not self._last_piece.checked:
                    self._castle_over_check(piece_board, valid_moves, moves)
                    
                self._set_king_position(*king_position)
                    
        return None
    
    def handle_move(self, x: int, y: int, piece_board: dict[tuple[int, int], pieces.Piece]) -> str | None:
        """
        Executes the selected move, updating the board state and controller state.

        :param x: The target x-coordinate (column) of the move.
        :param y: The target y-coordinate (row) of the move.
        :param piece_board: The current state of the chessboard dictionary (mutated by this method).
        :return: The sound key effect associated with the last move ('move', 'capture', 'castle', 'promotion') or None if no sound is associated.
        """
        sound = None
        if isinstance(self._last_piece, pieces.SpecialPiece) and not isinstance(self._last_piece, pieces.Rook): 
            sound = self._handle_special_move(x, y, piece_board)
            
        if not sound:
            sound = "capture" if piece_board.get((x, y)) else "move"
        
        del piece_board[self._last_piece.position]
        self._last_piece.move(x, y)
        piece_board[(x, y)] = self._last_piece
        self._last_moved_piece = self._last_piece
        
        if self._check:
            self.check_current_king(piece_board)
        
        return sound
    
    def is_check(self, piece_board: dict[tuple[int, int], pieces.Piece]) -> bool:
        """
        Checks if the current player's king is currently in check. If it is, updates the King's visual state and the internal check flag.

        :param piece_board: The current state of the chessboard dictionary.
        :return: True if the current player is in check, False otherwise.
        """
        if(self._is_king_in_check(piece_board)):
            self.check_current_king(piece_board, check=True)
            return True
        return False
    
    def any_valid_moves(self, piece_board: dict[tuple[int, int], pieces.Piece]) -> bool:
        """
        Checks if the current player has any valid moves available.

        :param piece_board: The current state of the chessboard dictionary.
        :return: True if the current player has at least one valid move, False otherwise.
        """
        king_position: tuple[int, int] = self._white_king if self._current_player else self._black_king
        for piece in piece_board.values():
            if piece.color == self._current_player:
                moves: list[tuple[int, int]] = piece.valid_moves(piece_board)
                for move in moves:
                    virtual_board: dict[tuple[int, int], pieces.Piece] = self._create_virtual_board(piece_board, move, piece)     
                    if not self._is_king_in_check(virtual_board):
                        self._set_king_position(*king_position)
                        return True
                if isinstance(piece, pieces.King):
                    self._set_king_position(*king_position)
                    
        return False
    
    def check_current_king(self, piece_board: dict[tuple[int, int], pieces.Piece], check: bool = False) -> None:
        """
        Updates the internal check flag and the visual state of the current player's King object.

        :param piece_board: The current state of the chessboard dictionary.
        :param check: The boolean status indicating whether the king is now in check. Defaults to False.
        """
        king_position: tuple[int, int] = self._white_king if self._current_player else self._black_king
        king: pieces.Piece | None = piece_board.get(king_position)
        
        assert isinstance(king, pieces.King), f"Internal Error: No King found at tracked position {king_position} for player {self._current_player}!"
                
        self._check = check
        if king.checked != check:
            king.check()
    
    def _create_virtual_board(self, piece_board: dict[tuple[int, int], pieces.Piece], move: tuple[int, int], 
                              piece: pieces.Piece) -> dict[tuple[int, int], pieces.Piece]:
        """
        Creates a temporary, virtual board state reflecting a potential move.

        :param piece_board: The original board state dictionary.
        :param move: The target coordinates (x, y) of the hypothetical move.
        :param piece: The piece object being hypothetically moved.
        :return: A new dictionary representing the board state after the hypothetical move.
        """
        if isinstance(piece, pieces.King):
            if self._current_player:
                self._white_king = move
            else:
                self._black_king = move
        
        virtual_board: dict[tuple[int, int], pieces.Piece] = piece_board.copy()
        virtual_board[move] = piece
        del virtual_board[piece.position]
        
        return virtual_board
    
    def _is_king_in_check(self, piece_board: dict[tuple[int, int], pieces.Piece]) -> bool:
        """
        Checks if the current player's king is attacked on the given board state.

        :param piece_board: The board state dictionary to check (can be real or virtual).
        :return: True if the king is under attack, False otherwise.
        """
        king_position: tuple[int, int] = self._white_king if self._current_player else self._black_king
        
        attacked_positions: list[tuple[int, int]] = []
        for piece in piece_board.values():
            if piece.color != self._current_player:
                attacked_positions = piece.valid_moves(piece_board, defend_moves=True)
                if attacked_positions and king_position in attacked_positions:
                    return True
        
        return False
    
    def _castle_over_check(self, piece_board: dict[tuple[int, int], pieces.Piece], 
                           valid_moves: list[tuple[int, int]], moves: list[tuple[int, int]]) -> None:
        """
        Filters potential castling moves from 'valid_moves' if the king passes through a square attacked by an opponent piece.

        :param piece_board: The current real board state.
        :param valid_moves: The list of currently valid moves (potentially including castling) - will be modified.
        :param moves: The initial list of potential moves generated by the King (including special moves).
        """
        assert isinstance(self._last_piece, pieces.SpecialPiece), f"Internal Error: Last moved piece - "
        f"{self._last_piece.__class__.__name__} at {self._last_piece.position} is not a special piece!"
        
        for move in moves:
            if move in valid_moves and move in self._last_piece.special_moves:
                dx = move[0] - self._last_piece.position[0]
                for x in range(1, abs(dx)):
                    if dx < 0:
                        x = -x
                        
                    virtual_board: dict[tuple[int, int], pieces.Piece] = \
                    self._create_virtual_board(piece_board, (self._last_piece.position[0] + x, 7), self._last_piece)
                    if self._is_king_in_check(virtual_board):
                        valid_moves.remove(move)
    
    def _set_king_position(self, x: int, y: int) -> None:
        """
        Updates the internally tracked position of the current player's king.

        :param x: The new x-coordinate of the king.
        :param y: The new y-coordinate of the king.
        """
        if self._current_player:
            self._white_king = (x, y)
        else:
            self._black_king = (x, y)
    
    def _handle_special_move(self, x: int, y: int, piece_board: dict[tuple[int, int], pieces.Piece]) -> str | None:
        """ 
        Checks and performs special moves for the most recently moved piece, including:
        - pawn promotion
        - en passant
        - castling
        
        :param x: The target x-coordinate (column) of the move.
        :param y: The target y-coordinate (row) of the move.
        :param piece_board: The current state of the chessboard dictionary (mutated by this method).
        :return: The sound key effect associated with the last move ('promotion', 'capture', 'castle') or None if no sound is associated.
        """
        sound: str | None = None
        if isinstance(self._last_piece, pieces.Pawn):
                if y == 0:
                    self._handle_promotion()
                    sound = "promotion"
                elif (x, y) in self._last_piece.special_moves:
                    del piece_board[x, y + 1]
                    sound = "capture"
            
        elif isinstance(self._last_piece, pieces.King):
            self._set_king_position(x, y)
            if (x, y) in self._last_piece.special_moves:
                sound = "castle"
                rook: pieces.Piece | None = piece_board.get(self._last_piece.castling_rook[x, y][0])
                assert isinstance(rook, pieces.Rook), f"Internal Error: No Rook found at tracked position {self._last_piece.castling_rook[x, y][0]} for player {self._current_player}!"
                
                del piece_board[self._last_piece.castling_rook[x, y][0]]
                rook.move(*self._last_piece.castling_rook[x, y][1])
                piece_board[self._last_piece.castling_rook[x, y][1]] = rook
        
        return sound
    
    def _handle_promotion(self) -> None:
        """
        Handles the pawn promotion process. Displays a panel with promotion choices (Knight, Queen, Rook, Bishop) and waits for the user to click on one.
        
        Note: This method contains a blocking loop and depends on `views.GameScreen`.
        """
        options: list[pygame.surface.Surface] = []
        piece_classes = [pieces.Knight, pieces.Queen, pieces.Rook, pieces.Bishop]
        
        for cls in piece_classes:
            temp_piece: pieces.Piece = cls(self._last_piece.color, self._last_piece.image_dir, 0, 0)
            image: pygame.surface.Surface | None = temp_piece.image
            assert image is not None, f"Internal Error: No image found for {cls.__name__}!"
            options.append(image)
        
        panel_width, panel_height, panel_x, panel_y = GameScreen.draw_promotion_panel(options)
        square_size = panel_width // 4
        
        clock = pygame.time.Clock()
        while True:
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if panel_x <= mouse_x <= panel_x + panel_width and panel_y <= mouse_y <= panel_y + panel_height:
                        idx: int = (mouse_x - panel_x) // square_size
                        if 0 <= idx < 4:
                            cls = piece_classes[idx]
                            self._last_piece = cls(self._last_piece.color, self._last_piece.image_dir, *self._last_piece.position)
                            return
                    else:
                        self._last_piece = pieces.Queen(self._last_piece.color, self._last_piece.image_dir, *self._last_piece.position)
                        return
                    
            clock.tick(20)
        
    @property
    def check(self) -> bool:
        """Returns the current check status (True if current player is in check)."""
        return self._check
         
    @property
    def current_player(self) -> int:
        """Returns the current player (1 for white, 0 for black)."""
        return self._current_player