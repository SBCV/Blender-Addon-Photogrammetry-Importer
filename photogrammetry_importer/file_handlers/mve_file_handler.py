import os
import numpy as np
import configparser
import math
import struct

from photogrammetry_importer.file_handlers.image_file_handler import (
    ImageFileHandler,
)
from photogrammetry_importer.utility.os_utility import get_subdirs
from photogrammetry_importer.file_handlers.utility import (
    check_radial_distortion,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report
from photogrammetry_importer.types.camera import Camera
from photogrammetry_importer.types.point import Point


class MVEFileHandler:
    """Class to read and write :code:`MVE` workspaces."""

    @staticmethod
    def _str_to_arr(some_str, target_type):
        return [target_type(x) for x in some_str.split()]

    @staticmethod
    def _readline_as_numbers(input_file, target_type):
        line_str = input_file.readline().rstrip()
        return MVEFileHandler._str_to_arr(line_str, target_type)

    @staticmethod
    def _parse_rotation_matrix(input_file):
        row_1 = MVEFileHandler._readline_as_numbers(
            input_file, target_type=float
        )
        row_2 = MVEFileHandler._readline_as_numbers(
            input_file, target_type=float
        )
        row_3 = MVEFileHandler._readline_as_numbers(
            input_file, target_type=float
        )
        return np.asarray([row_1, row_2, row_3], dtype=float)

    @staticmethod
    def parse_synth_out(synth_out_ifp):
        """Parse the :code:`synth_0.out` file in the :code:`MVE` workspace."""
        points3D = []

        with open(synth_out_ifp, "r") as input_file:
            meta_data_line = input_file.readline()

            num_cameras, num_points = MVEFileHandler._readline_as_numbers(
                input_file, target_type=int
            )

            # The camera information provided in the synth_0.out file is incomplete
            # Thus, we use the camera information provided in the view folders

            # Consume the lines corresponding to the (incomplete) camera information
            for cam_idx in range(num_cameras):
                intrinsic_line = MVEFileHandler._readline_as_numbers(
                    input_file, target_type=float
                )
                rotation_mat = MVEFileHandler._parse_rotation_matrix(
                    input_file
                )
                camera_translation = np.asarray(
                    MVEFileHandler._readline_as_numbers(
                        input_file, target_type=float
                    )
                )

            for point_idx in range(num_points):
                coord = MVEFileHandler._readline_as_numbers(
                    input_file, target_type=float
                )
                color = MVEFileHandler._readline_as_numbers(
                    input_file, target_type=int
                )
                measurement_line = MVEFileHandler._readline_as_numbers(
                    input_file, target_type=int
                )
                point = Point(
                    coord=coord, color=color, id=point_idx, scalars=[]
                )
                points3D.append(point)

        return points3D

    @staticmethod
    def parse_meta(meta_ifp, width, height, camera_name, op):
        """Parse a :code:`meta.ini` file in the :code:`MVE` workspace."""
        view_specific_dir = os.path.dirname(meta_ifp)
        relative_image_fp = os.path.join(view_specific_dir, "undistorted.png")
        image_dp = os.path.dirname(view_specific_dir)

        camera = Camera()
        camera.image_fp_type = Camera.IMAGE_FP_TYPE_RELATIVE
        camera.image_dp = image_dp
        camera._relative_fp = relative_image_fp
        camera._absolute_fp = os.path.join(image_dp, relative_image_fp)
        camera._undistorted_relative_fp = camera._relative_fp
        camera._undistorted_absolute_fp = camera._absolute_fp

        camera.width = width
        camera.height = height

        ini_config = configparser.RawConfigParser()
        ini_config.read(meta_ifp)
        focal_length_normalized = float(
            ini_config.get(section="camera", option="focal_length")
        )
        pixel_aspect = float(
            ini_config.get(section="camera", option="pixel_aspect")
        )
        if pixel_aspect != 1.0:
            log_report(
                "WARNING",
                "Focal length differs in x and y direction,"
                + " setting it to the average value.",
                op,
            )
            focal_length_normalized = (
                focal_length_normalized
                + focal_length_normalized * pixel_aspect
            ) / 2

        max_extend = max(width, height)
        focal_length = focal_length_normalized * max_extend

        principal_point_str = ini_config.get(
            section="camera", option="principal_point"
        )
        principal_point_list = MVEFileHandler._str_to_arr(
            principal_point_str, target_type=float
        )
        cx_normalized = principal_point_list[0]
        cy_normalized = principal_point_list[1]
        cx = cx_normalized * width
        cy = cy_normalized * height

        calib_mat = Camera.compute_calibration_mat(focal_length, cx, cy)
        camera.set_calibration_mat(calib_mat)

        radial_distortion_str = ini_config.get(
            section="camera", option="radial_distortion"
        )
        radial_distortion_vec = np.asarray(
            MVEFileHandler._str_to_arr(
                radial_distortion_str, target_type=float
            )
        )
        check_radial_distortion(radial_distortion_vec, relative_image_fp, op)

        rotation_str = ini_config.get(section="camera", option="rotation")
        rotation_mat = np.asarray(
            MVEFileHandler._str_to_arr(rotation_str, target_type=float)
        ).reshape((3, 3))

        translation_str = ini_config.get(
            section="camera", option="translation"
        )
        translation_vec = np.asarray(
            MVEFileHandler._str_to_arr(translation_str, target_type=float)
        )

        camera.set_rotation_with_rotation_mat(rotation_mat)
        camera.set_camera_translation_vector_after_rotation(translation_vec)
        return camera

    @staticmethod
    def parse_views(
        views_idp,
        default_width,
        default_height,
        add_depth_maps_as_point_cloud,
        op=None,
    ):
        """Parse the :code:`views` directory in the :code:`MVE` workspace."""
        cameras = []
        subdirs = get_subdirs(views_idp)
        for subdir in subdirs:
            folder_name = os.path.basename(subdir)
            # folder_name = view_0000.mve
            camera_name = folder_name.split("_")[1].split(".")[0]
            undistorted_img_ifp = os.path.join(subdir, "undistorted.png")
            success, width, height = ImageFileHandler.read_image_size(
                undistorted_img_ifp,
                default_width=default_width,
                default_height=default_height,
                op=op,
            )
            assert success

            meta_ifp = os.path.join(subdir, "meta.ini")
            camera = MVEFileHandler.parse_meta(
                meta_ifp, width, height, camera_name, op
            )

            if add_depth_maps_as_point_cloud:
                for level in range(9):
                    depth_ifp = os.path.join(
                        subdir, "depth-L" + str(level) + ".mvei"
                    )
                    if os.path.isfile(depth_ifp):
                        camera.set_depth_map_callback(
                            MVEFileHandler.read_depth_map,
                            depth_ifp,
                            Camera.DEPTH_MAP_WRT_UNIT_VECTORS,
                            shift_depth_map_to_pixel_center=True,
                        )
                        break
                if camera.get_depth_map_fp() is None:
                    log_report(
                        "WARNING", "No depth map found in " + subdir, op
                    )

            cameras.append(camera)
        return cameras

    @staticmethod
    def parse_mve_workspace(
        workspace_idp,
        default_width,
        default_height,
        add_depth_maps_as_point_cloud,
        suppress_distortion_warnings,
        op=None,
    ):
        """Parse a :code:`MVE` workspace. """
        log_report("INFO", "Parse MVE workspace: ...", op)
        log_report("INFO", workspace_idp, op)
        views_idp = os.path.join(workspace_idp, "views")
        synth_ifp = os.path.join(workspace_idp, "synth_0.out")
        cameras = MVEFileHandler.parse_views(
            views_idp,
            default_width,
            default_height,
            add_depth_maps_as_point_cloud,
            op,
        )
        points3D = MVEFileHandler.parse_synth_out(synth_ifp)
        log_report("INFO", "Parse MVE workspace: Done", op)
        return cameras, points3D

    @staticmethod
    def _read_next_bytes(
        fid, num_bytes, format_char_sequence, endian_character="<"
    ):
        """Read and unpack the next bytes from a binary file.
        :param num_bytes: Sum of combination of {2, 4, 8}, e.g. 2, 6, 16, etc.
        :param format_char_sequence: List of {c, e, f, d, h, H, i, I, ...}.
        :param endian_character: Any of {@, =, <, >, !}
        :return: Tuple of read and unpacked values.
        """
        data = fid.read(num_bytes)
        return struct.unpack(endian_character + format_char_sequence, data)

    @staticmethod
    def read_depth_map(depth_map_ifp):
        """Read a depth map. """
        # See:
        # https://github.com/simonfuhrmann/mve/wiki/MVE-File-Format#the-mvei-image-format
        # https://github.com/simonfuhrmann/mve/blob/master/libs/mve/image_io.cc

        with open(depth_map_ifp, "rb") as fid:
            mvei_file_signature = MVEFileHandler._read_next_bytes(
                fid, 11, "ccccccccccc"
            )
            width = MVEFileHandler._read_next_bytes(fid, 4, "i")[0]
            height = MVEFileHandler._read_next_bytes(fid, 4, "i")[0]
            channels = MVEFileHandler._read_next_bytes(fid, 4, "i")[0]
            assert channels == 1
            raw_type = MVEFileHandler._read_next_bytes(fid, 4, "i")[0]
            assert raw_type == 9  # IMAGE_TYPE_FLOAT
            num_elements = width * height * channels
            data = np.asarray(
                MVEFileHandler._read_next_bytes(
                    fid, num_elements * 4, "f" * num_elements
                )
            )
            return data.reshape((height, width))
