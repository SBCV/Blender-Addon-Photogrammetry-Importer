import json
import numpy as np
import os

from photogrammetry_importer.types.camera import Camera
from photogrammetry_importer.types.point import Point
from photogrammetry_importer.utility.blender_camera_utility import (
    check_radial_distortion,
)
from photogrammetry_importer.utility.blender_logging_utility import log_report


class OpenMVGJSONFileHandler:
    @staticmethod
    def get_default_polymorphic_name(intrinsics):
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
    def parse_cameras(
        json_data, image_dp, image_fp_type, suppress_distortion_warnings, op
    ):

        views = {item["key"]: item for item in json_data["views"]}
        intrinsics = {item["key"]: item for item in json_data["intrinsics"]}
        extrinsics = {item["key"]: item for item in json_data["extrinsics"]}

        # Regard 3D stores the polymorhic attribute in the first intrinsic
        default_polymorphic_name = (
            OpenMVGJSONFileHandler.get_default_polymorphic_name(intrinsics)
        )

        # IMPORTANT:
        # Views contain the description about the dataset and attribute to Pose and Intrinsic data.
        # View -> id_pose, id_intrinsic
        # Since sometimes some views cannot be localized, there is some missing pose and intrinsic data.
        # Extrinsics may contain only a subset of views! (Potentially not all views are contained in the reconstruction)

        cams = []
        # Iterate over views, and create camera if Intrinsic and Pose data exist
        for id, view in views.items():  # Iterate over views

            id_view = view[
                "key"
            ]  # Should be equal to view['value']['ptr_wrapper']['data']['id_view']
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

                # handle intrinsic params
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
                        + " is missing, substituting with polymorphic_name of first intrinsic.",
                        op,
                    )

                if polymorphic_name == "spherical":
                    camera.set_panoramic_type(
                        Camera.panoramic_type_equirectangular
                    )
                    # create some dummy values
                    focal_length = 0
                    cx = camera.width / 2
                    cy = camera.height / 2
                else:

                    focal_length = intrinsic_data["focal_length"]
                    principal_point = intrinsic_data["principal_point"]
                    cx = principal_point[0]
                    cy = principal_point[1]

                # For Radial there are several options: "None", disto_k1, disto_k3
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
                camera.set_rotation_mat(
                    np.array(cam_rotation_list, dtype=float)
                )
                camera.set_camera_center_after_rotation(
                    np.array(extrinsic_params["value"]["center"], dtype=float)
                )
                camera.view_index = id_view

                cams.append(camera)
        return cams

    @staticmethod
    def parse_points(json_data, view_index_to_absolute_fp=None, op=None):

        compute_color = True
        try:
            from PIL import Image, ImageFile

            ImageFile.LOAD_TRUNCATED_IMAGES = True
        except ImportError:
            log_report(
                "WARNING",
                "Can not compute point cloud color information, since Pillow is not installed.",
                op,
            )
            compute_color = False

        if view_index_to_absolute_fp is None:
            log_report(
                "WARNING",
                "Can not compute point cloud color information, since path to images is not correctly set.",
                op,
            )
            compute_color = False

        if compute_color:
            log_report(
                "INFO",
                "Try to collect color information from files (this might take a while)",
                op,
            )
            view_index_to_image = {}
            for view_index, absolute_fp in view_index_to_absolute_fp.items():
                if os.path.isfile(absolute_fp):
                    pil_image = Image.open(absolute_fp)
                    view_index_to_image[view_index] = pil_image
                else:
                    log_report(
                        "WARNING",
                        "Can not compute point cloud color information, since image file path is incorrect.",
                        op,
                    )
                    compute_color = False
                    break

        if compute_color:
            log_report(
                "INFO",
                "Compute color information from files (this might take a while)",
                op,
            )

        points = []
        structure = json_data["structure"]
        for json_point in structure:

            r = g = b = 0

            # color information can only be computed if input files are provided
            if compute_color:
                for observation in json_point["value"]["observations"]:
                    view_index = int(observation["key"])

                    # REMARK: The order of ndarray.shape (first height, then width) is complimentary to
                    # pils image.size (first width, then height).
                    # That means
                    # height, width = segmentation_as_matrix.shape
                    # width, height = image.size

                    # Therefore: x_in_openmvg_file == x_image == y_ndarray
                    # and y_in_openmvg_file == y_image == x_ndarray
                    x_in_json_file = float(
                        observation["value"]["x"][0]
                    )  # x has index 0
                    y_in_json_file = float(
                        observation["value"]["x"][1]
                    )  # y has index 1

                    current_image = view_index_to_image[view_index]
                    current_r, current_g, current_b = current_image.getpixel(
                        (x_in_json_file, y_in_json_file)
                    )
                    r += current_r
                    g += current_g
                    b += current_b

                # normalize the rgb values
                amount_observations = len(json_point["value"]["observations"])
                r /= amount_observations
                g /= amount_observations
                b /= amount_observations

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
        op,
    ):
        """
        The path_to_input_files parameter is optional, if provided the returned points carry also color information
        :param input_openMVG_file_path:
        :param path_to_images: Path to the input images (used to infer the color of the structural points)
        :return:
        """
        log_report("INFO", "parse_openmvg_file: ...", op)
        log_report(
            "INFO", "input_openMVG_file_path: " + input_openMVG_file_path, op
        )
        input_file = open(input_openMVG_file_path, "r")
        json_data = json.load(input_file)

        cams = OpenMVGJSONFileHandler.parse_cameras(
            json_data,
            image_dp,
            image_fp_type,
            suppress_distortion_warnings,
            op,
        )
        view_index_to_absolute_fp = {
            cam.view_index: cam.get_absolute_fp() for cam in cams
        }
        points = OpenMVGJSONFileHandler.parse_points(
            json_data, view_index_to_absolute_fp, op
        )
        log_report("INFO", "parse_openmvg_file: Done", op)
        return cams, points
