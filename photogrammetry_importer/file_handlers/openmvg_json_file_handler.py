import json
import numpy as np
import os

from photogrammetry_importer.types.camera import Camera
from photogrammetry_importer.types.point import Point
from photogrammetry_importer.file_handlers.utility import (
    check_radial_distortion,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report


class OpenMVGJSONFileHandler:
    """Class to read and write :code:`OpenMVG` files."""

    @staticmethod
    def _get_default_polymorphic_name(intrinsics):
        default_polymorpihc_name = None
        for _, intrinsic in intrinsics.items():
            if intrinsic["key"] == 0:
                default_polymorpihc_name = intrinsic["value"][
                    "polymorphic_name"
                ]
                break
        assert default_polymorpihc_name is not None
        return default_polymorpihc_name

    @staticmethod
    def _parse_cameras(
        json_data,
        image_dp,
        image_fp_type,
        suppress_distortion_warnings,
        op=None,
    ):

        # For each input image there exists an entry in "views". In contrast,
        # "extrinsics" contains only information of registered images (i.e.
        # reconstructed camera poses) and may contain only information for a
        # subset of images.
        views = {item["key"]: item for item in json_data["views"]}
        intrinsics = {item["key"]: item for item in json_data["intrinsics"]}
        extrinsics = {item["key"]: item for item in json_data["extrinsics"]}

        # Regard 3D stores the polymorhic attribute in the first intrinsic
        default_polymorphic_name = (
            OpenMVGJSONFileHandler._get_default_polymorphic_name(intrinsics)
        )

        cams = []
        # Iterate over views and create a camera if intrinsic and extrinsic
        # parameters exist
        for id, view in views.items():  # Iterate over views

            id_view = view["key"]
            # view["value"]["ptr_wrapper"]["data"] should be equal to
            # view["value"]["ptr_wrapper"]["data"]["id_view"]
            view_data = view["value"]["ptr_wrapper"]["data"]
            id_pose = view_data["id_pose"]
            id_intrinsic = view_data["id_intrinsic"]

            # Check if the view is having corresponding Pose and Intrinsic data
            if (
                id_pose in extrinsics.keys()
                and id_intrinsic in intrinsics.keys()
            ):

                camera = Camera()

                camera.image_fp_type = image_fp_type
                camera.image_dp = image_dp
                camera._relative_fp = os.path.join(
                    view_data["local_path"], view_data["filename"]
                )
                camera._absolute_fp = os.path.join(
                    json_data["root_path"],
                    view_data["local_path"],
                    view_data["filename"],
                )
                camera.width = view_data["width"]
                camera.height = view_data["height"]
                id_intrinsic = view_data["id_intrinsic"]

                # Handle intrinsic params
                intrinsic_values = intrinsics[int(id_intrinsic)]["value"]
                intrinsic_data = intrinsic_values["ptr_wrapper"]["data"]

                if "polymorphic_name" in intrinsic_values:
                    polymorphic_name = intrinsic_values["polymorphic_name"]
                else:
                    polymorphic_name = default_polymorphic_name
                    log_report(
                        "WARNING",
                        "Key polymorphic_name in intrinsic with id "
                        + str(id_intrinsic)
                        + " is missing, substituting with polymorphic_name of"
                        + " first intrinsic.",
                        op,
                    )

                if polymorphic_name == "spherical":
                    camera.set_panoramic_type(
                        Camera.panoramic_type_equirectangular
                    )
                    # create some dummy values
                    focal_length = 1
                    cx = camera.width / 2
                    cy = camera.height / 2
                else:

                    focal_length = intrinsic_data["focal_length"]
                    principal_point = intrinsic_data["principal_point"]
                    cx = principal_point[0]
                    cy = principal_point[1]

                # For Radial there are several options:
                # "None", disto_k1, disto_k3
                if "disto_k3" in intrinsic_data:
                    radial_distortion = [
                        float(intrinsic_data["disto_k3"][0]),
                        float(intrinsic_data["disto_k3"][1]),
                        float(intrinsic_data["disto_k3"][2]),
                    ]
                elif "disto_k1" in intrinsic_data:
                    radial_distortion = float(intrinsic_data["disto_k1"][0])
                else:  # No radial distortion, i.e. pinhole camera model
                    radial_distortion = 0

                if not suppress_distortion_warnings:
                    check_radial_distortion(
                        radial_distortion, camera._relative_fp, op
                    )

                camera_calibration_matrix = np.array(
                    [[focal_length, 0, cx], [0, focal_length, cy], [0, 0, 1]]
                )

                camera.set_calibration(
                    camera_calibration_matrix, radial_distortion
                )
                extrinsic_params = extrinsics[id_pose]
                cam_rotation_list = extrinsic_params["value"]["rotation"]
                camera.set_rotation_with_rotation_mat(
                    np.array(cam_rotation_list, dtype=float)
                )
                camera.set_camera_center_after_rotation(
                    np.array(extrinsic_params["value"]["center"], dtype=float)
                )
                camera.view_index = id_view

                cams.append(camera)
        return cams

    @staticmethod
    def _parse_points(json_data, view_index_to_absolute_fp=None, op=None):

        # Note: Blender 3.1.2 comes with Python 3.10, which is compatible to
        #  Pillow >= 9.0 and Pillow 8.3.2 - 8.4.
        #  However:
        #   - When reading *.JPG images with Pillow >= 9.0 WITHIN Blender
        #     3.1.2, then Blender crashes.
        #   - When reading *.JPG images with Pillow 8.3.2 - 8.4 WITHIN Blender
        #     3.1.2, then only black pixels are returned.
        #  Thus, we drop color computation for now.
        #  Interestingly, reading PNG images works without any problems.
        #
        #  If you want to visualize the point cloud colors, you may use:
        #  https://openmvg.readthedocs.io/en/latest/software/SfM/ComputeSfM_DataColor/
        #  and import the corresponding *.ply file.

        points = []
        structure = json_data["structure"]
        for json_point in structure:
            r = g = b = 0
            custom_point = Point(
                coord=np.array(json_point["value"]["X"], dtype=float),
                color=np.array([r, g, b], dtype=int),
                id=int(json_point["key"]),
                scalars=[],
            )

            points.append(custom_point)
        return points

    @staticmethod
    def parse_openmvg_file(
        input_openMVG_file_path,
        image_dp,
        image_fp_type,
        suppress_distortion_warnings,
        op=None,
    ):
        """Parse an :code:`OpenMVG` (:code:`.json`) file."""

        log_report("INFO", "parse_openmvg_file: ...", op)
        log_report(
            "INFO", "input_openMVG_file_path: " + input_openMVG_file_path, op
        )
        input_file = open(input_openMVG_file_path, "r")
        json_data = json.load(input_file)

        cams = OpenMVGJSONFileHandler._parse_cameras(
            json_data,
            image_dp,
            image_fp_type,
            suppress_distortion_warnings,
            op,
        )
        view_index_to_absolute_fp = {
            cam.view_index: cam.get_absolute_fp() for cam in cams
        }
        points = OpenMVGJSONFileHandler._parse_points(
            json_data, view_index_to_absolute_fp, op
        )
        log_report("INFO", "parse_openmvg_file: Done", op)
        return cams, points
