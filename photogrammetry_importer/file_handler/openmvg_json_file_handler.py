import json
import numpy as np
import os
from PIL import Image

from Utility.Types.Camera import Camera
from Utility.Types.Point import Point, Measurement
from Utility.Logging_Extension import logger

class OpenMVGFileHandler:

    @staticmethod
    def parse_cameras(json_data):

        views = json_data['views']
        intrinsics = json_data['intrinsics']
        extrinsics = json_data['extrinsics']

        # Remark: extrinsics may contain only a subset of views! (no all views are contained in the reconstruction)
        #         Matching entries are determined by view['key'] == extrinsics['key']

        cams = []

        # Mapping from input images to reconstructed cameras
        image_index_to_camera_index = {}

        # IMPORTANT: Views contains number of input images
        #            (this may be more than the number of reconstructed poses)
        for rec_index, extrinsic in enumerate(extrinsics):    # Iterate over extrinsics, not views!

            camera = Camera()

            # The key is defined w.r.t. view indices (NOT reconstructed camera indices)
            view_index = int(extrinsic['key'])

            image_index_to_camera_index[view_index] = rec_index

            view = views[view_index]

            camera.file_name = view['value']['ptr_wrapper']['data']['filename']
            id_intrinsic = view['value']['ptr_wrapper']['data']['id_intrinsic']

            # handle intrinsic params
            intrinsic_params = intrinsics[int(id_intrinsic)]['value']['ptr_wrapper']['data']
            focal_length = intrinsic_params['focal_length']
            principal_point = intrinsic_params['principal_point']

            if 'disto_k3' in intrinsic_params:
                logger.info('3 Radial Distortion Parameters are not supported')
                assert False

            # For Radial there are several options: "None", disto_k1, disto_k3
            if 'disto_k1' in intrinsic_params:
                radial_distortion = float(intrinsic_params['disto_k1'][0])
            else:  # No radial distortion, i.e. pinhole camera model
                radial_distortion = 0

            camera.set_calibration(
                np.asarray([[focal_length, 0, principal_point[0]],
                          [0, focal_length, principal_point[1]],
                          [0, 0, 1]], dtype=float),
                radial_distortion
                )

            # handle extrinsic params (pose = extrinsic)

            extrinsic_params = extrinsic['value']
            cam_rotation_list = extrinsic_params['rotation']
            camera.set_rotation_mat(np.array(cam_rotation_list, dtype=float))
            camera._center = np.array(extrinsic_params['center'], dtype=float).T

            # the camera looks in the z direction
            cam_view_vec_cam_coordinates = np.array([0, 0, 1]).T

            # transform view direction from cam coordinates to world coordinates
            # for rotations the inverse is equal to the transpose
            rotation_inv_mat = camera.get_rotation_mat().T
            camera.normal = rotation_inv_mat.dot(cam_view_vec_cam_coordinates)

            camera.view_index = view_index

            cams.append(camera)
        return cams, image_index_to_camera_index

    @staticmethod
    def parse_points(json_data, image_index_to_camera_index, path_to_input_files=None, view_index_to_file_name=None):

        compute_color = (not path_to_input_files is None) and (not view_index_to_file_name is None)
        structure = json_data['structure']

        if compute_color:
            logger.info('Computing color information from files: ...')
            view_index_to_image = {}
            for view_index, file_name in view_index_to_file_name.items():
                image_path = os.path.join(path_to_input_files, file_name)
                pil_image = Image.open(image_path)
                view_index_to_image[view_index] = pil_image

            logger.info('Computing color information from files: Done')

            logger.vinfo('view_index_to_image.keys()', view_index_to_image.keys())

        points = []
        for json_point in structure:
            custom_point = Point()
            position = json_point['value']['X']
            custom_point.set_coord(np.array(position))
            custom_point.id = int(json_point['key'])
            custom_point.measurements = []

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

                    # Measurements is a list of < Measurement >
                    # < Measurement > = < Image index > < Feature Index > < xy >
                    custom_point.measurements.append(
                        Measurement(
                            camera_index= image_index_to_camera_index[view_index],
                            feature_index=int(observation['value']['id_feat']),
                            x=x_in_json_file,
                            y=y_in_json_file,
                            x_y_are_image_coords=True))

                # normalize the rgb values
                amount_observations = len(json_point['value']['observations'])
                r /= amount_observations
                g /= amount_observations
                b /= amount_observations

            custom_point.set_color(np.array([r, g, b], dtype=int))
            points.append(custom_point)
        return points


    @staticmethod
    def parse_openmvg_file(input_openMVG_file_path):
        """
        The path_to_input_files parameter is optional, if provided the returned points carry also color information
        :param input_openMVG_file_path:
        :param path_to_input_files: Path to the input images (used to infer the color of the structural points)
        :return:
        """
        logger.info('parse_openmvg_file: ...')
        logger.vinfo('input_openMVG_file_path', input_openMVG_file_path)
        input_file = open(input_openMVG_file_path, 'r')
        json_data = json.load(input_file)

        path_to_input_files = os.path.abspath(json_data['root_path'])

        cams, image_index_to_camera_index = OpenMVGFileHandler.parse_cameras(json_data)
        view_index_to_file_name = {cam.view_index: cam.file_name for cam in cams}
        points = OpenMVGFileHandler.parse_points(
            json_data, image_index_to_camera_index, path_to_input_files, view_index_to_file_name)
        logger.info('parse_openmvg_file: Done')
        return cams, points

