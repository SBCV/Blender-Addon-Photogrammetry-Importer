from collections import namedtuple

class Point(namedtuple('Point', ['coord', 'color', 'measurements', 'id', 'scalars'])):
    """ 
    This class represents a three-dimensional point with the following information:
    3D coordinate, color, a list of measurements, point id and a list of scalars
    """

