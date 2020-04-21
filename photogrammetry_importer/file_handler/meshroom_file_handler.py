import json
import numpy as np
import os

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

class MeshroomFileHandler:

    # Note: *.SfM files are actually just *.JSON files.

    @staticmethod
    def _parse_cameras_from_json_data(json_data, image_dp, image_fp_type, op):

        cams = []
        image_index_to_camera_index = {}

        is_valid_file = 'views' in json_data and 'intrinsics' in json_data and 'poses' in json_data

        if not is_valid_file:
            op.report(
                {'ERROR'},
                'FILE FORMAT ERROR: Incorrect SfM/JSON file. Must contain the SfM reconstruction results: ' +
                'view, intrinsics and poses.')
            return cams, image_index_to_camera_index

        views = json_data['views']              # is a list of dicts (view)  
        intrinsics = json_data['intrinsics']    # is a list of dicts (intrinsic)
        extrinsics = json_data['poses']         # is a list of dicts (extrinsic)

        # IMPORTANT:
        # Views contain the number of input images  
        # Extrinsics may contain only a subset of views! 
        # (Not all views are necessarily contained in the reconstruction)

        for rec_index, extrinsic in enumerate(extrinsics):

            camera = Camera()
            view_index = int(extrinsic['poseId'])
            image_index_to_camera_index[view_index] = rec_index

            corresponding_view = get_element(
                views, "poseId", view_index, op)

            camera.image_fp_type = image_fp_type
            camera.image_dp = image_dp
            camera._absolute_fp = str(corresponding_view['path'])
            camera._relative_fp = os.path.basename(str(corresponding_view['path']))
            camera._undistorted_relative_fp = str(extrinsic['poseId']) + '.exr'
            if image_dp is None:
                camera._undistorted_absolute_fp = None
            else:
                camera._undistorted_absolute_fp = os.path.join(
                    image_dp, camera._undistorted_relative_fp)
                
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
    def _parse_points_from_json_data(json_data, image_index_to_camera_index, op):

        points = []
        is_valid_file = 'structure' in json_data

        if not is_valid_file:
            op.report(
                {'ERROR'},
                'FILE FORMAT ERROR: Incorrect SfM/JSON file. Must contain the SfM reconstruction results: structure.')
            return points

        structure = json_data['structure']
        for json_point in structure:
            custom_point = Point(
                coord=np.array(json_point['X'], dtype=float),
                color=np.array(json_point['color'], dtype=int),
                id=int(json_point['landmarkId']),
                scalars=[])
            points.append(custom_point)
        return points

    @staticmethod
    def parse_sfm_file(sfm_sfm_fp, image_dp, image_fp_type, op):
        """
        Parses cameras.sfm/sfm.sfm/sfm.json files created by the StructureFromMotion / ConvertSfMFormat node in Meshroom
        :param sfm_sfm_fp:
        :return:
        """
        op.report({'INFO'}, 'parse_sfm_sfm_file: ...')
        op.report({'INFO'},'sfm_sfm_fp: ' + sfm_sfm_fp)
        input_file = open(sfm_sfm_fp, 'r')
        json_data = json.load(input_file)

        cams, image_index_to_camera_index = MeshroomFileHandler._parse_cameras_from_json_data(
            json_data, image_dp, image_fp_type, op)
        if 'structure' in json_data:
            points = MeshroomFileHandler._parse_points_from_json_data(
                json_data, image_index_to_camera_index, op)
        else:
            points = []
        op.report({'INFO'},'parse_sfm_sfm_file: Done')
        return cams, points


    @staticmethod
    def get_latest_node(json_graph, node_key):
        i = 0
        while node_key + "_" + str(i + 1) in json_graph:
            i = i + 1
        if i == 0:
            return None
        else:
            return json_graph[node_key + "_" + str(i)]

    @staticmethod
    def get_latest_node_data_fp(cache_dp, json_graph, node_key, fn_or_fn_list):

        if isinstance(fn_or_fn_list, str):
            fn_list = [fn_or_fn_list]
        else:
            fn_list = fn_or_fn_list

        data_node = MeshroomFileHandler.get_latest_node(json_graph, node_key)
        data_fp = None
        if data_node is not None:
            node_type = data_node['nodeType']
            uid_0 = data_node['uids']['0']
            for fn in fn_list:
                possible_data_fp = os.path.join(cache_dp, node_type, uid_0, fn)
                if os.path.isfile(possible_data_fp):
                    data_fp = possible_data_fp
                    break
        return data_fp


    @staticmethod
    def parse_meshrom_mg_file(mg_fp, op):
        cache_dp = os.path.join(os.path.dirname(mg_fp), 'MeshroomCache')
        json_data = json.load(open(mg_fp, 'r'))
        json_graph = json_data['graph']

        sfm_fp = MeshroomFileHandler.get_latest_node_data_fp(
            cache_dp, json_graph, 'ConvertSfMFormat', ['sfm.sfm', 'sfm.json'])
        if sfm_fp is None:
            sfm_fp = MeshroomFileHandler.get_latest_node_data_fp(
                cache_dp, json_graph, 'StructureFromMotion', 'cameras.sfm')

        mesh_fp = MeshroomFileHandler.get_latest_node_data_fp(
            cache_dp, json_graph, 'Texturing', 'texturedMesh.obj')
        if mesh_fp is None:
            mesh_fp = MeshroomFileHandler.get_latest_node_data_fp(
                cache_dp, json_graph, 'MeshFiltering', 'mesh.obj')
        if mesh_fp is None:
            mesh_fp = MeshroomFileHandler.get_latest_node_data_fp(
                cache_dp, json_graph, 'Meshing', 'mesh.obj')

        op.report({'INFO'},'mesh_fp: ' + mesh_fp)

        return sfm_fp, mesh_fp


    @staticmethod
    def parse_meshroom_file(meshroom_ifp, image_dp, image_fp_type, op):
        """
        :param meshroom_ifp:
        :return:
        """
        op.report({'INFO'}, 'parse_meshroom_file: ...')
        op.report({'INFO'},'meshroom_ifp: ' + meshroom_ifp)

        ext = os.path.splitext(meshroom_ifp)[1].lower()
        if ext == '.mg':
            meshroom_ifp, mesh_fp = MeshroomFileHandler.parse_meshrom_mg_file(
                meshroom_ifp, op)
        else:
            assert ext == '.json' or ext == '.sfm'
            mesh_fp = None

        cams, points = MeshroomFileHandler.parse_sfm_file(
            meshroom_ifp, image_dp, image_fp_type, op)

        op.report({'INFO'},'parse_meshroom_file: Done')
        return cams, points, mesh_fp
