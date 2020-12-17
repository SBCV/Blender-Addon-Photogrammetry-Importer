import json
import numpy as np
import os

from photogrammetry_importer.types.camera import Camera
from photogrammetry_importer.types.point import Point
from photogrammetry_importer.utility.os_utility import (
    get_image_file_paths_in_dir,
)

from photogrammetry_importer.blender_utility.logging_utility import log_report


class Open3DFileHandler:
    """Class to read and write :code:`Open3D` files."""

    @staticmethod
    def parse_open3d_file(open3d_ifp, image_dp, image_fp_type, op):
        """Parse an :code:`Open3D` (:code:`.json` or :code:`.log`) file.

        The :code:`.json` format supports intrinsics as well as
        extrinsic parameters, whereas the :code:`.log` (`Redwood
        <http://redwood-data.org/indoor/fileformat.html>`_) format contains
        only extrinsic parameters.
        """
        log_report("INFO", "parse_open3d_file: ...", op)
        log_report("INFO", "open3d_ifp: " + open3d_ifp, op)
        log_report("INFO", "image_dp: " + image_dp, op)

        image_relative_fp_list = get_image_file_paths_in_dir(
            image_dp,
            relative_path_only=True,
            without_ext=False,
            sort_result=True,
            recursive=True,
        )

        cams = []
        if os.path.splitext(open3d_ifp)[1].lower() == ".json":
            cams = Open3DFileHandler._parse_open3d_json_file(
                open3d_ifp, image_dp, image_relative_fp_list, image_fp_type, op
            )
        elif os.path.splitext(open3d_ifp)[1].lower() == ".log":
            cams = Open3DFileHandler._parse_open3d_log_file(
                open3d_ifp, image_dp, image_relative_fp_list, image_fp_type, op
            )
        else:
            assert False

        log_report("INFO", "parse_open3d_file: Done", op)
        return cams

    @staticmethod
    def _create_dummy_fp_list(num_cameras):
        dummy_fp_list = ["img_" + str(i) for i in range(num_cameras)]
        return dummy_fp_list

    @staticmethod
    def _chunker(seq, size):
        return list(seq[pos : pos + size] for pos in range(0, len(seq), size))

    @staticmethod
    def _read_matrix_row(matrix_line):
        # split() without arguments splits at whitespaces and tabs
        matrix_list = matrix_line.split()
        matrix_row = list(map(float, matrix_list))
        return matrix_row

    @staticmethod
    def _parse_open3d_log_file(
        open3d_ifp, image_dp, image_relative_fp_list, image_fp_type, op
    ):
        cams = []
        with open(open3d_ifp, "r") as open3d_file:

            lines = open3d_file.readlines()
            # Chunk size: 1 line meta data, 4 lines for the matrix
            chunk_size = 5
            assert len(lines) % chunk_size == 0
            chunks = Open3DFileHandler._chunker(lines, chunk_size)

            if len(chunks) != len(image_relative_fp_list):
                # Create some dummy names for missing images
                image_relative_fp_list = (
                    Open3DFileHandler._create_dummy_fp_list(len(chunks))
                )

            for chunk, image_relative_fp in zip(
                chunks, image_relative_fp_list
            ):
                meta_data = chunk[0]

                matrix_list = [
                    Open3DFileHandler._read_matrix_row(chunk[1]),
                    Open3DFileHandler._read_matrix_row(chunk[2]),
                    Open3DFileHandler._read_matrix_row(chunk[3]),
                ]

                # Note: the transformation matrix in the .json file is the
                # inverse of the transformation matrix in the .log file
                extrinsic_matrix = np.asarray(matrix_list, dtype=float)

                cam = Camera()
                cam.image_fp_type = image_fp_type
                cam.image_dp = image_dp
                cam._relative_fp = image_relative_fp
                image_absolute_fp = os.path.join(image_dp, image_relative_fp)
                cam._absolute_fp = image_absolute_fp

                # Accuracy of rotation matrices is too low => disable test
                cam.set_4x4_cam_to_world_mat(
                    extrinsic_matrix, check_rotation=False
                )

                cams.append(cam)
        return cams

    @staticmethod
    def _parse_open3d_json_file(
        open3d_ifp, image_dp, image_relative_fp_list, image_fp_type, op
    ):
        cams = []

        with open(open3d_ifp, "r") as open3d_file:
            json_data = json.load(open3d_file)
            parameters = json_data["parameters"]

            if len(parameters) != len(image_relative_fp_list):
                # Create some dummy names for missing images
                image_relative_fp_list = (
                    Open3DFileHandler._create_dummy_fp_list(len(parameters))
                )

            for pinhole_camera_parameter, image_relative_fp in zip(
                parameters, image_relative_fp_list
            ):

                cam = Camera()
                cam.image_fp_type = image_fp_type
                cam.image_dp = image_dp
                cam._relative_fp = image_relative_fp
                cam._absolute_fp = os.path.join(image_dp, image_relative_fp)

                extrinsic = pinhole_camera_parameter["extrinsic"]
                # Note: the transformation matrix in the .json file is the inverse of
                #       the transformation matrix in the .log file
                extrinsic_mat = np.linalg.inv(
                    np.array(extrinsic, dtype=float).reshape((4, 4)).T
                )

                intrinsic = pinhole_camera_parameter["intrinsic"]

                cam.width = intrinsic["width"]
                cam.height = intrinsic["height"]

                # Accuracy of rotation matrices is too low => disable test
                cam.set_4x4_cam_to_world_mat(
                    extrinsic_mat, check_rotation=False
                )

                intrinsic = intrinsic["intrinsic_matrix"]
                intrinsic_mat = (
                    np.array(intrinsic, dtype=float).reshape((3, 3)).T
                )
                cam.set_calibration_mat(intrinsic_mat)

                cams.append(cam)
        return cams
