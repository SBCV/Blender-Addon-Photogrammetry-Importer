import os
import numpy as np
from photogrammetry_importer.ext.read_model import read_model

from photogrammetry_importer.camera import Camera
from photogrammetry_importer.point import Point


# From photogrammetry_importer\ext\read_model.py
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
    f, fx, fy, cx, cy = None, None, None, None, None
    if name == "SIMPLE_PINHOLE":
        f, cx, cy = params
    elif name == "PINHOLE":
        fx, fy, cx, cy = params
    elif name == "SIMPLE_RADIAL":
        f, cx, cy, _ = params
    elif name == "RADIAL":
        f, cx, cy, _, _ = params
    elif name == "OPENCV":
        fx, fy, cx, cy, _, _, _, _ = params
    elif name == "OPENCV_FISHEYE":
        fx, fy, cx, cy, _, _, _, _ = params
    elif name == "FULL_OPENCV":
        fx, fy, cx, cy, _, _, _, _, _, _, _, _ = params
    elif name == "FOV":
        fx, fy, cx, cy, _ = params
    elif name == "SIMPLE_RADIAL_FISHEYE":
        f, cx, cy, _ = params
    elif name == "RADIAL_FISHEYE":
        f, cx, cy, _, _ = params
    elif name == "THIN_PRISM_FISHEYE":
        fx, fy, cx, cy, _, _, _, _, _, _, _, _ = params
    if f is None:
        f = (fx + fy) * 0.5
    return f, cx, cy

class ColmapFileHandler(object):

    @staticmethod
    def convert_cameras(id_to_col_cameras, id_to_col_images, op):
        # CameraModel = collections.namedtuple(
        #   "CameraModel", ["model_id", "model_name", "num_params"])
        # Camera = collections.namedtuple(
        #    "Camera", ["id", "model", "width", "height", "params"])
        # BaseImage = collections.namedtuple(
        #    "Image", ["id", "qvec", "tvec", "camera_id", "name", "xys", "point3D_ids"])

        cameras = []
        for col_image in id_to_col_images.values():
            current_camera = Camera()
            current_camera.id = col_image.id
            current_camera.set_quaternion(col_image.qvec)
            current_camera.set_camera_translation_vector_after_rotation(col_image.tvec)
            current_camera.file_name = col_image.name
            camera_models = list(id_to_col_cameras.values())
            # Blender supports only one camera model for all images
            assert len(camera_models) == 1
            camera_model = camera_models[0]

            op.report({'INFO'}, 'camera_model: ' + str(camera_model))

            current_camera.width = camera_model.width
            current_camera.height = camera_model.height

            focal_length, cx, cy = parse_camera_param_list(camera_model)
            camera_calibration_matrix = np.array([[focal_length, 0, cx],
                            [0, focal_length, cy],
                            [0, 0, 1]])
            current_camera.set_calibration(
                camera_calibration_matrix, 
                radial_distortion=0)

            cameras.append(current_camera)
     
        return cameras

    @staticmethod
    def convert_points(id_to_col_points3D):
        # Point3D = collections.namedtuple(
        #   "Point3D", ["id", "xyz", "rgb", "error", "image_ids", "point2D_idxs"])
        
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
    def parse_colmap_model_folder(model_idp, op):

        op.report({'INFO'}, 'Parse Colmap model folder: ' + model_idp)

        ifp_s = os.listdir(model_idp)

        if len(set(ifp_s).intersection(['cameras.bin', 'images.bin', 'points3D.bin'])) == 3:
            ext = '.bin'
        elif len(set(ifp_s).intersection(['cameras.txt', 'images.txt', 'points3D.txt'])) == 3:
            ext = '.txt'
        else:
            assert False    # No valid model folder

        # cameras represent information about the camera model
        # images contain pose information
        id_to_col_cameras, id_to_col_images, id_to_col_points3D = read_model(
            model_idp, ext=ext)

        op.report({'INFO'}, 'id_to_col_cameras: ' + str(id_to_col_cameras))

        cameras = ColmapFileHandler.convert_cameras(
            id_to_col_cameras, id_to_col_images, op)

        points3D = ColmapFileHandler.convert_points(
            id_to_col_points3D)

        return cameras, points3D