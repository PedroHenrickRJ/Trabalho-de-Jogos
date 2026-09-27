import pygame
from shape import Polygon
from collision import Collide

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()


# -------------------------------------------------------------
# Example
# -------------------------------------------------------------

polygon_a = Polygon([
    (150, 150),
    (400, 100),
    (600, 250),
    (400, 220),   # concave
    (450, 400),
    (250, 350),
])

polygon_b = Polygon([
    (350, 250),
    (550, 200),
    (650, 350),
    (500, 500),
    (350, 400),
])


polygons = [polygon_a, polygon_b]

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:

                # Try to select a vertex from each polygon
                for polygon in polygons:
                    polygon.start_drag(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:

                for polygon in polygons:
                    polygon.stop_drag()

        elif event.type == pygame.MOUSEMOTION:

            for polygon in polygons:
                polygon.drag(event.pos)

    screen.fill((30, 30, 30))

    # Draw polygons
    for polygon in polygons:
        polygon.draw(screen)

    # Collision
    collision = Collide.polygon(
    polygon_a,
    polygon_b
)

    if collision:
        shape_a, shape_b = collision
    else:
        shape_a = None
        shape_b = None

    polygon_a.draw(screen, shape_a)
    polygon_b.draw(screen, shape_b)

    font = pygame.font.SysFont(None, 30)

    text = font.render(
        f"Collision: {collision} | "
        f"A: {len(polygon_a.convex_shapes)} shapes | "
        f"B: {len(polygon_b.convex_shapes)} shapes",
        True,
        (255, 255, 255)
    )

    screen.blit(text, (10, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()