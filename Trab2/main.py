import os

import pygame

from grid import Grid

pygame.init()
pygame.font.init()


WIDTH = 800
HEIGHT = 600

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT)
)

pygame.display.set_caption("Match 3")

clock = pygame.time.Clock()


GRID_SIZE = (8, 8)
CELL_SIZE = 60
GRID_WIDTH = GRID_SIZE[1] * CELL_SIZE
GRID_HEIGHT = GRID_SIZE[0] * CELL_SIZE
GRID_X = (WIDTH - GRID_WIDTH) // 2
GRID_Y = (HEIGHT - GRID_HEIGHT) // 2


PIECE_IMAGE_PATHS = [
    "images/Mana.png",
    "images/Lua Pálida.png",
    "images/Vela Negra.png",
    "images/Estrela.png"
]

EXPLOSION_IMAGE_PATHS = [
    "images/explosion/explosão1.png",
    "images/explosion/explosão2.png",
    "images/explosion/explosão3.png",
    "images/explosion/explosão4.png"
]

def load_images(paths):
    images = []

    for path in paths:

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Imagem não encontrada: {path}"
            )

        image = pygame.image.load(
            path
        ).convert_alpha()

        images.append(image)

    return images


piece_images = load_images(
    PIECE_IMAGE_PATHS
)

explosion_images = load_images(
    EXPLOSION_IMAGE_PATHS
)


# CRIA O GRID
grid = Grid(
    GRID_X,
    GRID_Y,
    GRID_SIZE,
    CELL_SIZE,
    piece_images,
    explosion_images
)


objects = [
    grid
]

score_font = pygame.font.Font(
    None,
    32
)


# =============================================================
# LOOP PRINCIPAL
# =============================================================

running = True

while running:

    dt = clock.tick(60) / 1000.0

    # ----------------------- EVENTOS ----------------------------------

    for event in pygame.event.get():

        # Fechar janela
        if event.type == pygame.QUIT:
            running = False

        # Mouse
        elif event.type == pygame.MOUSEMOTION:

            grid.hover_cell = grid.world_to_cell(
                event.pos
            )

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:
                grid.handle_mouse_click(
                    event.pos
                )

        # Teclado
        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

            else:
                grid.handle_key(
                    event.key
                )


    # atualizar
    for obj in objects:
        obj.update(dt)


    # desenhar
    screen.fill(
        (25, 25, 32)
    )

    for obj in objects:
        obj.draw(screen)


    # PLACAR
    score_text = score_font.render(
        f"Pontuação: {grid.get_score()}",
        True,
        (235, 235, 240)
    )

    score_rect = score_text.get_rect(
        center=(
            WIDTH // 2,
            30
        )
    )

    screen.blit(
        score_text,
        score_rect
    )

    pygame.display.flip()


pygame.quit()