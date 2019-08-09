import json
import numpy as np
import os
from PIL import Image

from photogrammetry_importer.camera import Camera
from photogrammetry_importer.point import Point

class OpenMVGJSONFileHandler:

    @staticmethod
    def parse_cameras(json_data, op):

        views = json_data['views']
        intrinsics = json_data['intrinsics']
        extrinsics = json_data['extrinsics']

        # IMPORTANT:
        # Views contain the number of input images  
        # Extrinsics may contain only a subset of views! (Potentially not all views are contained in the reconstruction)
        # Matching entries are determined by view['key'] == extrinsics['key']

        cams = []
        image_index_to_camera_index = {}
        for rec_index, extrinsic in enumerate(extrinsics):    # Iterate over extrinsics, not views!

            camera = Camera()
            # The key is defined w.r.t. view indices (NOT reconstructed camera indices)
            view_index = int(extrinsic['key'])
            image_index_to_camera_index[view_index] = rec_index
            corresponding_view = views[view_index]

            camera.file_name = corresponding_view['value']['ptr_wrapper']['data']['filename']
            camera.width = corresponding_view['value']['ptr_wrapper']['data']['width']
            camera.height = corresponding_view['value']['ptr_wrapper']['data']['height']
            id_intrinsic = corresponding_view['value']['ptr_wrapper']['data']['id_intrinsic']

            # handle intrinsic params
            intrinsic_params = intrinsics[int(id_intrinsic)]['value']['ptr_wrapper']['data']
            focal_length = intrinsic_params['focal_length']
            principal_point_image = intrinsic_params['principal_point']
            cx = principal_point_image[0] - camera.width / 2.0
            cy = principal_point_image[1] - camera.height / 2.0
 
            if 'disto_k3' in intrinsic_params:
                op.report({'INFO'},'3 Radial Distortion Parameters are not supported')
                assert False

            # For Radial there are several options: "None", disto_k1, disto_k3
            if 'disto_k1' in intrinsic_params:
                radial_distortion = float(intrinsic_params['disto_k1'][0])
            else:  # No radial distortion, i.e. pinhole camera model
                radial_distortion = 0

            camera_calibration_matrix = np.array([
                [focal_length, 0, cx],
                [0, focal_length, cy],
                [0, 0, 1]])

            camera.set_calibration(
                camera_calibration_matrix,
                radial_distortion)
            extrinsic_params = extrinsic['value']
            cam_rotation_list = extrinsic_params['rotation']
            camera.set_rotation_mat(np.array(cam_rotation_list, dtype=float))
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
                for observation in json_point['value']['observations']:
                    view_index = int(observation['key'])

                    # REMARK: The order of ndarray.shape (first height, then width) is complimentary to
                    # pils image.size (first width, then height).
                    # That means
                    # height, width = segmentation_as_matrix.shape
                    # width, height = image.size

                    # Therefore: x_in_openmvg_file == x_image == y_ndarray
                    # and y_in_openmvg_file == y_image == x_ndarray
                    x_in_json_file = float(observation['value']['x'][0])    # x has index 0
                    y_in_json_file = float(observation['value']['x'][1])    # y has index 1

                    current_image = view_index_to_image[view_index]
                    current_r, current_g, current_b = current_image.getpixel((x_in_json_file, y_in_json_file))
                    r += current_r
                    g += current_g
                    b += current_b

                # normalize the rgb values
                amount_observations = len(json_point['value']['observations'])
                r /= amount_observations
                g /= amount_observations
                b /= amount_observations

            custom_point = Point(
                coord=np.array(json_point['value']['X'], dtype=float),
                color=np.array([r, g, b], dtype=int),
                id=int(json_point['key']),
                scalars=[])

            points.append(custom_point)
        return points

    @staticmethod
    def parse_openmvg_file(input_openMVG_file_path, path_to_images, op):
        """
        The path_to_input_files parameter is optional, if provided the returned points carry also color information
        :param input_openMVG_file_path:
        :param path_to_images: Path to the input images (used to infer the color of the structural points)
        :return:
        """
        op.report({'INFO'}, 'parse_openmvg_file: ...')
        op.report({'INFO'},'input_openMVG_file_path: ' + input_openMVG_file_path)
        input_file = open(input_openMVG_file_path, 'r')
        json_data = json.load(input_file)

        cams, image_index_to_camera_index = OpenMVGJSONFileHandler.parse_cameras(json_data, op)
        view_index_to_file_name = {cam.view_index: cam.file_name for cam in cams}
        points = OpenMVGJSONFileHandler.parse_points(
            json_data, image_index_to_camera_index, op, path_to_images, view_index_to_file_name)
        op.report({'INFO'},'parse_openmvg_file: Done')
        return cams, points

