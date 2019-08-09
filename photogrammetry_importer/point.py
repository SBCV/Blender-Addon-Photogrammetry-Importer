from collections import namedtuple

class Point(namedtuple('Point', ['coord', 'color', 'id', 'scalars'])):
    """ 
    This class represents a three-dimensional point with the following information:
    3D coordinate, color, point id and a list of scalars
    """

