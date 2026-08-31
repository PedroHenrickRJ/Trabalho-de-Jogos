import random
from abc import ABC, abstractmethod

import pygame


class obj(ABC):

    def __init__(self, x, y, sprites=None):
        self.x = x
        self.y = y
        self.sprites = sprites if sprites else []

    def draw(self, screen):
        for sprite in self.sprites:
            screen.blit(
                sprite,
                (self.x, self.y)
            )

    @abstractmethod
    def update(self, dt):
        pass


class Cell(obj):
    #Uma célula da grade

    def __init__(self, x, y, row, col, size):
        super().__init__(x, y)

        self.row = row
        self.col = col
        self.size = size

    def draw(self, screen):
        rect = pygame.Rect(
            int(self.x),
            int(self.y),
            self.size,
            self.size
        )

        pygame.draw.rect(
            screen,
            (43, 43, 54),
            rect
        )

        pygame.draw.rect(
            screen,
            (82, 82, 96),
            rect,
            2
        )

    def update(self, dt):
        pass


class Piece(obj):
    # Peça única visual e lógica do Match 3

    MANA = 0
    MOON = 1
    CANDLE = 2
    STAR = 3

    def __init__(
        self,
        x,
        y,
        row,
        col,
        kind,
        size,
        images,
        explosion_images
    ):
        super().__init__(x, y)

        self.row = row
        self.col = col
        self.kind = kind
        self.size = size

        # Imagens normais das peças
        self.images = images

        # Imagens da animação de explosão
        self.explosion_images = explosion_images

        self.explosion_frame = 0
        self.explosion_timer = 0.0

        # Movimento
        self.target_x = x
        self.target_y = y

        self.moving = False

        # Estados:
        # idle
        # exploding
        # finished
        self.state = "idle"


    # EXPLOSÃO

    def start_explosion(self):
        self.state = "exploding"
        self.explosion_frame = 0
        self.explosion_timer = 0.0


    # MOVIMENTO

    def set_target(self, x, y):
        self.target_x = x
        self.target_y = y
        self.moving = True


    # atualizar

    def update(self, dt):

        if self.state == "exploding":

            self.explosion_timer += dt

            # Cada frame da explosão dura 0.05 segundos
            if self.explosion_timer >= 0.05:

                self.explosion_timer -= 0.05

                self.explosion_frame += 1

                # terminou a animação
                if (
                    self.explosion_frame
                    >= len(self.explosion_images)
                ):
                    self.state = "finished"

            return

        if not self.moving:
            return

        dx = self.target_x - self.x
        dy = self.target_y - self.y

        speed = 15.0

        factor = min(
            1.0,
            dt * speed
        )

        self.x += dx * factor
        self.y += dy * factor

        if (
            abs(dx) < 0.5
            and abs(dy) < 0.5
        ):
            self.x = self.target_x
            self.y = self.target_y
            self.moving = False

    # desenhar

    def draw(self, screen):

        # DESENHANDO EXPLOSÃO

        if self.state == "exploding":

            image = self.explosion_images[
                self.explosion_frame
            ]

        elif self.state == "finished":

            return


        # PEÇA NORMAL

        else:

            image = self.images[
                self.kind
            ]

        # Ajusta o tamanho da imagem
        image = pygame.transform.scale(
            image,
            (
                self.size - 10,
                self.size - 10
            )
        )

        # Desenha centralizado dentro da célula
        screen.blit(
            image,
            (
                int(self.x + 5),
                int(self.y + 5)
            )
        )


class Grid(obj):
    # Grid principal do Match 3

    def __init__(
        self,
        x,
        y,
        grid_size=(8, 8),
        cell_size=60,
        images=None,
        explosion_images=None
    ):
        super().__init__(x, y)

        self.rows, self.cols = grid_size

        self.cell_size = cell_size

        self.images = images

        self.explosion_images = explosion_images


        # CÉLULAS

        self.cells = []

        for row in range(self.rows):

            current_row = []

            for col in range(self.cols):

                cell_x = x + col * cell_size
                cell_y = y + row * cell_size

                cell = Cell(
                    cell_x,
                    cell_y,
                    row,
                    col,
                    cell_size
                )

                current_row.append(
                    cell
                )

            self.cells.append(
                current_row
            )


        # TABULEIRO LÓGICO

        self.board = [
            [
                None
                for _ in range(self.cols)
            ]
            for _ in range(self.rows)
        ]


        # CONTROLES

        self.selected = None

        self.cursor_row = 0
        self.cursor_col = 0

        self.hover_cell = None

        # ESTADOS

        self.phase = "idle"
        self.phase_timer = 0.0
        self.pending_matches = set()

        self.score = 0

        self.reset_board()


    # COORDENADAS

    def cell_to_world(self, row, col):

        return (
            self.x + col * self.cell_size,
            self.y + row * self.cell_size
        )

    def world_to_cell(self, pos):

        mouse_x, mouse_y = pos

        col = int(
            (mouse_x - self.x)
            // self.cell_size
        )

        row = int(
            (mouse_y - self.y)
            // self.cell_size
        )

        if (
            0 <= row < self.rows
            and 0 <= col < self.cols
        ):
            return (
                row,
                col
            )

        return None


    # ADJACÊNCIA
    def adjacent(self, a, b):

        if a is None or b is None:
            return False

        return (
            abs(a[0] - b[0])
            + abs(a[1] - b[1])
            == 1
        )


    # GERAÇÃO DO TABULEIRO
    def would_create_match(
        self,
        row,
        col,
        kind
    ):

        if col >= 2:

            left_1 = self.board[
                row
            ][
                col - 1
            ]

            left_2 = self.board[
                row
            ][
                col - 2
            ]

            if (
                left_1 is not None
                and left_2 is not None
                and left_1.kind == kind
                and left_2.kind == kind
            ):
                return True


        if row >= 2:

            up_1 = self.board[
                row - 1
            ][
                col
            ]

            up_2 = self.board[
                row - 2
            ][
                col
            ]

            if (
                up_1 is not None
                and up_2 is not None
                and up_1.kind == kind
                and up_2.kind == kind
            ):
                return True

        return False

    def generate_kind(
        self,
        row,
        col
    ):

        kinds = [
            Piece.MANA,
            Piece.MOON,
            Piece.CANDLE,
            Piece.STAR
        ]

        random.shuffle(
            kinds
        )

        for kind in kinds:

            if not self.would_create_match(
                row,
                col,
                kind
            ):
                return kind

        return kinds[0]


    # RESET

    def reset_board(self):

        self.selected = None

        self.pending_matches.clear()

        self.phase = "idle"

        self.phase_timer = 0.0

        self.board = [
            [
                None
                for _ in range(self.cols)
            ]
            for _ in range(self.rows)
        ]

        # Cria cada peça
        # evitando matches iniciais

        for row in range(self.rows):

            for col in range(self.cols):

                x, y = self.cell_to_world(
                    row,
                    col
                )

                kind = self.generate_kind(
                    row,
                    col
                )

                self.board[row][col] = Piece(
                    x,
                    y,
                    row,
                    col,
                    kind,
                    self.cell_size,
                    self.images,
                    self.explosion_images
                )


    # ENCONTRA MATCHES

    def find_matches(self):

        matches = set()

        for row in range(self.rows):

            col = 0

            while col < self.cols:

                piece = self.board[
                    row
                ][
                    col
                ]

                if piece is None:
                    col += 1
                    continue

                kind = piece.kind

                start = col

                while (
                    col < self.cols
                    and self.board[row][col]
                    is not None
                    and self.board[row][col].kind
                    == kind
                ):
                    col += 1

                length = col - start

                if length >= 3:

                    for c in range(
                        start,
                        col
                    ):

                        matches.add(
                            (
                                row,
                                c
                            )
                        )

        for col in range(self.cols):

            row = 0

            while row < self.rows:

                piece = self.board[
                    row
                ][
                    col
                ]

                if piece is None:
                    row += 1
                    continue

                kind = piece.kind

                start = row

                while (
                    row < self.rows
                    and self.board[row][col]
                    is not None
                    and self.board[row][col].kind
                    == kind
                ):
                    row += 1

                length = row - start

                if length >= 3:

                    for r in range(
                        start,
                        row
                    ):

                        matches.add(
                            (
                                r,
                                col
                            )
                        )

        return matches


    # TROCA

    def swap_pieces(
        self,
        first,
        second
    ):

        if not self.adjacent(
            first,
            second
        ):
            return

        row_a, col_a = first
        row_b, col_b = second

        piece_a = self.board[
            row_a
        ][
            col_a
        ]

        piece_b = self.board[
            row_b
        ][
            col_b
        ]

        # Troca lógica
        self.board[
            row_a
        ][
            col_a
        ] = piece_b

        self.board[
            row_b
        ][
            col_b
        ] = piece_a

        # Atualiza posição lógica
        piece_a.row = row_b
        piece_a.col = col_b

        piece_b.row = row_a
        piece_b.col = col_a

        # Posições visuais
        ax, ay = self.cell_to_world(
            row_a,
            col_a
        )

        bx, by = self.cell_to_world(
            row_b,
            col_b
        )

        piece_a.set_target(
            bx,
            by
        )

        piece_b.set_target(
            ax,
            ay
        )

    def make_move(
        self,
        first,
        second
    ):

        if not self.adjacent(
            first,
            second
        ):
            return

        self.swap_pieces(
            first,
            second
        )

        self.phase = "swapping"

        self.phase_timer = 0.0

        self.selected = None


    # SELEÇÃO

    def select_cell(
        self,
        cell
    ):

        if cell is None:
            return

        if self.phase != "idle":
            return

        # Primeira seleção
        if self.selected is None:

            self.selected = cell

            return

        # Clicou novamente na mesma
        if self.selected == cell:

            self.selected = None

            return

        # Células adjacentes
        if self.adjacent(
            self.selected,
            cell
        ):

            self.make_move(
                self.selected,
                cell
            )

        else:

            # Seleciona a nova célula
            self.selected = cell


    # MOUSE

    def handle_mouse_click(
        self,
        pos
    ):

        if self.phase != "idle":
            return

        cell = self.world_to_cell(
            pos
        )

        if cell is not None:

            self.select_cell(
                cell
            )


    # CURSOR

    def move_cursor(
        self,
        row_change,
        col_change
    ):

        self.cursor_row = max(
            0,
            min(
                self.rows - 1,
                self.cursor_row
                + row_change
            )
        )

        self.cursor_col = max(
            0,
            min(
                self.cols - 1,
                self.cursor_col
                + col_change
            )
        )


    # TECLADO

    def handle_key(
        self,
        key
    ):

        if key in (
            pygame.K_UP,
            pygame.K_w
        ):

            self.move_cursor(
                -1,
                0
            )

        elif key in (
            pygame.K_DOWN,
            pygame.K_s
        ):

            self.move_cursor(
                1,
                0
            )

        elif key in (
            pygame.K_LEFT,
            pygame.K_a
        ):

            self.move_cursor(
                0,
                -1
            )

        elif key in (
            pygame.K_RIGHT,
            pygame.K_d
        ):

            self.move_cursor(
                0,
                1
            )

        elif key in (
            pygame.K_SPACE,
            pygame.K_RETURN
        ):

            if self.phase == "idle":

                self.select_cell(
                    (
                        self.cursor_row,
                        self.cursor_col
                    )
                )

        elif key == pygame.K_r:

            self.reset_board()


    # INICIA MATCH
    def start_match(
        self,
        matches
    ):

        if not matches:
            return

        self.pending_matches = matches

        # Cada peça vale 10 pontos
        self.score += (
            len(matches) * 10
        )

        # Inicia explosão de cada peça
        for row, col in matches:

            piece = self.board[
                row
            ][
                col
            ]

            if piece is not None:

                piece.start_explosion()

        # ESPERANDO a explosão terminar
        self.phase = "removing"

        self.phase_timer = 0.0


    # REMOVE MATCHES E FAZ AS PEÇAS CAÍREM
    def remove_matches(self):

        for row, col in self.pending_matches:

            self.board[
                row
            ][
                col
            ] = None

        self.pending_matches.clear()

        for col in range(self.cols):

            target_row = self.rows - 1

            # Percorre de baixo para cima
            for row in range(
                self.rows - 1,
                -1,
                -1
            ):

                piece = self.board[
                    row
                ][
                    col
                ]

                if piece is not None:

                    if row != target_row:

                        self.board[
                            target_row
                        ][
                            col
                        ] = piece

                        self.board[
                            row
                        ][
                            col
                        ] = None

                        piece.row = target_row
                        piece.col = col

                        x, y = self.cell_to_world(
                            target_row,
                            col
                        )

                        piece.set_target(
                            x,
                            y
                        )

                    target_row -= 1


            # NOVAS PEÇAS

            for row in range(
                target_row,
                -1,
                -1
            ):

                x, y = self.cell_to_world(
                    row,
                    col
                )

                # Começa acima do grid
                spawn_y = (
                    self.y
                    - (
                        target_row
                        - row
                        + 1
                    )
                    * self.cell_size
                )

                kind = random.randint(
                    0,
                    3
                )

                piece = Piece(
                    x,
                    spawn_y,
                    row,
                    col,
                    kind,
                    self.cell_size,
                    self.images,
                    self.explosion_images
                )

                piece.set_target(
                    x,
                    y
                )

                self.board[
                    row
                ][
                    col
                ] = piece

        self.phase = "falling"

        self.phase_timer = 0.0

    # atualizar

    def update(
        self,
        dt
    ):

        # Atualiza todas as peças
        for row in self.board:

            for piece in row:

                if piece is not None:

                    piece.update(
                        dt
                    )

        self.phase_timer += dt

        # TROCA

        if self.phase == "swapping":

            moving = any(
                piece is not None
                and piece.moving
                for row in self.board
                for piece in row
            )

            if (
                not moving
                and self.phase_timer >= 0.05
            ):

                matches = self.find_matches()

                if matches:

                    self.start_match(
                        matches
                    )

                else:

                    # A troca permanece
                    self.phase = "idle"


        # EXPLOSÃO
        elif self.phase == "removing":

            # Só remove depois que TODAS as explosões terminaram.
            animation_finished = True

            for row, col in self.pending_matches:

                piece = self.board[
                    row
                ][
                    col
                ]

                if (
                    piece is not None
                    and piece.state != "finished"
                ):

                    animation_finished = False

                    break

            if animation_finished:

                self.remove_matches()


        # QUEDA

        elif self.phase == "falling":

            moving = any(
                piece is not None
                and piece.moving
                for row in self.board
                for piece in row
            )

            if (
                not moving
                and self.phase_timer >= 0.10
            ):

                # Verifica se a queda criou outro match.

                matches = self.find_matches()

                if matches:

                    self.start_match(
                        matches
                    )

                else:

                    self.phase = "idle"

    # desenhar
    def draw(
        self,
        screen
    ):

        # CÉLULAS
        for row in self.cells:

            for cell in row:

                cell.draw(
                    screen
                )

        # PEÇAS
        for row in self.board:

            for piece in row:

                if piece is not None:

                    piece.draw(
                        screen
                    )

        # CURSOR DO TECLADO
        cursor_rect = pygame.Rect(
            self.x
            + self.cursor_col
            * self.cell_size
            + 2,

            self.y
            + self.cursor_row
            * self.cell_size
            + 2,

            self.cell_size - 4,

            self.cell_size - 4
        )

        pygame.draw.rect(
            screen,
            (70, 200, 255),
            cursor_rect,
            3
        )


        # SELEÇÃO

        if self.selected is not None:

            row, col = self.selected

            selected_rect = pygame.Rect(

                self.x
                + col
                * self.cell_size
                + 4,

                self.y
                + row
                * self.cell_size
                + 4,

                self.cell_size - 8,

                self.cell_size - 8
            )

            pygame.draw.rect(
                screen,
                (255, 220, 70),
                selected_rect,
                4
            )

    # PONTUAÇÃO
    def get_score(self):
        return self.score