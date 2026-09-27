class Collide:

    @staticmethod
    def polygon(a, b):

        if not a.bounding_box.colliderect(b.bounding_box):
            return None

        for shape_a in a.convex_shapes:
            for shape_b in b.convex_shapes:

                if Collide.convex(shape_a.points, shape_b.points):
                    return shape_a, shape_b

        return None

    @staticmethod
    def convex(a, b):

        for axis in Collide.axes(a) + Collide.axes(b):

            min_a, max_a = Collide.project(a, axis)
            min_b, max_b = Collide.project(b, axis)

            if max_a < min_b or max_b < min_a:
                return False

        return True

    @staticmethod
    def axes(points):
        axes = []

        for i in range(len(points)):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % len(points)]

            dx = x2 - x1
            dy = y2 - y1

            axis = (-dy, dx)

            length = (axis[0] ** 2 + axis[1] ** 2) ** 0.5

            if length:
                axes.append((
                    axis[0] / length,
                    axis[1] / length
                ))

        return axes

    @staticmethod
    def project(points, axis):
        values = [
            p[0] * axis[0] + p[1] * axis[1]
            for p in points
        ]

        return min(values), max(values)