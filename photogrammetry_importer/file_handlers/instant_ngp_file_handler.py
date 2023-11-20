import json
import os
import math
import numpy as np

from photogrammetry_importer.types.camera import Camera
from photogrammetry_importer.file_handlers.utility import (
    check_radial_distortion,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report
from photogrammetry_importer.importers.camera_utility import (
    invert_y_and_z_axis,
)


class InstantNGPFileHandler:
    """Class to read and write :code:`Instant-NGP` json files."""

    @classmethod
    def parse_instant_ngp_json_file(
        cls,
        json_ifp,
        image_dp,
        image_fp_type,
        suppress_distortion_warnings=False,
        op=None,
    ):
        """Parse a :code:`Instant-NGP` json file."""
        log_report("INFO", f"Parse Instant-NGP json file: {json_ifp}", op)
        log_report("INFO", f"image_dp: {image_dp}", op)

        cams = []

        input_file = open(json_ifp, "r")
        json_data = json.load(input_file)
        frames = json_data["frames"]
        for frame in frames:
            camera = Camera()
            camera.image_fp_type = image_fp_type
            camera.image_dp = image_dp

            relative_image_ifp = frame["file_path"]
            len_relative_image_ifp = len(relative_image_ifp.split(os.path.sep))
            if len_relative_image_ifp > 1:
                msg = "Nested relative image paths are currently not supported"
                msg += " going to extract only the file name"
                log_report("WARNING", msg, op)
            image_fn = os.path.basename(relative_image_ifp)
            camera._relative_fp = image_fn
            camera._absolute_fp = os.path.join(image_dp, image_fn)

            camera.width = int(json_data["w"])
            camera.height = int(json_data["h"])

            camera_angle_x = json_data["camera_angle_x"]
            camera_angle_y = json_data["camera_angle_y"]
            fl_x = json_data["fl_x"]
            fl_y = json_data["fl_y"]
            assert camera_angle_x == math.atan(camera.width / (fl_x * 2)) * 2
            assert camera_angle_y == math.atan(camera.height / (fl_y * 2)) * 2

            if not suppress_distortion_warnings:
                radial_distortion = None
                radial_parameters = ["k1", "k2", "k3", "k4", "p1", "p2"]
                for radial_parameter in radial_parameters:
                    if radial_parameter in json_data:
                        radial_value = json_data[radial_parameter]
                        if radial_distortion is None:
                            radial_distortion = [radial_value]
                        else:
                            radial_distortion.append(radial_value)
                    check_radial_distortion(
                        radial_distortion, camera._relative_fp, op
                    )

            cx = json_data["cx"]
            cy = json_data["cy"]

            camera_calibration_mat = np.array(
                [[fl_x, 0, cx], [0, fl_y, cy], [0, 0, 1]]
            )
            camera.set_calibration_mat(camera_calibration_mat)

            camera_to_world_mat_list = frame["transform_matrix"]
            camera_to_world_mat = np.asarray(camera_to_world_mat_list)

            # camera_to_world_mat = [R^T    c]
            #                       [0      1]
            rotation_mat = camera_to_world_mat[0:3, 0:3].transpose()
            camera_center_vec = camera_to_world_mat[0:3, 3]

            # Instant-NGP uses a camera coordinate system common in computer
            #  graphics (such as used by blender). However, the addon expects
            #  camera coordinate systems in common computer vision notation.
            #
            # In Instant-NGP the y axis in the image is pointing downwards (not
            #  upwards) and the camera is looking along the positive z axis
            #  (points in front of the camera show a positive z value).
            #
            # The conversion of camera coordinate systems in computer graphic
            #  notation to computer vision notiation is defined by a rotation
            #  of x axis around 180 degrees, i.e. an inversion of the y and z
            #  axis of the CAMERA MATRICES.
            #
            # Thus, in the case of a world to camera matrix
            #  world_to_camera_mat = [R      -Rc]
            #                        [0      1  ]
            #  the y and z axis of the TRANSLATION VECTOR t=-Rc must also be
            #  inverted.
            rotation_mat = invert_y_and_z_axis(rotation_mat)

            # Set camera rotation and center according to
            #  camera.set_4x4_cam_to_world_mat(cam_to_world_mat)
            camera.set_rotation_with_rotation_mat(
                rotation_mat,
                check_rotation=True,
            )
            camera.set_camera_center_after_rotation(
                camera_center_vec, check_rotation=True
            )

            cams.append(camera)

        return cams

    @staticmethod
    def _ensure_consistent_values(cameras):
        for cam_1, cam_2 in zip(cameras, cameras[1:]):
            assert cam_1.width == cam_2.width
            assert cam_1.height == cam_2.height

    @classmethod
    def write_instant_ngp_file(cls, ofp, cameras, op=None):
        """Write cameras and points as :code:`Instant-NGP` json file."""
        log_report("INFO", f"Write Instant-NGP json file: {ofp}", op)

        cls._ensure_consistent_values(cameras)
        reference_camera = cameras[0]
        cx, cy = reference_camera.get_principal_point()
        focal_length = reference_camera.get_focal_length()
        width = float(reference_camera.width)
        height = float(reference_camera.height)
        fl_x = focal_length
        fl_y = focal_length
        camera_angle_x = math.atan(width / (fl_x * 2)) * 2
        camera_angle_y = math.atan(height / (fl_y * 2)) * 2

        json_data = {
            "camera_angle_x": camera_angle_x,
            "camera_angle_y": camera_angle_y,
            "fl_x": fl_x,
            "fl_y": fl_y,
            "cx": cx,
            "cy": cy,
            "w": width,
            "h": height,
        }

        json_frames = []
        for camera in cameras:
            blender_name = camera.get_relative_fp()
            blender_stem = blender_name.split("_")[0]
            instant_fn = os.path.join("images", f"{blender_stem}.jpg")

            rotation_mat = camera.get_rotation_as_rotation_mat()
            camera_center_vec = camera.get_camera_center()

            # As stated in self.parse_instant_ngp_json_file() it is necessary
            # to convert the camera coordinate system from computer vision to
            # computer graphics convention, i.e. inverting the y and z axis
            # of the rotation matrix.
            rotation_mat = invert_y_and_z_axis(rotation_mat)

            # camera_to_world_mat = [R^T    c]
            #                       [0      1]
            camera_to_world_mat = np.identity(4, dtype=float)
            camera_to_world_mat[0:3, 0:3] = rotation_mat.transpose()
            camera_to_world_mat[0:3, 3] = camera_center_vec

            camera_to_world_list = camera_to_world_mat.tolist()
            json_frame = {
                "file_path": instant_fn,
                "transform_matrix": camera_to_world_list,
            }

            json_frames.append(json_frame)
        json_data["frames"] = json_frames

        with open(ofp, "w") as f:
            json.dump(json_data, f, indent=4)
