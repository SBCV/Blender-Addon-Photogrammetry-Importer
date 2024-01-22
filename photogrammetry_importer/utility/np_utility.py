import numpy as np


def is_rotation_mat(some_mat):
    """Test if a matrix is a rotation matrix."""
    # (i.e. det = -1 or det = 1)
    det = np.linalg.det(some_mat)
    res = np.isclose(det, 1) or np.isclose(det, -1)
    return res


def invert_transformation_matrix(mat):
    """Invert transformation matrix without numerical errors."""
    assert is_rotation_mat(mat)
    # Analogue to set_camera_translation_vector_after_rotation()
    mat_copy = np.array(mat).copy()
    mat_copy[0:3, 3] = -np.dot(mat[0:3, 0:3].T, mat_copy[0:3, 3])
    mat_copy[0:3, 0:3] = mat[0:3, 0:3].T
    return mat_copy
