import os
import numpy as np
from photogrammetry_importer.ext.read_model import read_model

from photogrammetry_importer.camera import Camera
from photogrammetry_importer.point import Point
from photogrammetry_importer.measurement import Measurement

class ColmapFileHandler(object):

    @staticmethod
    def convert_cameras(id_to_col_cameras, id_to_col_images):
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

            current_camera.width = camera_model.width
            current_camera.height = camera_model.height

            # the first parameter is always the focal length
            focal_length = camera_model.params[0]

            camera_calibration_matrix = np.array([[focal_length, 0, 0],
                            [0, focal_length, 0],
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
                measurements = [], 
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
            id_to_col_cameras, id_to_col_images)

        points3D = ColmapFileHandler.convert_points(
            id_to_col_points3D)

        return cameras, points3D