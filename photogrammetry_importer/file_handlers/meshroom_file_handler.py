import json
import numpy as np
import os

from photogrammetry_importer.types.camera import Camera
from photogrammetry_importer.types.point import Point
from photogrammetry_importer.file_handlers.utility import (
    check_radial_distortion,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report


class MeshroomFileHandler:
    """Class to read and write :code:`Meshroom` files and workspaces."""

    # Note: *.SfM files are actually just *.JSON files.

    @staticmethod
    def _get_element(data_list, id_string, query_id):
        result = None
        for ele in data_list:
            if int(ele[id_string]) == query_id:
                result = ele
                break
        assert result is not None
        return result

    @classmethod
    def _parse_cameras_from_json_data(
        cls,
        json_data,
        image_dp,
        image_fp_type,
        suppress_distortion_warnings,
        op,
    ):

        cams = []
        image_index_to_camera_index = {}

        is_valid_file = (
            "views" in json_data
            and "intrinsics" in json_data
            and "poses" in json_data
        )

        if not is_valid_file:
            log_report(
                "ERROR",
                "FILE FORMAT ERROR: Incorrect SfM/JSON file. Must contain the"
                + " SfM reconstruction results: view, intrinsics and poses.",
                op,
            )
            return cams, image_index_to_camera_index

        alicevision_sfm_data_version = tuple(
            [int(val) for val in json_data["version"]]
        )

        views = json_data["views"]  # is a list of dicts (view)
        intrinsics = json_data["intrinsics"]  # is a list of dicts (intrinsic)
        extrinsics = json_data["poses"]  # is a list of dicts (extrinsic)

        # IMPORTANT:
        # Views contain the number of input images
        # Extrinsics may contain only a subset of views!
        # (Not all views are necessarily contained in the reconstruction)

        for rec_index, extrinsic in enumerate(extrinsics):

            camera = Camera()
            view_index = int(extrinsic["poseId"])
            image_index_to_camera_index[view_index] = rec_index

            corresponding_view = cls._get_element(views, "poseId", view_index)

            camera.image_fp_type = image_fp_type
            camera.image_dp = image_dp
            camera._absolute_fp = str(corresponding_view["path"])
            camera._relative_fp = os.path.basename(
                str(corresponding_view["path"])
            )
            camera._undistorted_relative_fp = str(extrinsic["poseId"]) + ".exr"
            if image_dp is None:
                camera._undistorted_absolute_fp = None
            else:
                camera._undistorted_absolute_fp = os.path.join(
                    image_dp, camera._undistorted_relative_fp
                )

            camera.width = int(corresponding_view["width"])
            camera.height = int(corresponding_view["height"])
            id_intrinsic = int(corresponding_view["intrinsicId"])

            intrinsic_params = cls._get_element(
                intrinsics, "intrinsicId", id_intrinsic
            )

            # https://github.com/alicevision/Meshroom/blob/develop/meshroom/nodes/aliceVision/CameraInit.py
            #
            # CameraInit.py Version 5.0
            #   https://github.com/alicevision/Meshroom/commit/5ab6ed8e5259d49b393dfa74197494b856dd082e
            #       - Aug 13, 2021
            #       - focal length is now split on x and y
            #       - sfmData version: None
            # CameraInit.py Version 6.0
            #   https://github.com/alicevision/Meshroom/commit/61308eb211472c772b2253ca4081f3d8060f3fab
            #       - Aug 19, 2021
            #       - sfmData version: 1.2.1
            #       - Principal Point is now relative to the image center
            #         (and not relative to the top-left image corner)
            # CameraInit.py Version 7.0
            #   https://github.com/alicevision/Meshroom/commit/655dad9959657301fe5e5cfd539b2d05c1f70a4d
            #       - Mar 25, 2022
            #       - sfmData version: 1.2.2
            #       - parameters use focal in mm
            # CameraInit.py Version 8.0
            #    https://github.com/alicevision/Meshroom/commit/95bb93b4bf7fdd54906ecf5f00279de4e78a62c4
            #       - Sep 15, 2022
            #       - sfmData version: 1.2.2
            #       - No semantic changes
            # CameraInit.py Version 9.0
            #   https://github.com/alicevision/Meshroom/commit/5b331fc13935a6630dd47aa66fccf6296069272f
            #       - Jan 22, 2023
            #       - sfmData version: 1.2.2
            #       - No semantic changes
            # CameraInit.py Version 9.0
            #   https://github.com/alicevision/Meshroom/commit/56f77e2d52f943006227644359a5c2f14180a3bf
            #       - Jun 28, 2023
            #       - sfmData version: 1.2.5
            #       - No semantic changes

            # https://github.com/alicevision/AliceVision/tree/develop/src/aliceVision/sfmDataIO/compatibilityData
            #   scene_v1.2.0.json
            #   scene_v1.2.1.json
            #   scene_v1.2.2.json
            #   scene_v1.2.3.json
            #   scene_v1.2.4.json

            if alicevision_sfm_data_version >= (1, 2, 6):
                raise NotImplementedError(
                    f"support for alicevision sfm data version: {alicevision_sfm_data_version}"
                )

            if alicevision_sfm_data_version >= (1, 2, 2):
                # Focal lenght in mm
                focal_length_x_mm = float(intrinsic_params["focalLength"])
                pixel_ratio = float(intrinsic_params["pixelRatio"])
                focal_length_y_mm = pixel_ratio * focal_length_x_mm

                width_px = float(intrinsic_params["width"])
                height_px = float(intrinsic_params["height"])
                width_mm = float(intrinsic_params["sensorWidth"])
                height_mm = float(intrinsic_params["sensorHeight"])

                focal_length_x_px = focal_length_x_mm / width_mm * width_px
                focal_length_y_px = focal_length_y_mm / height_mm * height_px
            elif alicevision_sfm_data_version >= (1, 2, 0):
                # Focal lenght x and y in pixel
                focal_length_x_px = float(intrinsic_params["pxFocalLength"][0])
                focal_length_y_px = float(intrinsic_params["pxFocalLength"][1])
            else:
                # Focal lenght in pixel
                focal_length_x_px = float(intrinsic_params["pxFocalLength"])
                focal_length_y_px = focal_length_x_px

            if alicevision_sfm_data_version >= (1, 2, 1):
                # Principal point (in pixel) relative to the image center
                width_px = float(intrinsic_params["width"])
                height_px = float(intrinsic_params["height"])
                cx_px_rel_to_center = float(
                    intrinsic_params["principalPoint"][0]
                )
                cy_px_rel_to_center = float(
                    intrinsic_params["principalPoint"][1]
                )
                cx_px = width_px / 2 + cx_px_rel_to_center
                cy_px = height_px / 2 + cy_px_rel_to_center
            else:
                # Principal point (in pixel) relative to the top-left image corner
                cx_px = float(intrinsic_params["principalPoint"][0])
                cy_px = float(intrinsic_params["principalPoint"][1])

            if (
                "distortionParams" in intrinsic_params
                and len(intrinsic_params["distortionParams"]) > 0
            ):
                # TODO proper handling of distortion parameters
                radial_distortion = float(
                    intrinsic_params["distortionParams"][0]
                )
            else:
                radial_distortion = 0.0

            if not suppress_distortion_warnings:
                check_radial_distortion(
                    radial_distortion, camera._relative_fp, op
                )

            camera_calibration_matrix = np.array(
                [
                    [focal_length_x_px, 0, cx_px],
                    [0, focal_length_y_px, cy_px],
                    [0, 0, 1],
                ]
            )

            camera.set_calibration(
                camera_calibration_matrix, radial_distortion
            )
            extrinsic_params = extrinsic["pose"]["transform"]

            cam_rotation_list = extrinsic_params["rotation"]
            camera.set_rotation_with_rotation_mat(
                np.array(cam_rotation_list, dtype=float).reshape(3, 3).T
            )
            camera.set_camera_center_after_rotation(
                np.array(extrinsic_params["center"], dtype=float)
            )
            camera.view_index = view_index

            cams.append(camera)
        return cams, image_index_to_camera_index

    @staticmethod
    def _parse_points_from_json_data(
        json_data, image_index_to_camera_index, op
    ):

        points = []
        is_valid_file = "structure" in json_data

        if not is_valid_file:
            log_report(
                "ERROR",
                "FILE FORMAT ERROR: Incorrect SfM/JSON file. Must contain "
                + " the SfM reconstruction results: structure.",
                op,
            )
            return points

        structure = json_data["structure"]
        for json_point in structure:
            custom_point = Point(
                coord=np.array(json_point["X"], dtype=float),
                color=np.array(json_point["color"], dtype=int),
                id=int(json_point["landmarkId"]),
                scalars=[],
            )
            points.append(custom_point)
        return points

    @classmethod
    def parse_meshroom_sfm_file(
        cls,
        sfm_ifp,
        image_idp,
        image_fp_type,
        suppress_distortion_warnings,
        op=None,
    ):
        """Parse a :code:`Meshroom` (:code:`.sfm` or :code:`.json`) file.

        Parse different file formats created with the
        :code:`StructureFromMotion` / :code:`ConvertSfMFormat` node in
        :code:`Meshroom`.
        """
        log_report("INFO", "parse_meshroom_sfm_file: ...", op)
        log_report("INFO", "sfm_ifp: " + sfm_ifp, op)
        input_file = open(sfm_ifp, "r")
        json_data = json.load(input_file)

        (
            cams,
            image_index_to_camera_index,
        ) = cls._parse_cameras_from_json_data(
            json_data,
            image_idp,
            image_fp_type,
            suppress_distortion_warnings,
            op,
        )
        if "structure" in json_data:
            points = cls._parse_points_from_json_data(
                json_data, image_index_to_camera_index, op
            )
        else:
            points = []
        log_report("INFO", "parse_meshroom_sfm_file: Done", op)
        return cams, points

    @staticmethod
    def _get_latest_node(json_graph, node_type):
        i = 0
        while node_type + "_" + str(i + 1) in json_graph:
            i = i + 1
        if i == 0:
            return None
        else:
            return json_graph[node_type + "_" + str(i)]

    @classmethod
    def _get_node(cls, json_graph, node_type, node_number, op):
        if node_number == -1:
            return cls._get_latest_node(json_graph, node_type)
        else:
            node_key = node_type + "_" + str(node_number)
            if node_key in json_graph:
                return json_graph[node_key]
            else:
                log_report(
                    "ERROR",
                    "Invalid combination of node type (i.e. "
                    + node_type
                    + ") "
                    + "and node number (i.e. "
                    + str(node_number)
                    + ") provided",
                    op,
                )
                assert False

    @staticmethod
    def _get_data_fp_of_node(cache_dp, data_node, fn_or_fn_list):
        if isinstance(fn_or_fn_list, str):
            fn_list = [fn_or_fn_list]
        else:
            fn_list = fn_or_fn_list
        if data_node is None:
            return None
        node_type = data_node["nodeType"]
        uid_0 = data_node["uids"]["0"]
        data_fp = None
        for fn in fn_list:
            possible_data_fp = os.path.join(cache_dp, node_type, uid_0, fn)
            if os.path.isfile(possible_data_fp):
                data_fp = possible_data_fp
                break
        return data_fp

    @classmethod
    def _get_node_data_fp(
        cls, cache_dp, json_graph, node_type, node_number, fn_or_fn_list, op
    ):
        data_node = cls._get_node(json_graph, node_type, node_number, op)
        data_fp = cls._get_data_fp_of_node(cache_dp, data_node, fn_or_fn_list)
        return data_fp

    @staticmethod
    def _get_data_dp_of_node(cache_dp, data_node):
        if data_node is None:
            return None
        node_type = data_node["nodeType"]
        uid_0 = data_node["uids"]["0"]
        return os.path.join(cache_dp, node_type, uid_0)

    @classmethod
    def _get_node_data_dp(
        cls, cache_dp, json_graph, node_type, node_number, op
    ):
        data_node = cls._get_node(json_graph, node_type, node_number, op)
        data_dp = cls._get_data_dp_of_node(cache_dp, data_node)
        return data_dp

    @classmethod
    def _get_sfm_fp(
        cls, sfm_node_type, cache_dp, json_graph, sfm_node_number, op
    ):
        if sfm_node_type == "ConvertSfMFormatNode":
            sfm_fp = cls._get_node_data_fp(
                cache_dp,
                json_graph,
                "ConvertSfMFormat",
                sfm_node_number,
                ["sfm.sfm", "sfm.json"],
                op,
            )
        elif sfm_node_type == "StructureFromMotionNode":
            sfm_fp = cls._get_node_data_fp(
                cache_dp,
                json_graph,
                "StructureFromMotion",
                sfm_node_number,
                "cameras.sfm",
                op,
            )
        elif sfm_node_type == "AUTOMATIC":
            sfm_fp = cls._get_node_data_fp(
                cache_dp,
                json_graph,
                "ConvertSfMFormat",
                sfm_node_number,
                ["sfm.sfm", "sfm.json"],
                op,
            )
            if sfm_fp is None:
                sfm_fp = cls._get_node_data_fp(
                    cache_dp,
                    json_graph,
                    "StructureFromMotion",
                    sfm_node_number,
                    "cameras.sfm",
                    op,
                )
        else:
            log_report("ERROR", "Selected SfM node is not supported", op)
            assert False
        return sfm_fp

    @classmethod
    def _get_mesh_fp(
        cls, mesh_node_type, cache_dp, json_graph, mesh_node_number, op
    ):
        if mesh_node_type == "Texturing":
            mesh_fp = cls._get_node_data_fp(
                cache_dp,
                json_graph,
                "Texturing",
                mesh_node_number,
                "texturedMesh.obj",
                op,
            )
        elif mesh_node_type == "MeshFiltering":
            mesh_fp = cls._get_node_data_fp(
                cache_dp,
                json_graph,
                "MeshFiltering",
                mesh_node_number,
                "mesh.obj",
                op,
            )
        elif mesh_node_type == "Meshing":
            mesh_fp = cls._get_node_data_fp(
                cache_dp,
                json_graph,
                "Meshing",
                mesh_node_number,
                "mesh.obj",
                op,
            )
        elif mesh_node_type == "AUTOMATIC":
            mesh_fp = cls._get_node_data_fp(
                cache_dp,
                json_graph,
                "Texturing",
                mesh_node_number,
                "texturedMesh.obj",
                op,
            )
            if mesh_fp is None:
                mesh_fp = cls._get_node_data_fp(
                    cache_dp,
                    json_graph,
                    "MeshFiltering",
                    mesh_node_number,
                    "mesh.obj",
                    op,
                )
            if mesh_fp is None:
                mesh_fp = cls._get_node_data_fp(
                    cache_dp,
                    json_graph,
                    "Meshing",
                    mesh_node_number,
                    "mesh.obj",
                    op,
                )
        else:
            log_report("ERROR", "Select Mesh node is not supported!", op)
            assert False
        return mesh_fp

    @classmethod
    def _get_image_dp(cls, cache_dp, json_graph, prepare_node_number, op):
        prepare_dp = cls._get_node_data_dp(
            cache_dp,
            json_graph,
            "PrepareDenseScene",
            prepare_node_number,
            op,
        )
        return prepare_dp

    @classmethod
    def parse_meshrom_mg_file(
        cls,
        mg_fp,
        sfm_node_type,
        sfm_node_number,
        mesh_node_type,
        mesh_node_number,
        prepare_node_number,
        op=None,
    ):
        """Parse a :code:`Meshroom` project file (:code:`.mg`)."""

        cache_dp = os.path.join(os.path.dirname(mg_fp), "MeshroomCache")
        json_data = json.load(open(mg_fp, "r"))
        json_graph = json_data["graph"]

        sfm_fp = cls._get_sfm_fp(
            sfm_node_type, cache_dp, json_graph, sfm_node_number, op
        )

        mesh_fp = cls._get_mesh_fp(
            mesh_node_type, cache_dp, json_graph, mesh_node_number, op
        )

        image_dp = cls._get_image_dp(
            cache_dp, json_graph, prepare_node_number, op
        )

        if sfm_fp is not None:
            log_report("INFO", "Found the following sfm file: " + sfm_fp, op)
        else:
            log_report(
                "INFO",
                "Requested target SfM result does not exist in this meshroom"
                " project.",
                op,
            )

        if mesh_fp is not None:
            log_report("INFO", "Found the following mesh file: " + mesh_fp, op)
        else:
            log_report(
                "INFO",
                "Request target mesh does not exist in this meshroom project.",
                op,
            )

        return sfm_fp, mesh_fp, image_dp

    @classmethod
    def parse_meshroom_file(
        cls,
        meshroom_ifp,
        use_workspace_images,
        image_dp,
        image_fp_type,
        suppress_distortion_warnings,
        sfm_node_type,
        sfm_node_number,
        mesh_node_type,
        mesh_node_number,
        prepare_node_number,
        op=None,
    ):
        """Parse a :code:`Meshroom` file.

        Supported file formats are :code:`.mg`, :code:`.sfm` or :code:`.json`.
        """
        log_report("INFO", "parse_meshroom_file: ...", op)
        log_report("INFO", "meshroom_ifp: " + meshroom_ifp, op)

        ext = os.path.splitext(meshroom_ifp)[1].lower()
        if ext == ".mg":
            (
                meshroom_ifp,
                mesh_fp,
                image_idp_workspace,
            ) = cls.parse_meshrom_mg_file(
                meshroom_ifp,
                sfm_node_type,
                sfm_node_number,
                mesh_node_type,
                mesh_node_number,
                prepare_node_number,
                op,
            )
            if (
                use_workspace_images
                and image_idp_workspace is not None
                and os.path.isdir(image_idp_workspace)
            ):
                image_dp = image_idp_workspace
                log_report("INFO", "Using image directory in workspace.", op)
        else:
            assert ext == ".json" or ext == ".sfm"
            mesh_fp = None

        if meshroom_ifp is not None:
            cams, points = cls.parse_meshroom_sfm_file(
                meshroom_ifp,
                image_dp,
                image_fp_type,
                suppress_distortion_warnings,
                op,
            )
        else:
            log_report(
                "WARNING",
                "Meshroom project does not contain cameras or points. Have"
                " you saved the project (i.e. the *.mg file)?",
                op,
            )
            cams = []
            points = []

        log_report("INFO", "parse_meshroom_file: Done", op)
        return cams, points, mesh_fp, image_dp
