import os
import numpy as np
from photogrammetry_importer.ext.read_write_model import read_model
from photogrammetry_importer.ext.read_write_model import write_model

from photogrammetry_importer.ext.read_write_model import Camera as ColmapCamera
from photogrammetry_importer.ext.read_write_model import Image as ColmapImage
from photogrammetry_importer.ext.read_write_model import Point3D as ColmapPoint3D

from photogrammetry_importer.types.camera import Camera
from photogrammetry_importer.types.point import Point
from photogrammetry_importer.utility.blender_camera_utility import check_radial_distortion
from photogrammetry_importer.utility.blender_logging_utility import log_report

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

def parse_camera_param_list(cam):
    name = cam.model
    params = cam.params 
    f, fx, fy, cx, cy, r = None, None, None, None, None, None
    if name == "SIMPLE_PINHOLE":
        f, cx, cy = params
    elif name == "PINHOLE":
        fx, fy, cx, cy = params
    elif name == "SIMPLE_RADIAL":
        f, cx, cy, r = params
    elif name == "RADIAL":
        f, cx, cy, k1, k2 = params
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
        f, cx, cy, r = params
    elif name == "RADIAL_FISHEYE":
        f, cx, cy, k1, k2 = params
        r = [k1, k2]
    elif name == "THIN_PRISM_FISHEYE":
        fx, fy, cx, cy, k1, k2, p1, p2, k3, k4, sx1, sy1 = params
        r = [k1, k2, p1, p2, k3, k4, sx1, sy1]
    if f is None:
        f = (fx + fy) * 0.5
    return f, cx, cy, r

class ColmapFileHandler(object):

    @staticmethod
    def convert_cameras(id_to_col_cameras, id_to_col_images, image_dp, image_fp_type, depth_map_idp, suppress_distortion_warnings, op):
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
            current_camera.set_quaternion(col_image.qvec)
            current_camera.set_camera_translation_vector_after_rotation(
                col_image.tvec)

            current_camera.image_fp_type = image_fp_type
            current_camera.image_dp = image_dp
            current_camera._relative_fp = col_image.name
            
            camera_model = id_to_col_cameras[col_image.camera_id]
    
            # log_report('INFO', 'image_id: ' + str(col_image.id))
            # log_report('INFO', 'camera_id: ' + str(col_image.camera_id))
            # log_report('INFO', 'camera_model: ' + str(camera_model))

            current_camera.width = camera_model.width
            current_camera.height = camera_model.height

            focal_length, cx, cy, r = parse_camera_param_list(camera_model)
            if not suppress_distortion_warnings:
                check_radial_distortion(r, current_camera._relative_fp, op)

            camera_calibration_matrix = np.array([
                [focal_length, 0, cx],
                [0, focal_length, cy],
                [0, 0, 1]])
            current_camera.set_calibration(
                camera_calibration_matrix, 
                radial_distortion=0)

            if depth_map_idp is not None:
                geometric_ifp = os.path.join(depth_map_idp, col_image.name + '.geometric.bin')
                photometric_ifp = os.path.join(depth_map_idp, col_image.name + '.photometric.bin')
                if os.path.isfile(geometric_ifp):
                    current_camera.depth_map_fp = geometric_ifp
                elif os.path.isfile(photometric_ifp):
                    current_camera.depth_map_fp = photometric_ifp
            cameras.append(current_camera)
     
        return cameras

    @staticmethod
    def convert_points(id_to_col_points3D):
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
                scalars=None)
            points3D.append(current_point)

        return points3D

    @staticmethod
    def get_model_folder_ext(idp):
        ifp_s = os.listdir(idp)
        if len(set(ifp_s).intersection(['cameras.txt', 'images.txt', 'points3D.txt'])) == 3:
            ext = '.txt'
        elif len(set(ifp_s).intersection(['cameras.bin', 'images.bin', 'points3D.bin'])) == 3:
            ext = '.bin'
        else:
            ext = None
        return ext

    @staticmethod
    def is_valid_model_folder(idp):
        ext = ColmapFileHandler.get_model_folder_ext(idp)
        return ext is not None

    @staticmethod
    def is_valid_workspace_folder(idp):
        elements = os.listdir(idp)
        valid = True
        if 'sparse' in elements:
            valid = ColmapFileHandler.is_valid_model_folder(
                os.path.join(idp, 'sparse'))
        else:
            valid = False
        return valid

    @staticmethod
    def parse_colmap_model_folder(model_idp, image_dp, image_fp_type, depth_map_idp, suppress_distortion_warnings, op):

        op.report({'INFO'}, 'Parse Colmap model folder: ' + model_idp)

        assert ColmapFileHandler.is_valid_model_folder(model_idp)
        ext = ColmapFileHandler.get_model_folder_ext(model_idp)

        # cameras represent information about the camera model
        # images contain pose information
        id_to_col_cameras, id_to_col_images, id_to_col_points3D = read_model(
            model_idp, ext=ext)

        op.report({'INFO'}, 'id_to_col_cameras: ' + str(id_to_col_cameras))

        cameras = ColmapFileHandler.convert_cameras(
            id_to_col_cameras,
            id_to_col_images,
            image_dp,
            image_fp_type,
            depth_map_idp,
            suppress_distortion_warnings,
            op)

        points3D = ColmapFileHandler.convert_points(
            id_to_col_points3D)

        return cameras, points3D

    @staticmethod
    def parse_colmap_workspace_folder(workspace_idp):

        assert ColmapFileHandler.is_valid_workspace_folder(workspace_idp)

        model_idp = os.path.join(workspace_idp, 'sparse')
        poisson_mesh_ifp = os.path.join(workspace_idp, 'meshed-poisson.ply')
        delaunay_mesh_ifp = os.path.join(workspace_idp, 'meshed-delaunay.ply')
        if os.path.isfile(poisson_mesh_ifp):
            mesh_ifp = poisson_mesh_ifp
        elif os.path.isfile(delaunay_mesh_ifp):
            mesh_ifp = delaunay_mesh_ifp
        else:
            mesh_ifp = None
        depth_map_idp = os.path.join(workspace_idp, 'stereo', 'depth_maps')

        return model_idp, depth_map_idp, mesh_ifp

    @staticmethod
    def parse_colmap_folder(idp, image_dp, image_fp_type, suppress_distortion_warnings, op):

        op.report({'INFO'}, 'idp: ' + str(idp))

        if ColmapFileHandler.is_valid_model_folder(idp):
            model_idp = idp
            mesh_ifp = None
            depth_map_idp = None
        elif ColmapFileHandler.is_valid_workspace_folder(idp):
            model_idp, depth_map_idp, mesh_ifp = ColmapFileHandler.parse_colmap_workspace_folder(idp)

        cameras, points = ColmapFileHandler.parse_colmap_model_folder(
            model_idp, image_dp, image_fp_type, depth_map_idp, suppress_distortion_warnings, op)

        return cameras, points, mesh_ifp


    @staticmethod
    def write_colmap_model(odp, cameras, points, op):
        op.report({'INFO'}, 'Write Colmap model folder: ' + odp)

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
                params=np.array([cam.get_focal_length(), pp[0], pp[1]]))
            colmap_cams[cam.id] = colmap_cam

            colmap_image = ColmapImage(
                id=cam.id, 
                qvec=cam.get_quaternion(), 
                tvec=cam.get_translation_vec(),
                camera_id=cam.id, 
                name=cam.get_file_name(),
                xys=[], 
                point3D_ids=[])
            colmap_images[cam.id] = colmap_image

        colmap_points3D = {}
        for point in points:
            colmap_point = ColmapPoint3D(
                id=point.id, 
                xyz=point.coord, 
                rgb=point.color,
                error=0, 
                # The default settings in Colmap show only points with 3+ observations
                image_ids=[0, 1, 2],        
                point2D_idxs=[0, 1, 2]
            )
            colmap_points3D[point.id] = colmap_point

        write_model(
            colmap_cams, 
            colmap_images, 
            colmap_points3D, 
            odp, 
            ext='.txt')

        
