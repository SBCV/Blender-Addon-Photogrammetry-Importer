from collections import namedtuple

class Point(namedtuple('Point', ['coord', 'color', 'id', 'scalars'])):
    """ 
    This class represents a three-dimensional point with the following information:
    3D coordinate, color, point id and a list of scalars
    """

    @staticmethod
    def split_points(points):
        positions = []
        colors = []
        for point in points:
            positions.append(point.coord)
            color_with_alpha = [
                point.color[0] / 255.0, point.color[1] / 255.0, point.color[2] / 255.0, 1.0]
            colors.append(color_with_alpha)
        return positions, colors
