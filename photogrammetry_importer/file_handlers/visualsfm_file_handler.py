import os
from collections import defaultdict
import numpy as np

from photogrammetry_importer.types.camera import Camera
from photogrammetry_importer.types.point import Point
from photogrammetry_importer.file_handlers.utility import (
    check_radial_distortion,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report


class VisualSfMFileHandler:
    """Class to read and write :code:`VisualSfM` files."""

    # Check the LoadNVM function in util.h of the
    # Multicore bundle adjustment code for more details.
    # http://grail.cs.washington.edu/projects/mcba/
    # pba/src/pba/util.h

    @classmethod
    def _parse_cameras(
        cls,
        input_file,
        num_cameras,
        camera_calibration_matrix,
        image_dp,
        image_fp_type,
        suppress_distortion_warnings,
        op=None,
    ):

        """
        VisualSFM CAMERA coordinate system is the standard CAMERA
        coordinate system in computer vision (not the same as
        in computer graphics like in bundler, blender, etc.)
        That means the y axis in the image is pointing downwards (not upwards)
        and the camera is looking along the positive z axis (points in front
        of the camera show a positive z value)

        The camera coordinate system in computer vision VISUALSFM uses camera
        matrices, which are rotated around the x axis by 180 degree
        i.e. the y and z axis of the CAMERA MATRICES are inverted
        therefore, the y and z axis of the TRANSLATION VECTOR are also inverted
        """
        # log_report('INFO', '_parse_cameras: ...', op)
        cameras = []

        for i in range(num_cameras):
            line = input_file.readline()

            # Read the camera section
            # From the docs:
            # <Camera> = <File name> <focal length> <quaternion WXYZ> <camera center> <radial distortion> 0
            line_values = line.split()
            relative_path = line_values[0].replace("/", os.sep)
            focal_length = float(line_values[1])

            quaternion_w = float(line_values[2])
            quaternion_x = float(line_values[3])
            quaternion_y = float(line_values[4])
            quaternion_z = float(line_values[5])
            quaternion = np.array(
                [quaternion_w, quaternion_x, quaternion_y, quaternion_z],
                dtype=float,
            )

            camera_center_x = float(line_values[6])
            camera_center_y = float(line_values[7])
            camera_center_z = float(line_values[8])
            center_vec = np.array(
                [camera_center_x, camera_center_y, camera_center_z]
            )

            radial_distortion = float(line_values[9])
            if not suppress_distortion_warnings:
                check_radial_distortion(radial_distortion, relative_path, op)

            if camera_calibration_matrix is None:
                # In this case, we have no information about the principal point
                # We assume that the principal point lies in the center
                camera_calibration_matrix = np.array(
                    [[focal_length, 0, 0], [0, focal_length, 0], [0, 0, 1]]
                )

            zero_value = float(line_values[10])
            assert zero_value == 0

            current_camera = Camera()
            # Setting the quaternion also sets the rotation matrix
            current_camera.set_rotation_with_quaternion(quaternion)

            # Set the camera center after rotation
            current_camera._center = center_vec

            # set the camera view direction as normal w.r.t world coordinates
            cam_view_vec_cam_coord = np.array([0, 0, 1]).T
            cam_rotation_matrix_inv = np.linalg.inv(
                current_camera.get_rotation_as_rotation_mat()
            )
            cam_view_vec_world_coord = cam_rotation_matrix_inv.dot(
                cam_view_vec_cam_coord
            )
            current_camera.normal = cam_view_vec_world_coord

            translation_vec = cls._compute_translation_vector(
                center_vec, current_camera.get_rotation_as_rotation_mat()
            )
            current_camera._translation_vec = translation_vec

            current_camera.set_calibration(
                camera_calibration_matrix, radial_distortion=radial_distortion
            )
            # log_report('INFO', 'Calibration mat:', op)
            # log_report('INFO', str(camera_calibration_matrix), op)

            current_camera.image_fp_type = image_fp_type
            current_camera.image_dp = image_dp
            current_camera._relative_fp = relative_path
            current_camera.id = i
            cameras.append(current_camera)
        # log_report('INFO', '_parse_cameras: Done', op)
        return cameras

    @staticmethod
    def _parse_nvm_points(input_file, num_3D_points):

        points = []
        for point_index in range(num_3D_points):
            # From the VSFM docs:
            # <Point>  = <XYZ> <RGB> <number of measurements> <List of Measurements>
            point_line = input_file.readline()
            point_line_elements = (point_line.rstrip()).split()
            xyz_vec = list(map(float, point_line_elements[0:3]))
            rgb_vec = list(map(int, point_line_elements[3:6]))
            current_point = Point(
                coord=xyz_vec, color=rgb_vec, id=point_index, scalars=None
            )
            points.append(current_point)

        return points

    @staticmethod
    def _parse_fixed_calibration(line, op):

        line_elements = line.split()
        if len(line_elements) == 1:
            assert line.startswith("NVM_V3")
            calib_mat = None
        elif len(line_elements) == 7:
            _, _, fx, cx, fy, cy, radial_distortion = line_elements
            calib_mat = np.array(
                [
                    [float(fx), 0, float(cx)],
                    [0, float(fy), float(cy)],
                    [0, 0, 1],
                ]
            )
        else:
            assert False
        if calib_mat is not None:
            log_report("INFO", "Found Fixed Calibration in NVM File.", op)
            # log_report('INFO', 'Fixed calibration mat:', op)
            # log_report('INFO', str(calib_mat), op)
        return calib_mat

    @classmethod
    def parse_visualsfm_file(
        cls,
        input_visual_fsm_file_name,
        image_dp,
        image_fp_type,
        suppress_distortion_warnings,
        op=None,
    ):
        """Parse a :code:`VisualSfM` (:code:`.nvm`) file."""
        log_report("INFO", "Parse NVM file: " + input_visual_fsm_file_name, op)
        input_file = open(input_visual_fsm_file_name, "r")
        # Documentation of *.NVM data format
        # http://ccwu.me/vsfm/doc.html#nvm

        # In a simple case there is only one model

        # Each reconstructed <model> contains the following
        # <Number of cameras>   <List of cameras>
        # <Number of 3D points> <List of points>

        # Read the first two lines (fixed)
        current_line = (input_file.readline()).rstrip()
        calibration_matrix = cls._parse_fixed_calibration(current_line, op)
        current_line = (input_file.readline()).rstrip()
        assert current_line == ""

        amount_cameras = int((input_file.readline()).rstrip())
        log_report(
            "INFO",
            "Amount Cameras (Images in NVM file): " + str(amount_cameras),
            op,
        )

        cameras = cls._parse_cameras(
            input_file,
            amount_cameras,
            calibration_matrix,
            image_dp,
            image_fp_type,
            suppress_distortion_warnings,
            op,
        )
        current_line = (input_file.readline()).rstrip()
        assert current_line == ""
        current_line = (input_file.readline()).rstrip()
        if current_line.isdigit():
            amount_points = int(current_line)
            log_report(
                "INFO",
                "Amount Sparse Points (Points in NVM file): "
                + str(amount_points),
                op,
            )
            points = cls._parse_nvm_points(input_file, amount_points)
        else:
            points = []

        log_report("INFO", "Parse NVM file: Done", op)
        return cameras, points

    @staticmethod
    def _create_nvm_first_line(cameras, op):

        log_report("INFO", "create_nvm_first_line: ...", op)
        # The first line can be either
        #   'NVM_V3'
        # or
        #   'NVM_V3 FixedK fx cx fy cy r'

        calib_mat = cameras[0].get_calibration_mat()
        log_report("INFO", "calib_mat: " + str(calib_mat), op)
        # radial_dist = None
        # if cameras[0].has_radial_distortion():
        #     radial_dist = cameras[0].has_radial_distortion()

        fixed_calibration = True
        for cam in cameras:
            log_report(
                "INFO",
                "cam.get_calibration_mat(): " + str(cam.get_calibration_mat()),
                op,
            )
            if not np.allclose(cam.get_calibration_mat(), calib_mat):
                log_report("INFO", "calib_mat: " + str(calib_mat), op)
                fixed_calibration = False
                break
        log_report("INFO", "fixed_calibration: " + str(fixed_calibration), op)
        if fixed_calibration:
            fl = "NVM_V3 FixedK"
            fl += " " + str(calib_mat[0][0])
            fl += " " + str(calib_mat[0][2])
            fl += " " + str(calib_mat[1][1])
            fl += " " + str(calib_mat[1][2])
            fl += " " + str(0)  # TODO Radial distortion
        else:
            fl = "NVM_V3"
        log_report("INFO", "fl: " + fl, op)
        log_report("INFO", "create_nvm_first_line: Done", op)
        return fl

    @staticmethod
    def _nvm_line(content):
        return content + " " + os.linesep

    @classmethod
    def write_visualsfm_file(
        cls, output_nvm_file_name, cameras, points, op=None
    ):
        """Write cameras and points as :code:`.nvm` file."""

        log_report("INFO", "Write NVM file: " + output_nvm_file_name, op)

        nvm_content = []
        nvm_content.append(
            cls._nvm_line(cls._create_nvm_first_line(cameras, op))
        )
        nvm_content.append(cls._nvm_line(""))
        amount_cameras = len(cameras)
        nvm_content.append(cls._nvm_line(str(amount_cameras)))
        log_report(
            "INFO",
            "Amount Cameras (Images in NVM file):" + str(amount_cameras),
            op,
        )

        # Write the camera section
        # From the VSFM docs:
        # <Camera> = <File name> <focal length> <quaternion WXYZ> <camera center> <radial distortion> 0

        for camera in cameras:
            quaternion = camera.get_rotation_as_quaternion()

            current_line = camera.get_relative_fp()
            current_line += "\t" + str(camera.get_calibration_mat()[0][0])
            current_line += " " + " ".join(list(map(str, quaternion)))
            current_line += " " + " ".join(
                list(map(str, camera.get_camera_center()))
            )
            current_line += " " + "0"  # TODO USE RADIAL DISTORTION
            current_line += " " + "0"
            nvm_content.append(current_line + " " + os.linesep)

        nvm_content.append(" " + os.linesep)
        number_points = len(points)
        nvm_content.append(str(number_points) + " " + os.linesep)
        log_report(
            "INFO", "Found " + str(number_points) + " object points", op
        )

        num_features = 2
        image_idx = 0
        feature_idx = 0
        x = 0.0
        y = 0.0

        for point in points:
            # From the VSFM docs:
            # <Point>  = <XYZ> <RGB> <number of measurements> <List of Measurements>
            current_line = " ".join(list(map(str, point.coord)))
            current_line += " " + " ".join(list(map(str, point.color)))

            # current_line += ' ' + str(len(point.measurements))
            # for measurement in point.measurements:
            #     current_line += ' ' + str(measurement)
            current_line += " " + str(num_features)
            for feature in range(num_features):
                current_line += (
                    " "
                    + str(image_idx)
                    + " "
                    + str(feature_idx)
                    + " "
                    + str(x)
                    + " "
                    + str(y)
                )

            nvm_content.append(current_line + " " + os.linesep)

        nvm_content.append(" " + os.linesep)
        nvm_content.append(" " + os.linesep)
        nvm_content.append(" " + os.linesep)
        nvm_content.append("0" + os.linesep)
        nvm_content.append(" " + os.linesep)
        nvm_content.append(
            "#the last part of NVM file points to the PLY files " + os.linesep
        )
        nvm_content.append(
            "#the first number is the number of associated PLY files "
            + os.linesep
        )
        nvm_content.append(
            "#each following number gives a model-index that has PLY "
            + os.linesep
        )
        nvm_content.append("0" + os.linesep)

        output_file = open(output_nvm_file_name, "wb")
        output_file.writelines([item.encode() for item in nvm_content])

        log_report("INFO", "Write NVM file: Done", op)

    @staticmethod
    def _compute_translation_vector(c, R):

        """
        x_cam = R (X - C) = RX - RC == RX + t
        <=> t = -RC
        """
        t = np.zeros(3, dtype=float)
        for j in range(0, 3):
            t[j] = -float(R[j][0] * c[0] + R[j][1] * c[1] + R[j][2] * c[2])
        return t
