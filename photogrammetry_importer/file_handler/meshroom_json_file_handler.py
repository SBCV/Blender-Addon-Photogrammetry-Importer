import json
import numpy as np
import os
from PIL import Image

from photogrammetry_importer.camera import Camera
from photogrammetry_importer.point import Point

def get_element(data_list, id_string, query_id, op):
    result = None
    for ele in data_list:
        if int(ele[id_string]) == query_id:
            result = ele
            break
    assert result is not None
    return result

class MeshroomJSONFileHandler:

    @staticmethod
    def parse_cameras(json_data, op):

        views = json_data['views']              # is a list of dicts (view)  
        intrinsics = json_data['intrinsics']    # is a list of dicts (intrinsic)
        extrinsics = json_data['poses']         # is a list of dicts (extrinsic)

        # IMPORTANT:
        # Views contain the number of input images  
        # Extrinsics may contain only a subset of views! 
        # (Not all views are necessarily contained in the reconstruction)

        cams = []
        image_index_to_camera_index = {}
        for rec_index, extrinsic in enumerate(extrinsics):

            camera = Camera()
            view_index = int(extrinsic['poseId'])
            image_index_to_camera_index[view_index] = rec_index

            corresponding_view = get_element(
                views, "poseId", view_index, op)

            camera.file_name = str(corresponding_view['path'])
            camera.width = int(corresponding_view['width'])
            camera.height = int(corresponding_view['height'])
            id_intrinsic = int(corresponding_view['intrinsicId'])

            intrinsic_params = get_element(
                intrinsics, "intrinsicId", id_intrinsic, op)

            focal_length = float(intrinsic_params['pxFocalLength']) 
            cx = float(intrinsic_params['principalPoint'][0])
            cy = float(intrinsic_params['principalPoint'][1])
 
            if 'distortionParams' in intrinsic_params and len(intrinsic_params['distortionParams']) > 0:
                # TODO proper handling of distortion parameters
                radial_distortion = float(intrinsic_params['distortionParams'][0])
            else:
                radial_distortion = 0.0

            camera_calibration_matrix = np.array([
                [focal_length, 0, cx],
                [0, focal_length, cy],
                [0, 0, 1]])

            camera.set_calibration(
                camera_calibration_matrix,
                radial_distortion)
            extrinsic_params = extrinsic['pose']['transform']

            cam_rotation_list = extrinsic_params['rotation']
            camera.set_rotation_mat(
                np.array(cam_rotation_list, dtype=float).reshape(3,3).T)
            camera.set_camera_center_after_rotation(
                np.array(extrinsic_params['center'], dtype=float))
            camera.view_index = view_index

            cams.append(camera)
        return cams, image_index_to_camera_index


    @staticmethod
    def parse_points(json_data, image_index_to_camera_index, op, path_to_input_files=None, view_index_to_file_name=None):

        compute_color = (not path_to_input_files is None) and (not view_index_to_file_name is None)
        structure = json_data['structure']

        if compute_color:
            op.report({'INFO'},'Computing color information from files: ...')
            view_index_to_image = {}
            for view_index, file_name in view_index_to_file_name.items():
                image_path = os.path.join(path_to_input_files, file_name)
                pil_image = Image.open(image_path)
                view_index_to_image[view_index] = pil_image

            op.report({'INFO'},'Computing color information from files: Done')

        points = []
        for json_point in structure:

            r = g = b = 0

            # color information can only be computed if input files are provided
            if compute_color:
                for observation in json_point['observations']:
                    view_index = int(observation['observationId'])

                    # REMARK: pil/pillow: image.size == (width, height)
                    x_in_json_file = float(observation['x'][0])    # x has index 0
                    y_in_json_file = float(observation['x'][1])    # y has index 1

                    current_image = view_index_to_image[view_index]
                    current_r, current_g, current_b = current_image.getpixel((x_in_json_file, y_in_json_file))
                    r += current_r
                    g += current_g
                    b += current_b

                # normalize the rgb values
                amount_observations = len(json_point['observations'])
                r /= amount_observations
                g /= amount_observations
                b /= amount_observations

            custom_point = Point(
                coord=np.array(json_point['X'], dtype=float),
                color=np.array([r, g, b], dtype=int),
                id=int(json_point['landmarkId']),
                scalars=[])

            points.append(custom_point)
        return points

    @staticmethod
    def parse_meshroom_file(input_meshroom_file_path, path_to_images, op):
        """
        The path_to_input_files parameter is optional, if provided the returned points carry also color information
        :param input_meshroom_file_path:
        :param path_to_images: Path to the input images (used to infer the color of the structural points)
        :return:
        """
        op.report({'INFO'}, 'parse_meshroom_file: ...')
        op.report({'INFO'},'input_meshroom_file_path: ' + input_meshroom_file_path)
        input_file = open(input_meshroom_file_path, 'r')
        json_data = json.load(input_file)

        cams, image_index_to_camera_index = MeshroomJSONFileHandler.parse_cameras(json_data, op)
        view_index_to_file_name = {cam.view_index: cam.file_name for cam in cams}
        points = MeshroomJSONFileHandler.parse_points(
            json_data, image_index_to_camera_index, op, path_to_images, view_index_to_file_name)
        op.report({'INFO'},'parse_meshroom_file: Done')
        return cams, points

