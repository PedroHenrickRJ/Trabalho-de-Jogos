import pygame

class Polygon:
    HANDLE_RADIUS = 8

    def __init__(self, points):
        self.points = list(points)
        self.selected_vertex = None
        self.update_geometry()

    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    def update_geometry(self):
        self.bounding_box = self.get_bounding_box()
        self.convex = self.is_convex()

        if self.convex:
            self.convex_shapes = [self]
            self.decomposition_edges = []
        else:
            self.convex_shapes, self.decomposition_edges = \
                self.decompose(self.points)

    def get_bounding_box(self):
        #xs = [p[0] for p in self.points]
        #ys = [p[1] for p in self.points]


        xs = []
        ys = []
        for p in self.points:
            xs.append(p[0])
            ys.append(p[1])


        return pygame.Rect(
            min(xs), min(ys),
            max(xs) - min(xs),
            max(ys) - min(ys)
        )

    def cross(self, a, b, c):
        return (
            # xAB * yBC - yAB * XBC
            (b[0] - a[0]) * (c[1] - b[1])
            - (b[1] - a[1]) * (c[0] - b[0])
        )

    def is_convex(self, points=None):
        points = self.points if points is None else points

        signs = []

        for i in range(len(points)):
            a = points[i - 1]
            b = points[i]
            c = points[(i + 1) % len(points)]

            cross = self.cross(a, b, c)

            if abs(cross) > 0.0001:
                signs.append(cross > 0)

        return not signs or all(s == signs[0] for s in signs)

    # ---------------------------------------------------------
    # Point inside polygon
    # ---------------------------------------------------------

    def point_inside(self, point, polygon):
        x, y = point
        inside = False

        for i in range(len(polygon)):
            a = polygon[i]
            b = polygon[(i + 1) % len(polygon)]

            if (a[1] > y) != (b[1] > y):
                x_intersection = (
                    (b[0] - a[0]) *
                    (y - a[1]) /
                    (b[1] - a[1]) +
                    a[0]
                )

                if x < x_intersection:
                    inside = not inside

        return inside

    # ---------------------------------------------------------
    # Segment intersection
    # ---------------------------------------------------------

    def segments_intersect(self, a, b, c, d):
        def orientation(p, q, r):
            value = self.cross(p, q, r)

            if abs(value) < 0.0001:
                return 0

            return 1 if value > 0 else -1

        o1 = orientation(a, b, c)
        o2 = orientation(a, b, d)
        o3 = orientation(c, d, a)
        o4 = orientation(c, d, b)

        return o1 != o2 and o3 != o4

    # ---------------------------------------------------------
    # Check whether a diagonal is valid
    # ---------------------------------------------------------

    def valid_diagonal(self, a, b, points):
        # Diagonal cannot cross an existing edge
        for i in range(len(points)):
            c = points[i]
            d = points[(i + 1) % len(points)]

            if c in (a, b) or d in (a, b):
                continue

            if self.segments_intersect(a, b, c, d):
                return False

        # Its midpoint must remain inside the polygon
        midpoint = (
            (a[0] + b[0]) / 2,
            (a[1] + b[1]) / 2
        )

        return self.point_inside(midpoint, points)

    # ---------------------------------------------------------
    # Recursive convex decomposition
    # ---------------------------------------------------------

    def decompose(self, points):
        # Already convex
        if self.is_convex(points):
            return [Polygon(points)], []

        n = len(points)

        for i in range(n):

            prev = points[i - 1]
            curr = points[i]
            next = points[(i + 1) % n]

            # We only want convex vertices
            if self.cross(prev, curr, next) <= 0:
                continue

            # The triangle formed by the neighboring vertices
            triangle = [prev, curr, next]

            # Remove the middle vertex
            remaining = points[:i] + points[i + 1:]

            # If this triangle's diagonal is valid...
            if not self.valid_diagonal(prev, next, points):
                continue

            # ...and the remainder is convex, we're done
            if self.is_convex(remaining):

                return (
                    [Polygon(triangle), Polygon(remaining)],
                    [(prev, next)]
                )

            # Otherwise recursively decompose the remainder
            shapes, edges = self.decompose(remaining)

            return (
                [Polygon(triangle)] + shapes,
                [(prev, next)] + edges
            )

        # Should only happen for invalid/self-intersecting polygons
        return [Polygon(points)], []

    # ---------------------------------------------------------
    # Mouse interaction
    # ---------------------------------------------------------

    def start_drag(self, mouse_pos):
        for i, p in enumerate(self.points):

            dx = mouse_pos[0] - p[0]
            dy = mouse_pos[1] - p[1]

            if dx * dx + dy * dy <= self.HANDLE_RADIUS ** 2:
                self.selected_vertex = i
                return

    def drag(self, mouse_pos):
        if self.selected_vertex is not None:
            self.points[self.selected_vertex] = mouse_pos
            self.update_geometry()

    def stop_drag(self):
        self.selected_vertex = None

    # ---------------------------------------------------------
    # Drawing
    # ---------------------------------------------------------

    def draw(self, screen, highlight=None):

        # Bounding box
        pygame.draw.rect(
            screen,
            (80, 80, 80),
            self.bounding_box,
            2
        )

        # Original polygon
        pygame.draw.polygon(
            screen,
            (100, 180, 100),
            self.points
        )

        pygame.draw.polygon(
            screen,
            (255, 255, 255),
            self.points,
            2
        )

        # Decomposition lines
        for a, b in self.decomposition_edges:
            pygame.draw.line(
                screen,
                (255, 200, 50),
                a, b, 3
            )

        # Highlight the colliding convex shape
        if highlight is not None:

            pygame.draw.polygon(
                screen,
                (220, 70, 70),
                highlight.points
            )

            pygame.draw.polygon(
                screen,
                (255, 255, 255),
                highlight.points,
                2
            )

        # Vertices
        for i, p in enumerate(self.points):

            color = (
                (255, 255, 0)
                if i == self.selected_vertex
                else (255, 100, 100)
            )

            pygame.draw.circle(
                screen,
                color,
                p,
                self.HANDLE_RADIUS
            )