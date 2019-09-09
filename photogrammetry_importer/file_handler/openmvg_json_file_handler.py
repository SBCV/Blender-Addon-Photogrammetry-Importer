import json
import numpy as np
import os

from photogrammetry_importer.camera import Camera
from photogrammetry_importer.point import Point

class OpenMVGJSONFileHandler:

    @staticmethod
    def parse_cameras(json_data, op):

        views = {item['key']:item for item in json_data['views']}
        intrinsics = {item['key']:item for item in json_data['intrinsics']}
        extrinsics = {item['key']:item for item in json_data['extrinsics']}

        # IMPORTANT:
        # Views contain the description about the dataset and attribute to Pose and Intrinsic data.
        # View -> id_pose, id_intrinsic
        # Since sometimes some views cannot be localized, there is some missing pose and intrinsic data.
        # Extrinsics may contain only a subset of views! (Potentially not all views are contained in the reconstruction)

        cams = []
        # Iterate over views, and create camera if Intrinsic and Pose data exist
        for id, view in views.items():    # Iterate over views

            id_view = view['key'] # Should be equal to view['value']['ptr_wrapper']['data']['id_view']
            view_data = view['value']['ptr_wrapper']['data']
            id_pose = view_data['id_pose']
            id_intrinsic = view_data['id_intrinsic']

            # Check if the view is having corresponding Pose and Intrinsic data
            if id_pose in extrinsics.keys() and \
               id_intrinsic in intrinsics.keys():

                camera = Camera()

                camera.file_name = view_data['filename']
                camera.width = view_data['width']
                camera.height = view_data['height']
                id_intrinsic = view_data['id_intrinsic']

                # handle intrinsic params
                intrinsic_data = intrinsics[int(id_intrinsic)]['value']['ptr_wrapper']['data']
                polymorphic_name = intrinsics[int(id_intrinsic)]['value']['polymorphic_name']

                if polymorphic_name == 'spherical':
                    camera.set_panoramic_type(Camera.panoramic_type_equirectangular)
                    # create some dummy values
                    focal_length = 0     
                    cx = camera.width / 2
                    cy = camera.height / 2
                else:

                    focal_length = intrinsic_data['focal_length']
                    principal_point = intrinsic_data['principal_point']
                    cx = principal_point[0]
                    cy = principal_point[1]
        
                if 'disto_k3' in intrinsic_data:
                    op.report({'INFO'},'3 Radial Distortion Parameters are not supported')
                    assert False

                # For Radial there are several options: "None", disto_k1, disto_k3
                if 'disto_k1' in intrinsic_data:
                    radial_distortion = float(intrinsic_data['disto_k1'][0])
                else:  # No radial distortion, i.e. pinhole camera model
                    radial_distortion = 0

                camera_calibration_matrix = np.array([
                    [focal_length, 0, cx],
                    [0, focal_length, cy],
                    [0, 0, 1]])

                camera.set_calibration(
                    camera_calibration_matrix,
                    radial_distortion)
                extrinsic_params = extrinsics[id_pose]
                cam_rotation_list = extrinsic_params['value']['rotation']
                camera.set_rotation_mat(np.array(cam_rotation_list, dtype=float))
                camera.set_camera_center_after_rotation(
                    np.array(extrinsic_params['value']['center'], dtype=float))
                camera.view_index = id_view

                cams.append(camera)
        return cams


    @staticmethod
    def parse_points(json_data, op, path_to_input_files=None, view_index_to_file_name=None):

        try:
            from PIL import Image
            compute_color = (not path_to_input_files is None) and (not view_index_to_file_name is None)
        except ImportError:
            compute_color = False
            
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

        cams = OpenMVGJSONFileHandler.parse_cameras(json_data, op)
        view_index_to_file_name = {cam.view_index: cam.file_name for cam in cams}
        points = OpenMVGJSONFileHandler.parse_points(
            json_data, op, path_to_images, view_index_to_file_name)
        op.report({'INFO'},'parse_openmvg_file: Done')
        return cams, points

