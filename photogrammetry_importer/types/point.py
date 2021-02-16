from collections import namedtuple


class Point(namedtuple("Point", ["coord", "color", "id", "scalars"])):
    """This class represents a three-dimensional point.

    A point contains the following attributes: 3D coordinate, color, point id
    and a list of scalars.
    """

    @staticmethod
    def split_points(points, normalize_colors=False):
        """Split points into coordinates and colors."""
        coords = []
        colors = []

        if normalize_colors:
            color_normalize_factor = 255.0
        else:
            color_normalize_factor = 1

        for point in points:
            coords.append(point.coord)
            color_with_alpha = [
                point.color[0] / color_normalize_factor,
                point.color[1] / color_normalize_factor,
                point.color[2] / color_normalize_factor,
                1.0,
            ]
            colors.append(color_with_alpha)
        return coords, colors

    @staticmethod
    def create_points(coords, colors, unnormalize_colors=False):
        if unnormalize_colors:
            color_unnormalize_factor = 255.0
        else:
            color_unnormalize_factor = 1
        return [
            Point(
                coord=coord,
                color=[val * color_unnormalize_factor for val in color],
                id=idx,
                scalars=None,
            )
            for idx, (coord, color) in enumerate(zip(coords, colors))
        ]
