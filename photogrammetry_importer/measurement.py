from collections import namedtuple

class Measurement(namedtuple('Measurement', ['image_index', 'feature_index', 'x', 'y'])):
    """ 
    This class represents a measurement with the following information:
    image_index, feature_index, and x as well as y position.
    """