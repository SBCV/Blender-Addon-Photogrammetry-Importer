__author__ = 'sebastian'

import numpy as np
import math

class Camera:
    def __init__(self):
        self._center = np.array([0, 0, 0], dtype=float)              # C = -R^T t
        self._translation_vec = np.array([0, 0, 0], dtype=float)     # t = -R C
        self.normal = np.array([0, 0, 0], dtype=float)
        self.color = np.array([255, 255, 255], dtype=int)

        # use for these attributes the getter and setter methods
        self._quaternion = np.array([0, 0, 0, 0], dtype=float)
        self._rotation_mat = np.zeros((3, 3), dtype=float)
        
        self._calibration_mat = np.zeros((3, 3), dtype=float)
        
        self.file_name = None
        self.width = None
        self.height = None

        self.id = None  # an unique identifier (natural number)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str('Camera: ' + self.file_name + ' ' + str(self._center) + ' ' + str(self.normal))

    def set_calibration(self, calibration_mat, radial_distortion):
        self._calibration_mat = np.asarray(calibration_mat, dtype=float)
        self._radial_distortion = radial_distortion
        assert self._radial_distortion is not None
        
    def get_focal_length(self):
        return self._calibration_mat[0][0]
    
    def check_calibration_mat(self):
        assert self.is_principal_point_initialized()
    
    def get_calibration_mat(self):
        self.check_calibration_mat()
        return self._calibration_mat
    
    def set_calibration_mat(self, calibration_mat):
        self._calibration_mat = calibration_mat

    def set_principal_point(self, principal_point):
        self._calibration_mat[0][2] = principal_point[0]
        self._calibration_mat[1][2] = principal_point[1]

    def get_principal_point(self):
        calibration_mat = self.get_calibration_mat()
        cx = calibration_mat[0][2]
        cy = calibration_mat[1][2]
        return np.asarray([cx,cy], dtype=float)
    
    def is_principal_point_initialized(self):
        cx_zero = np.isclose(self._calibration_mat[0][2], 0.0)
        cy_zero = np.isclose(self._calibration_mat[1][2], 0.0)
        initialized = (not cx_zero) and (not cy_zero)
        return initialized

    @staticmethod
    def compute_calibration_mat(focal_length, cx, cy):
        return np.array([[focal_length, 0, cx], [0, focal_length, cy], [0,0,1]], dtype=float)

    def set_quaternion(self, quaternion):
        self._quaternion = quaternion
        # we must change the rotation matrixes as well
        self._rotation_mat = Camera.quaternion_to_rotation_matrix(quaternion)

    def set_rotation_mat(self, rotation_mat):
        assert Camera.is_rotation_mat_valid(rotation_mat)
        self._rotation_mat = rotation_mat
        # we must change the quaternion as well
        self._quaternion = Camera.rotation_matrix_to_quaternion(rotation_mat)

    def set_camera_center_after_rotation(self, center):
        assert Camera.is_rotation_mat_valid(self._rotation_mat)
        self._center = center
        self._translation_vec = - np.dot(self._rotation_mat, center)    # t = -R C

    def set_camera_translation_vector_after_rotation(self, translation_vector):
        assert Camera.is_rotation_mat_valid(self._rotation_mat)
        self._translation_vec = translation_vector
        self._center = - np.dot(self._rotation_mat.transpose(), translation_vector) # C = -R^T t

    def get_quaternion(self):
        return self._quaternion

    def get_rotation_mat(self):
        return self._rotation_mat

    def get_translation_vec(self):
        return self._translation_vec

    def get_camera_center(self):
        return self._center
    
    def set_4x4_cam_to_world_mat(self, cam_to_world_mat):
        self.set_rotation_mat(cam_to_world_mat[0:3, 0:3].transpose())
        self.set_camera_center_after_rotation(cam_to_world_mat[0:3, 3])

    @staticmethod
    def is_rotation_mat_valid(some_mat):
        # test if rotation_mat is really a rotation matrix (i.e. det = -1 or det = 1)
        return np.isclose(np.linalg.det(some_mat), 1) or np.isclose(np.linalg.det(some_mat), -1)

    @staticmethod
    def quaternion_to_rotation_matrix(q):
        """
        Original C++ Method ('SetQuaternionRotation()') defined in  pba/src/pba/DataInterface.h
        Parallel bundle adjustment (pba) code (used by visualsfm) is provided here:
            http://grail.cs.washington.edu/projects/mcba/
        """
        qq = math.sqrt(q[0]*q[0]+q[1]*q[1]+q[2]*q[2]+q[3]*q[3])
        if qq > 0:  # Normalize the quaternion
            qw = q[0]/qq
            qx = q[1]/qq
            qy = q[2]/qq
            qz = q[3]/qq
        else:
            qw = 1
            qx = qy = qz = 0
        m = np.zeros((3, 3), dtype=float)
        m[0][0] = float(qw*qw + qx*qx- qz*qz- qy*qy )
        m[0][1] = float(2*qx*qy -2*qz*qw )
        m[0][2] = float(2*qy*qw + 2*qz*qx)
        m[1][0] = float(2*qx*qy+ 2*qw*qz)
        m[1][1] = float(qy*qy+ qw*qw - qz*qz- qx*qx)
        m[1][2] = float(2*qz*qy- 2*qx*qw)
        m[2][0] = float(2*qx*qz- 2*qy*qw)
        m[2][1] = float(2*qy*qz + 2*qw*qx )
        m[2][2] = float(qz*qz+ qw*qw- qy*qy- qx*qx)
        return m

    @staticmethod
    def rotation_matrix_to_quaternion(m):
        """
        Original C++ Method ('GetQuaternionRotation()') defined in  pba/src/pba/DataInterface.h
        Parallel bundle adjustment (pba) code (used by visualsfm) is provided here:
            http://grail.cs.washington.edu/projects/mcba/
        """
        q = np.array([0, 0, 0, 0], dtype=float)
        q[0] = 1 + m[0][0] + m[1][1] + m[2][2]
        if q[0] > 0.000000001:
            q[0] = math.sqrt(q[0]) / 2.0
            q[1] = (m[2][1] - m[1][2]) / ( 4.0 * q[0])
            q[2] = (m[0][2] - m[2][0]) / ( 4.0 * q[0])
            q[3] = (m[1][0] - m[0][1]) / ( 4.0 * q[0])
        else:
            if m[0][0] > m[1][1] and m[0][0] > m[2][2]:
                s = 2.0 * math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2])
                q[1] = 0.25 * s
                q[2] = (m[0][1] + m[1][0]) / s
                q[3] = (m[0][2] + m[2][0]) / s
                q[0] = (m[1][2] - m[2][1]) / s
            elif m[1][1] > m[2][2]:
                s = 2.0 * math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2])
                q[1] = (m[0][1] + m[1][0]) / s
                q[2] = 0.25 * s
                q[3] = (m[1][2] + m[2][1]) / s
                q[0] = (m[0][2] - m[2][0]) / s
            else:
                s = 2.0 * math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1])
                q[1] = (m[0][2] + m[2][0]) / s
                q[2] = (m[1][2] + m[2][1]) / s
                q[3] = 0.25 * s
                q[0] = (m[0][1] - m[1][0]) / s
        return q




