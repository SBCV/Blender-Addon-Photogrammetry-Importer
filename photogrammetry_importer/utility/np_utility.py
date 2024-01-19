import numpy as np


def is_rotation_mat_valid(some_mat):
    """ Test if a matrix is a rotation matrix."""
    # (i.e. det = -1 or det = 1)
    det = np.linalg.det(some_mat)
    res = np.isclose(det, 1) or np.isclose(det, -1)
    return res
