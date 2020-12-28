import os
import numpy as np

from photogrammetry_importer.ext.read_dense import read_array
from photogrammetry_importer.ext.read_write_model import (
    read_model,
    write_model,
    Camera as ColmapCamera,
    Image as ColmapImage,
    Point3D as ColmapPoint3D,
)

from photogrammetry_importer.types.camera import Camera
from photogrammetry_importer.types.point import Point
from photogrammetry_importer.file_handlers.utility import (
    check_radial_distortion,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report

# From photogrammetry_importer\ext\read_write_model.py
# CAMERA_MODELS = {
#     CameraModel(model_id=0, model_name="SIMPLE_PINHOLE", num_params=3),
#     CameraModel(model_id=1, model_name="PINHOLE", num_params=4),
#     CameraModel(model_id=2, model_name="SIMPLE_RADIAL", num_params=4),
#     CameraModel(model_id=3, model_name="RADIAL", num_params=5),
#     CameraModel(model_id=4, model_name="OPENCV", num_params=8),
#     CameraModel(model_id=5, model_name="OPENCV_FISHEYE", num_params=8),
#     CameraModel(model_id=6, model_name="FULL_OPENCV", num_params=12),
#     CameraModel(model_id=7, model_name="FOV", num_params=5),
#     CameraModel(model_id=8, model_name="SIMPLE_RADIAL_FISHEYE", num_params=4),
#     CameraModel(model_id=9, model_name="RADIAL_FISHEYE", num_params=5),
#     CameraModel(model_id=10, model_name="THIN_PRISM_FISHEYE", num_params=12)
# }

# From https://github.com/colmap/colmap/blob/dev/src/base/camera_models.h
#   SIMPLE_PINHOLE: f, cx, cy
#   PINHOLE: fx, fy, cx, cy
#   SIMPLE_RADIAL: f, cx, cy, k
#   RADIAL: f, cx, cy, k1, k2
#   OPENCV: fx, fy, cx, cy, k1, k2, p1, p2
#   OPENCV_FISHEYE: fx, fy, cx, cy, k1, k2, k3, k4
#   FULL_OPENCV: fx, fy, cx, cy, k1, k2, p1, p2, k3, k4, k5, k6
#   FOV: fx, fy, cx, cy, omega
#   SIMPLE_RADIAL_FISHEYE: f, cx, cy, k
#   RADIAL_FISHEYE: f, cx, cy, k1, k2
#   THIN_PRISM_FISHEYE: fx, fy, cx, cy, k1, k2, p1, p2, k3, k4, sx1, sy1


class ColmapFileHandler:
    """Class to read and write :code:`Colmap` models and workspaces."""

    @staticmethod
    def _parse_camera_param_list(cam):
        name = cam.model
        params = cam.params
        fx, fy, cx, cy, skew, r = None, None, None, None, None, None
        if name == "SIMPLE_PINHOLE":
            fx, cx, cy = params
        elif name == "PINHOLE":
            fx, fy, cx, cy = params
        elif name == "SIMPLE_RADIAL":
            fx, cx, cy, r = params
        elif name == "RADIAL":
            fx, cx, cy, k1, k2 = params
            r = [k1, k2]
        elif name == "OPENCV":
            fx, fy, cx, cy, k1, k2, p1, p2 = params
            r = [k1, k2, p1, p2]
        elif name == "OPENCV_FISHEYE":
            fx, fy, cx, cy, k1, k2, k3, k4 = params
            r = [k1, k2, k3, k4]
        elif name == "FULL_OPENCV":
            fx, fy, cx, cy, k1, k2, p1, p2, k3, k4, k5, k6 = params
            r = [k1, k2, p1, p2, k3, k4, k5, k6]
        elif name == "FOV":
            fx, fy, cx, cy, r = params
        elif name == "SIMPLE_RADIAL_FISHEYE":
            fx, cx, cy, r = params
        elif name == "RADIAL_FISHEYE":
            fx, cx, cy, k1, k2 = params
            r = [k1, k2]
        elif name == "THIN_PRISM_FISHEYE":
            fx, fy, cx, cy, k1, k2, p1, p2, k3, k4, sx1, sy1 = params
            r = [k1, k2, p1, p2, k3, k4, sx1, sy1]
        # PERSPECTIVE is defined in this Colmap fork
        #  https://github.com/Kai-46/VisSatSatelliteStereo
        elif name == "PERSPECTIVE":
            fx, fy, cx, cy, skew = params
        if fy is None:
            fy = fx
        if skew is None:
            skew = 0.0
        return fx, fy, cx, cy, skew, r

    @staticmethod
    def _convert_cameras(
        id_to_col_cameras,
        id_to_col_images,
        image_dp,
        image_fp_type,
        depth_map_idp=None,
        suppress_distortion_warnings=False,
        op=None,
    ):
        # From photogrammetry_importer\ext\read_write_model.py
        #   CameraModel = collections.namedtuple(
        #       "CameraModel", ["model_id", "model_name", "num_params"])
        #   Camera = collections.namedtuple(
        #       "Camera", ["id", "model", "width", "height", "params"])
        #   BaseImage = collections.namedtuple(
        #       "Image", ["id", "qvec", "tvec", "camera_id", "name", "xys", "point3D_ids"])

        cameras = []
        for col_image in id_to_col_images.values():
            current_camera = Camera()
            current_camera.id = col_image.id
            current_camera.set_rotation_with_quaternion(col_image.qvec)
            current_camera.set_camera_translation_vector_after_rotation(
                col_image.tvec
            )

            current_camera.image_fp_type = image_fp_type
            current_camera.image_dp = image_dp
            current_camera._relative_fp = col_image.name

            # log_report('INFO', 'image_dp: ' + str(image_dp))
            # log_report('INFO', 'col_image.name: ' + str(col_image.name))

            camera_model = id_to_col_cameras[col_image.camera_id]

            # log_report('INFO', 'image_id: ' + str(col_image.id))
            # log_report('INFO', 'camera_id: ' + str(col_image.camera_id))
            # log_report('INFO', 'camera_model: ' + str(camera_model))

            current_camera.width = camera_model.width
            current_camera.height = camera_model.height

            (
                fx,
                fy,
                cx,
                cy,
                skew,
                r,
            ) = ColmapFileHandler._parse_camera_param_list(
                camera_model,
            )
            if not suppress_distortion_warnings:
                check_radial_distortion(r, current_camera._relative_fp, op)

            camera_calibration_matrix = np.array(
                [[fx, skew, cx], [0, fy, cy], [0, 0, 1]]
            )
            current_camera.set_calibration(
                camera_calibration_matrix, radial_distortion=0
            )

            if depth_map_idp is not None:
                geometric_ifp = os.path.join(
                    depth_map_idp, col_image.name + ".geometric.bin"
                )
                photometric_ifp = os.path.join(
                    depth_map_idp, col_image.name + ".photometric.bin"
                )
                if os.path.isfile(geometric_ifp):
                    depth_map_ifp = geometric_ifp
                elif os.path.isfile(photometric_ifp):
                    depth_map_ifp = photometric_ifp
                else:
                    depth_map_ifp = None
                current_camera.set_depth_map_callback(
                    read_array,
                    depth_map_ifp,
                    Camera.DEPTH_MAP_WRT_CANONICAL_VECTORS,
                    shift_depth_map_to_pixel_center=False,
                )
            cameras.append(current_camera)
        return cameras

    @staticmethod
    def _convert_points(id_to_col_points3D):
        # From photogrammetry_importer\ext\read_write_model.py
        #   Point3D = collections.namedtuple(
        #       "Point3D", ["id", "xyz", "rgb", "error", "image_ids", "point2D_idxs"])

        col_points3D = id_to_col_points3D.values()
        points3D = []
        for col_point3D in col_points3D:
            current_point = Point(
                coord=col_point3D.xyz,
                color=col_point3D.rgb,
                id=col_point3D.id,
                scalars=None,
            )
            points3D.append(current_point)

        return points3D

    @staticmethod
    def _get_model_folder_ext(idp):
        ifp_s = os.listdir(idp)
        txt_list = ["cameras.txt", "images.txt", "points3D.txt"]
        bin_list = ["cameras.bin", "images.bin", "points3D.bin"]
        if len(set(ifp_s).intersection(txt_list)) == 3:
            ext = ".txt"
        elif len(set(ifp_s).intersection(bin_list)) == 3:
            ext = ".bin"
        else:
            ext = None
        return ext

    @staticmethod
    def _is_valid_model_folder(idp):
        ext = ColmapFileHandler._get_model_folder_ext(idp)
        return ext is not None

    @staticmethod
    def _is_valid_workspace_folder(idp):
        elements = os.listdir(idp)
        valid = True
        if "sparse" in elements:
            valid = ColmapFileHandler._is_valid_model_folder(
                os.path.join(idp, "sparse")
            )
        else:
            valid = False
        return valid

    @staticmethod
    def parse_colmap_model_folder(
        model_idp,
        image_dp,
        image_fp_type,
        depth_map_idp=None,
        suppress_distortion_warnings=False,
        op=None,
    ):
        """Parse a :code:`Colmap` model."""
        log_report("INFO", "Parse Colmap model folder: " + model_idp, op)

        assert ColmapFileHandler._is_valid_model_folder(model_idp)
        ext = ColmapFileHandler._get_model_folder_ext(model_idp)

        # cameras represent information about the camera model
        # images contain pose information
        id_to_col_cameras, id_to_col_images, id_to_col_points3D = read_model(
            model_idp, ext=ext
        )

        cameras = ColmapFileHandler._convert_cameras(
            id_to_col_cameras,
            id_to_col_images,
            image_dp,
            image_fp_type,
            depth_map_idp,
            suppress_distortion_warnings,
            op,
        )

        points3D = ColmapFileHandler._convert_points(id_to_col_points3D)

        return cameras, points3D

    @staticmethod
    def _disassemble_colmap_workspace_folder(workspace_idp):
        """Parse a :code:`Colmap` workspace."""
        assert ColmapFileHandler._is_valid_workspace_folder(workspace_idp)

        model_idp = os.path.join(workspace_idp, "sparse")
        image_idp = os.path.join(workspace_idp, "images")
        depth_map_idp = os.path.join(workspace_idp, "stereo", "depth_maps")
        poisson_mesh_ifp = os.path.join(workspace_idp, "meshed-poisson.ply")
        delaunay_mesh_ifp = os.path.join(workspace_idp, "meshed-delaunay.ply")
        if os.path.isfile(poisson_mesh_ifp):
            mesh_ifp = poisson_mesh_ifp
        elif os.path.isfile(delaunay_mesh_ifp):
            mesh_ifp = delaunay_mesh_ifp
        else:
            mesh_ifp = None

        return model_idp, image_idp, depth_map_idp, mesh_ifp

    @staticmethod
    def parse_colmap_folder(
        idp,
        use_workspace_images,
        image_dp,
        image_fp_type,
        suppress_distortion_warnings=False,
        op=None,
    ):
        """Parse a :code:`Colmap` model or a :code:`Colmap` workspace."""
        log_report("INFO", "idp: " + str(idp), op)

        if ColmapFileHandler._is_valid_model_folder(idp):
            model_idp = idp
            mesh_ifp = None
            depth_map_idp = None
        elif ColmapFileHandler._is_valid_workspace_folder(idp):
            (
                model_idp,
                image_idp_workspace,
                depth_map_idp,
                mesh_ifp,
            ) = ColmapFileHandler._disassemble_colmap_workspace_folder(idp)
            if use_workspace_images and os.path.isdir(image_idp_workspace):
                image_dp = image_idp_workspace
                log_report("INFO", "Using image directory in workspace.", op)
        else:
            log_report("ERROR", "Invalid colmap model / workspace", op)
            assert False, "Invalid colmap model / workspace"

        log_report("INFO", "image_dp: " + image_dp, op)
        cameras, points = ColmapFileHandler.parse_colmap_model_folder(
            model_idp,
            image_dp,
            image_fp_type,
            depth_map_idp,
            suppress_distortion_warnings=suppress_distortion_warnings,
            op=op,
        )

        return cameras, points, mesh_ifp

    @staticmethod
    def write_colmap_model(odp, cameras, points, op=None):
        """Write cameras and points as :code:`Colmap` model."""
        log_report("INFO", "Write Colmap model folder: " + odp, op)

        if not os.path.isdir(odp):
            os.mkdir(odp)

        # From photogrammetry_importer\ext\read_write_model.py
        #   CameraModel = collections.namedtuple(
        #       "CameraModel", ["model_id", "model_name", "num_params"])
        #   Camera = collections.namedtuple(
        #       "Camera", ["id", "model", "width", "height", "params"])
        #   BaseImage = collections.namedtuple(
        #       "Image", ["id", "qvec", "tvec", "camera_id", "name", "xys", "point3D_ids"])
        #   Point3D = collections.namedtuple(
        #       "Point3D", ["id", "xyz", "rgb", "error", "image_ids", "point2D_idxs"])

        colmap_cams = {}
        colmap_images = {}
        for cam in cameras:

            # TODO Support the "PINHOLE" camera model
            colmap_camera_model_name = "SIMPLE_PINHOLE"

            pp = cam.get_principal_point()
            colmap_cam = ColmapCamera(
                id=cam.id,
                model=colmap_camera_model_name,
                width=cam.width,
                height=cam.height,
                params=np.array([cam.get_focal_length(), pp[0], pp[1]]),
            )
            colmap_cams[cam.id] = colmap_cam

            colmap_image = ColmapImage(
                id=cam.id,
                qvec=cam.get_rotation_as_quaternion(),
                tvec=cam.get_translation_vec(),
                camera_id=cam.id,
                name=cam.get_file_name(),
                xys=[],
                point3D_ids=[],
            )
            colmap_images[cam.id] = colmap_image

        colmap_points3D = {}
        for point in points:
            colmap_point = ColmapPoint3D(
                id=point.id,
                xyz=point.coord,
                rgb=point.color,
                error=0,
                # The default settings in Colmap show only points with more than
                # 3 observations
                image_ids=[0, 1, 2],
                point2D_idxs=[0, 1, 2],
            )
            colmap_points3D[point.id] = colmap_point

        write_model(
            colmap_cams, colmap_images, colmap_points3D, odp, ext=".txt"
        )
