import math
import os
import numpy as np


class Camera:
    """This class represents a reconstructed camera.

    It provides functionality to manage intrinsic and extrinsic camera
    parameters as well as corresponding image and depth map information.
    """

    panoramic_type_equirectangular = "EQUIRECTANGULAR"

    IMAGE_FP_TYPE_NAME = "NAME"
    IMAGE_FP_TYPE_RELATIVE = "RELATIVE"
    IMAGE_FP_TYPE_ABSOLUTE = "ABSOLUTE"

    DEPTH_MAP_WRT_UNIT_VECTORS = "DEPTH_MAP_WRT_UNIT_VECTORS"
    DEPTH_MAP_WRT_CANONICAL_VECTORS = "DEPTH_MAP_WRT_CANONICAL_VECTORS"

    def __init__(self):
        self._center = np.array([0, 0, 0], dtype=float)  # C = -R^T t
        self._translation_vec = np.array([0, 0, 0], dtype=float)  # t = -R C
        self.normal = np.array([0, 0, 0], dtype=float)
        self.color = np.array([255, 255, 255], dtype=int)

        # Use these attributes ONLY with getter and setter methods
        self._quaternion = np.array([0, 0, 0, 0], dtype=float)
        self._rotation_mat = np.zeros((3, 3), dtype=float)

        self._calibration_mat = np.zeros((3, 3), dtype=float)

        self.image_fp_type = None
        self.image_dp = None

        # Use these attributes ONLY with the corresponding methods
        self._relative_fp = None
        self._absolute_fp = None
        self._undistorted_relative_fp = None
        self._undistorted_absolute_fp = None

        self.width = None
        self.height = None
        self._panoramic_type = None

        # Parameters of the depth map callback
        self._depth_map_callback = None
        self._depth_map_fp = None
        self._depth_map_semantic = None
        self._shift_depth_map_to_pixel_center = None

        self.id = None  # A unique identifier (natural number)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(
            "Camera: "
            + self._relative_fp
            + " "
            + str(self._center)
            + " "
            + str(self.normal)
        )

    def get_file_name(self):
        """Return the file name of the image used to register this camera."""
        return os.path.basename(self.get_absolute_fp())

    def set_relative_fp(self, relative_fp, image_fp_type):
        """Set the relative file path of the corresponding image."""
        self._relative_fp = relative_fp
        self.image_fp_type = image_fp_type

    def get_relative_fp(self):
        """Return the relative file path of the corresponding image."""
        return self._get_relative_fp(self._relative_fp, self._absolute_fp)

    def get_undistorted_relative_fp(self):
        """Return the relative file path of the undistorted image."""
        return self._get_relative_fp(
            self._undistorted_relative_fp, self._undistorted_absolute_fp
        )

    def _get_relative_fp(self, relative_fp, absolute_fp):
        if self.image_fp_type == Camera.IMAGE_FP_TYPE_NAME:
            assert relative_fp is not None
            return os.path.basename(relative_fp)
        elif self.image_fp_type == Camera.IMAGE_FP_TYPE_RELATIVE:
            assert relative_fp is not None
            return relative_fp
        elif self.image_fp_type == Camera.IMAGE_FP_TYPE_ABSOLUTE:
            assert absolute_fp is not None
            return absolute_fp
        else:
            assert False

    def set_absolute_fp(self, absolute_fp):
        """Set the absolute file path of the corresponding image."""
        self._absolute_fp = absolute_fp

    def get_absolute_fp(self):
        """Return the absolute file path of the corresponding image."""
        return self._get_absolute_fp(self._relative_fp, self._absolute_fp)

    def get_undistorted_absolute_fp(self):
        """Return the absolute file path of the undistorted image."""
        if self.image_fp_type == Camera.IMAGE_FP_TYPE_ABSOLUTE:
            assert False  # Not supported for undistorted images
        return self._get_absolute_fp(
            self._undistorted_relative_fp, self._undistorted_absolute_fp
        )

    def _get_absolute_fp(self, relative_fp, absolute_fp):
        if self.image_fp_type == Camera.IMAGE_FP_TYPE_NAME:
            assert self.image_dp is not None
            assert relative_fp is not None
            return os.path.join(self.image_dp, os.path.basename(relative_fp))
        elif self.image_fp_type == Camera.IMAGE_FP_TYPE_RELATIVE:
            assert self.image_dp is not None
            assert relative_fp is not None
            return os.path.join(self.image_dp, relative_fp)
        elif self.image_fp_type == Camera.IMAGE_FP_TYPE_ABSOLUTE:
            assert absolute_fp is not None
            return absolute_fp
        else:
            assert False

    def has_undistorted_absolute_fp(self):
        """Determine if there is an absolute path to the undistorted image."""
        requirements = False
        if self.image_fp_type == Camera.IMAGE_FP_TYPE_NAME:
            requirements = (self.image_dp is not None) and (
                self._undistorted_relative_fp is not None
            )
        elif self.image_fp_type == Camera.IMAGE_FP_TYPE_RELATIVE:
            requirements = (self.image_dp is not None) and (
                self._undistorted_relative_fp is not None
            )
        elif self.image_fp_type == Camera.IMAGE_FP_TYPE_ABSOLUTE:
            requirements = self._undistorted_absolute_fp is not None

        has_fp = False
        if requirements:
            fp = self._get_absolute_fp(
                self._undistorted_relative_fp, self._undistorted_absolute_fp
            )
            if os.path.isfile(fp):
                has_fp = True
        return has_fp

    def get_undistorted_file_name(self):
        """Return the file name of the undistorted image."""
        if self.has_undistorted_absolute_fp():
            return os.path.basename(self.get_undistorted_absolute_fp())
        else:
            return None

    def set_calibration(self, calibration_mat, radial_distortion):
        """Set calibration matrix and distortion parameter."""
        self._calibration_mat = np.asarray(calibration_mat, dtype=float)
        self._radial_distortion = radial_distortion
        assert self._radial_distortion is not None

    def has_focal_length(self):
        """Return wether the focal length value has been defined or not."""
        return self._calibration_mat[0][0] > 0

    def get_focal_length(self):
        """Return the focal length value."""
        return self._calibration_mat[0][0]

    def get_field_of_view(self):
        """Return the field of view corresponding to the focal length."""
        assert self.width is not None and self.height is not None
        angle = (
            math.atan(
                max(self.width, self.height) / (self.get_focal_length() * 2.0)
            )
            * 2.0
        )
        return angle

    def has_intrinsics(self):
        """Return wether the intrinsic parameters have been defined or not."""
        return self.has_focal_length() and self.has_principal_point()

    def _check_calibration_mat(self):
        assert self.has_focal_length() and self.has_principal_point()

    def get_calibration_mat(self):
        """Return the calibration matrix."""
        self._check_calibration_mat()
        return self._calibration_mat

    def set_calibration_mat(self, calibration_mat):
        """Set the calibration matrix."""
        self._calibration_mat = calibration_mat

    def set_principal_point(self, principal_point):
        """Set the principal point."""
        self._calibration_mat[0][2] = principal_point[0]
        self._calibration_mat[1][2] = principal_point[1]

    def get_principal_point(self):
        """Return the principal point."""
        calibration_mat = self.get_calibration_mat()
        cx = calibration_mat[0][2]
        cy = calibration_mat[1][2]
        return np.asarray([cx, cy], dtype=float)

    def has_principal_point(self):
        """Return wether the principal point has been defined or not."""
        cx_zero = np.isclose(self._calibration_mat[0][2], 0.0)
        cy_zero = np.isclose(self._calibration_mat[1][2], 0.0)
        initialized = (not cx_zero) and (not cy_zero)
        return initialized

    def is_panoramic(self):
        """Return wether the camera model is a panoramic camera or not."""
        return self._panoramic_type is not None

    def set_panoramic_type(self, panoramic_type):
        """Set the panoramic camera type."""
        self._panoramic_type = panoramic_type

    def get_panoramic_type(self):
        """Return the panoramic camera type (if any)."""
        return self._panoramic_type

    @staticmethod
    def compute_calibration_mat(focal_length, cx, cy):
        """Return the calibration matrix."""
        return np.array(
            [[focal_length, 0, cx], [0, focal_length, cy], [0, 0, 1]],
            dtype=float,
        )

    def set_rotation_with_quaternion(self, quaternion):
        """Set the camera rotation using a quaternion."""
        self._quaternion = quaternion
        # We must change the rotation matrixes as well.
        self._rotation_mat = Camera.quaternion_to_rotation_matrix(quaternion)

    def set_rotation_with_rotation_mat(
        self, rotation_mat, check_rotation=True
    ):
        """Set the camera rotation using a rotation matrix."""
        if check_rotation:
            assert self.__class__._is_rotation_mat_valid(rotation_mat)
        self._rotation_mat = rotation_mat
        # We must change the quaternion as well.
        self._quaternion = Camera.rotation_matrix_to_quaternion(rotation_mat)

    def set_camera_center_after_rotation(self, center, check_rotation=True):
        """Set the camera center after setting the camera rotation."""
        if check_rotation:
            assert self.__class__._is_rotation_mat_valid(self._rotation_mat)
        self._center = center
        # t = -R C
        self._translation_vec = -np.dot(self._rotation_mat, center)

    def set_camera_translation_vector_after_rotation(
        self, translation_vector, check_rotation=True
    ):
        """Set the camera translation after setting the camera rotation."""
        if check_rotation:
            assert self.__class__._is_rotation_mat_valid(self._rotation_mat)
        self._translation_vec = translation_vector
        # C = -R^T t
        self._center = -np.dot(
            self._rotation_mat.transpose(), translation_vector
        )

    def get_rotation_as_quaternion(self):
        """Return the rotation as quaternion."""
        return self._quaternion

    def get_rotation_as_rotation_mat(self):
        """Return the rotation as rotation matrix."""
        return self._rotation_mat

    def get_translation_vec(self):
        """Return the translation vector."""
        return self._translation_vec

    def get_camera_center(self):
        """Return the camera center."""
        return self._center

    def set_4x4_cam_to_world_mat(self, cam_to_world_mat, check_rotation=True):
        """Set the extrinsic parameters."""
        self.set_rotation_with_rotation_mat(
            cam_to_world_mat[0:3, 0:3].transpose(),
            check_rotation=check_rotation,
        )
        self.set_camera_center_after_rotation(
            cam_to_world_mat[0:3, 3], check_rotation=check_rotation
        )

    @staticmethod
    def _is_rotation_mat_valid(some_mat):
        # Test if rotation_mat is really a rotation matrix
        # (i.e. det = -1 or det = 1)
        det = np.linalg.det(some_mat)
        res = np.isclose(det, 1) or np.isclose(det, -1)
        return res

    @staticmethod
    def quaternion_to_rotation_matrix(q):
        """Convert a quaternion to a rotation matrix."""

        # Original C++ method ('SetQuaternionRotation()') is defined in
        # pba/src/pba/DataInterface.h.
        # Parallel bundle adjustment (pba) code (used by visualsfm) is provided
        # here: http://grail.cs.washington.edu/projects/mcba/
        qq = math.sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3])
        if qq > 0:  # Normalize the quaternion
            qw = q[0] / qq
            qx = q[1] / qq
            qy = q[2] / qq
            qz = q[3] / qq
        else:
            qw = 1
            qx = qy = qz = 0
        m = np.zeros((3, 3), dtype=float)
        m[0][0] = float(qw * qw + qx * qx - qz * qz - qy * qy)
        m[0][1] = float(2 * qx * qy - 2 * qz * qw)
        m[0][2] = float(2 * qy * qw + 2 * qz * qx)
        m[1][0] = float(2 * qx * qy + 2 * qw * qz)
        m[1][1] = float(qy * qy + qw * qw - qz * qz - qx * qx)
        m[1][2] = float(2 * qz * qy - 2 * qx * qw)
        m[2][0] = float(2 * qx * qz - 2 * qy * qw)
        m[2][1] = float(2 * qy * qz + 2 * qw * qx)
        m[2][2] = float(qz * qz + qw * qw - qy * qy - qx * qx)
        return m

    @staticmethod
    def rotation_matrix_to_quaternion(m):
        """Convert a rotation matrix to a quaternion."""

        # Original C++ method ('GetQuaternionRotation()') is defined in
        # pba/src/pba/DataInterface.h
        # Parallel bundle adjustment (pba) code (used by visualsfm) is provided
        # here: http://grail.cs.washington.edu/projects/mcba/
        q = np.array([0, 0, 0, 0], dtype=float)
        q[0] = 1 + m[0][0] + m[1][1] + m[2][2]
        if q[0] > 0.000000001:
            q[0] = math.sqrt(q[0]) / 2.0
            q[1] = (m[2][1] - m[1][2]) / (4.0 * q[0])
            q[2] = (m[0][2] - m[2][0]) / (4.0 * q[0])
            q[3] = (m[1][0] - m[0][1]) / (4.0 * q[0])
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

    def set_depth_map_callback(
        self,
        depth_map_callback,
        depth_map_ifp,
        depth_map_semantic,
        shift_depth_map_to_pixel_center,
    ):
        """Set the depth map callback."""
        self._depth_map_callback = depth_map_callback
        self._depth_map_fp = depth_map_ifp
        self._depth_map_semantic = depth_map_semantic
        self._shift_depth_map_to_pixel_center = shift_depth_map_to_pixel_center

    def get_depth_map_fp(self):
        """Return the depth map file path."""
        return self._depth_map_fp

    def get_depth_map(self):
        """Return the depth map."""
        if os.path.isfile(self._depth_map_fp):
            return self._depth_map_callback(self._depth_map_fp)
        else:
            return None

    def get_4x4_cam_to_world_mat(self):
        """Return the camera to world transformation matrix.

        This matrix can be used to convert homogeneous points given in camera
        coordinates to homogeneous points given in world coordinates.
        """
        # M = [R^T    c]
        #     [0      1]
        homogeneous_mat = np.identity(4, dtype=float)
        homogeneous_mat[
            0:3, 0:3
        ] = self.get_rotation_as_rotation_mat().transpose()
        homogeneous_mat[0:3, 3] = self.get_camera_center()
        return homogeneous_mat

    def convert_depth_map_to_world_coords(
        self, depth_map_display_sparsity=100
    ):
        """Convert the depth map to points in world coordinates."""
        cam_coords = self.convert_depth_map_to_cam_coords(
            depth_map_display_sparsity
        )
        world_coords = self.convert_cam_coords_to_world_coords(cam_coords)
        return world_coords

    def convert_cam_coords_to_world_coords(self, cam_coords):
        """Convert camera coordinates to world coordinates."""
        num_coords = cam_coords.shape[0]
        hom_entries = np.ones(num_coords).reshape((num_coords, 1))
        cam_coords_hom = np.hstack((cam_coords, hom_entries))
        world_coords_hom = (
            self.get_4x4_cam_to_world_mat().dot(cam_coords_hom.T).T
        )
        world_coords = np.delete(world_coords_hom, 3, 1)
        return world_coords

    def convert_depth_map_to_cam_coords(self, depth_map_display_sparsity=100):
        """Convert the depth map to points in camera coordinates."""
        assert depth_map_display_sparsity > 0

        depth_map = self.get_depth_map()

        height, width = depth_map.shape
        if self.height == height and self.width == width:
            x_step_size = 1.0
            y_step_size = 1.0
        else:
            x_step_size = self.width / width
            y_step_size = self.height / height

        fx, fy, skew, cx, cy = self._split_intrinsic_mat(
            self.get_calibration_mat()
        )

        # Use the local coordinate system of the camera to analyze its viewing
        # directions.The Blender camera coordinate system looks along the
        # negative z axis (blue), the up axis points along the y axis (green).

        indices = np.indices((height, width))
        y_index_list = indices[0].flatten()
        x_index_list = indices[1].flatten()

        depth_values = depth_map.flatten()

        assert len(x_index_list) == len(y_index_list) == len(depth_values)

        if self._shift_depth_map_to_pixel_center:
            # https://github.com/simonfuhrmann/mve/blob/master/libs/mve/depthmap.cc
            #  math::Vec3f v = invproj * math::Vec3f(
            #       (float)x + 0.5f, (float)y + 0.5f, 1.0f);
            u_index_coord_list = x_step_size * x_index_list + 0.5
            v_index_coord_list = y_step_size * y_index_list + 0.5
        else:
            # https://github.com/colmap/colmap/blob/dev/src/base/reconstruction.cc
            # COLMAP assumes that the upper left pixel center is (0.5, 0.5)
            # i.e. the pixels are already shifted
            u_index_coord_list = x_step_size * x_index_list
            v_index_coord_list = y_step_size * y_index_list

        # The cannoncial vectors are defined according to p.155 of
        # "Multiple View Geometry" by Hartley and Zisserman using a canonical
        # focal length of 1 , i.e. vec = [(x - cx) / fx, (y - cy) / fy, 1]
        skew_correction = (cy - v_index_coord_list) * skew / (fx * fy)
        x_coords_canonical = (u_index_coord_list - cx) / fx + skew_correction
        y_coords_canonical = (v_index_coord_list - cy) / fy
        z_coords_canonical = np.ones(len(depth_values), dtype=float)

        # Determine non-background data
        depth_values_not_nan = np.nan_to_num(depth_values)
        non_background_flags = depth_values_not_nan > 0
        x_coords_canonical_filtered = x_coords_canonical[non_background_flags]
        y_coords_canonical_filtered = y_coords_canonical[non_background_flags]
        z_coords_canonical_filtered = z_coords_canonical[non_background_flags]
        depth_values_filtered = depth_values[non_background_flags]

        if depth_map_display_sparsity > 1:
            x_coords_canonical_filtered = x_coords_canonical_filtered[
                ::depth_map_display_sparsity
            ]
            y_coords_canonical_filtered = y_coords_canonical_filtered[
                ::depth_map_display_sparsity
            ]
            z_coords_canonical_filtered = z_coords_canonical_filtered[
                ::depth_map_display_sparsity
            ]
            depth_values_filtered = depth_values_filtered[
                ::depth_map_display_sparsity
            ]

        if self._depth_map_semantic == Camera.DEPTH_MAP_WRT_CANONICAL_VECTORS:
            # In this case, the depth values are defined w.r.t. the canonical
            # vectors. This kind of depth data is used by Colmap.
            x_coords_filtered = (
                x_coords_canonical_filtered * depth_values_filtered
            )
            y_coords_filtered = (
                y_coords_canonical_filtered * depth_values_filtered
            )
            z_coords_filtered = (
                z_coords_canonical_filtered * depth_values_filtered
            )

        elif self._depth_map_semantic == Camera.DEPTH_MAP_WRT_UNIT_VECTORS:
            # In this case the depth values are defined w.r.t. the normalized
            # canonical vectors. This kind of depth data is used by MVE.
            cannonical_norms_filtered = np.linalg.norm(
                np.array(
                    [
                        x_coords_canonical_filtered,
                        y_coords_canonical_filtered,
                        z_coords_canonical_filtered,
                    ],
                    dtype=float,
                ),
                axis=0,
            )
            # Instead of normalizing the x,y and z component, we divide the
            # depth values by the corresponding norm.
            normalized_depth_values_filtered = (
                depth_values_filtered / cannonical_norms_filtered
            )
            x_coords_filtered = (
                x_coords_canonical_filtered * normalized_depth_values_filtered
            )
            y_coords_filtered = (
                y_coords_canonical_filtered * normalized_depth_values_filtered
            )
            z_coords_filtered = (
                z_coords_canonical_filtered * normalized_depth_values_filtered
            )

        else:
            assert False

        cam_coords = np.dstack(
            (x_coords_filtered, y_coords_filtered, z_coords_filtered)
        )[0]

        return cam_coords

    @staticmethod
    def _split_intrinsic_mat(intrinsic_mat):
        f_x = intrinsic_mat[0][0]
        f_y = intrinsic_mat[1][1]
        skew = intrinsic_mat[0][1]
        p_x = intrinsic_mat[0][2]
        p_y = intrinsic_mat[1][2]
        return f_x, f_y, skew, p_x, p_y
