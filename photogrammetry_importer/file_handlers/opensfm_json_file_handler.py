import json
import numpy as np
import os
import math
import sys

from photogrammetry_importer.types.camera import Camera
from photogrammetry_importer.types.point import Point
from photogrammetry_importer.file_handlers.utility import (
    check_radial_distortion,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report


class OpenSfMJSONFileHandler:
    """Class to read and write :code:`OpenSfM` files."""

    @staticmethod
    def _convert_intrinsics(
        json_camera_intrinsics, relative_fp, suppress_distortion_warnings, op
    ):

        # See https://www.opensfm.org/docs/_modules/opensfm/types.html

        height = json_camera_intrinsics["height"]
        width = json_camera_intrinsics["width"]

        radial_distortion = [
            json_camera_intrinsics["k1"],
            json_camera_intrinsics["k2"],
        ]
        projection_type = json_camera_intrinsics["projection_type"]

        if projection_type == "perspective":
            focal_length = json_camera_intrinsics["focal"] * max(width, height)
            cx = width / 2
            cy = height / 2
            log_report(
                "WARNING",
                "Principal point not provided, setting it to the image"
                + " center.",
                op,
            )
        elif projection_type == "brown":
            fx = json_camera_intrinsics["focal_x"] * max(width, height)
            fy = json_camera_intrinsics["focal_y"] * max(width, height)
            if fx != fy:
                log_report(
                    "WARNING",
                    "Focal length in x and y direction differs, setting it"
                    + " to the average value.",
                    op,
                )
            focal_length = (fx + fy) * 0.5
            cx = json_camera_intrinsics["c_x"]
            cy = json_camera_intrinsics["c_y"]
        else:
            log_report("ERROR", "Projection Type not supported!", op)
            assert False

        if not suppress_distortion_warnings:
            check_radial_distortion(radial_distortion, relative_fp, op)

        return [focal_length, cx, cy, width, height, radial_distortion]

    @staticmethod
    def _rodrigues_to_matrix(rodrigues_vec):
        # https://docs.opencv.org/4.2.0/d9/d0c/group__calib3d.html#ga61585db663d9da06b68e70cfbf6a1eac
        #   Check the formulas under Rodrigues()
        # https://github.com/opencv/opencv/blob/master/modules/calib3d/src/calibration.cpp
        #   Check the definition of cvRodrigues2()
        # http://www.cplusplus.com/reference/cfloat/
        #   See the defintion of DBL_EPSILON

        theta = np.linalg.norm(rodrigues_vec)
        if (
            theta < sys.float_info.epsilon
        ):  # For most systems: theta < 2.220446049250313e-16
            rot_mat = np.eye(3, dtype=float)
        else:
            r = rodrigues_vec / theta
            I = np.eye(3, dtype=float)
            r_rT = np.array(
                [
                    [r[0] * r[0], r[0] * r[1], r[0] * r[2]],
                    [r[1] * r[0], r[1] * r[1], r[1] * r[2]],
                    [r[2] * r[0], r[2] * r[1], r[2] * r[2]],
                ]
            )
            r_cross = np.array(
                [[0, -r[2], r[1]], [r[2], 0, -r[0]], [-r[1], r[0], 0]]
            )
            rot_mat = (
                math.cos(theta) * I
                + (1 - math.cos(theta)) * r_rT
                + math.sin(theta) * r_cross
            )
        return rot_mat

    @staticmethod
    def _parse_cameras(
        json_data, image_dp, image_fp_type, suppress_distortion_warnings, op
    ):

        json_cameras_intrinsics = json_data["cameras"]
        views = json_data["shots"]

        cams = []
        for view_name in views:
            view = views[view_name]

            camera = Camera()
            camera.image_fp_type = image_fp_type
            camera.image_dp = image_dp
            camera._relative_fp = view_name
            camera._absolute_fp = os.path.join(image_dp, view_name)

            intrinsic_key = view["camera"]
            (
                focal_length,
                cx,
                cy,
                width,
                height,
                radial_distortion,
            ) = OpenSfMJSONFileHandler._convert_intrinsics(
                json_cameras_intrinsics[intrinsic_key],
                camera._relative_fp,
                suppress_distortion_warnings,
                op,
            )
            camera.height = height
            camera.width = width
            camera_calibration_matrix = np.array(
                [[focal_length, 0, cx], [0, focal_length, cy], [0, 0, 1]]
            )
            camera.set_calibration(
                camera_calibration_matrix, radial_distortion
            )

            rodrigues_vec = np.array(view["rotation"], dtype=float)
            rot_mat = OpenSfMJSONFileHandler._rodrigues_to_matrix(
                rodrigues_vec
            )
            camera.set_rotation_with_rotation_mat(rot_mat)
            camera.set_camera_translation_vector_after_rotation(
                np.array(view["translation"], dtype=float)
            )

            cams.append(camera)
        return cams

    @staticmethod
    def _parse_points(json_data, op):
        points = []
        json_points = json_data["points"]
        for point_id in json_points:
            json_point = json_points[point_id]
            custom_point = Point(
                coord=np.array(json_point["coordinates"], dtype=float),
                color=np.array(json_point["color"], dtype=int),
                id=point_id,
                scalars=[],
            )
            points.append(custom_point)
        return points

    @staticmethod
    def parse_opensfm_file(
        input_opensfm_fp,
        image_dp,
        image_fp_type,
        reconstruction_idx,
        suppress_distortion_warnings=False,
        op=None,
    ):
        """Parse a :code:`OpenSfM` (:code:`.json`) file."""

        log_report("INFO", "parse_opensfm_file: ...", op)
        log_report("INFO", "input_opensfm_fp: " + input_opensfm_fp, op)
        input_file = open(input_opensfm_fp, "r")
        json_data = json.load(input_file)
        reconstruction_data = json_data[reconstruction_idx]
        if len(json_data) > 1:
            log_report(
                "WARNING",
                "OpenSfM file contains multiple reconstructions. Only "
                + f" reconstruction with index {reconstruction_idx} is"
                + " imported.",
                op,
            )

        cams = OpenSfMJSONFileHandler._parse_cameras(
            reconstruction_data,
            image_dp,
            image_fp_type,
            suppress_distortion_warnings,
            op,
        )
        points = OpenSfMJSONFileHandler._parse_points(reconstruction_data, op)
        log_report("INFO", "parse_opensfm_file: Done", op)
        return cams, points
