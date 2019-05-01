'''
Copyright (C) 2018 Sebastian Bullinger

Created by Sebastian Bullinger

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import numpy as np
from photogrammetry_importer.ext.plyfile import PlyData, PlyElement
from photogrammetry_importer.point import Point


# REMARK: In PLY file format FLOAT is SINGLE precision (32 bit) and DOUBLE is DOUBLE PRECISION (64 bit)
class PLYFileHandler:

    @staticmethod
    def __ply_data_vertices_to_vetex_list(ply_data):

        vertex_data_type_names = ply_data['vertex'].data.dtype.names
        use_color = False
        if 'red' in vertex_data_type_names and 'green' in vertex_data_type_names and 'blue' in vertex_data_type_names:
            use_color = True

        vertices = []
        value_keys = [x for x, y in sorted(ply_data['vertex'].data.dtype.fields.items(),key=lambda k: k[1])]
        non_scalar_value_keys = ['x', 'y', 'z', 'red', 'green', 'blue', 'nx', 'ny', 'nz', 'measurements']
        scalar_value_keys = [value_key for value_key in value_keys if not value_key in non_scalar_value_keys]
        print('Found the following vertex properties: ' + str(value_keys))

        #scalar_value_keys = [value_key for (value_key, some_value) in ]
        #logger.info(scalar_value_keys)

        print('Found ' + str(len(ply_data['vertex'].data)) + ' vertices')
        for point_index, line in enumerate(ply_data['vertex'].data):
            coord = np.array([line['x'], line['y'], line['z']])
            if use_color:
                color = np.array([line['red'], line['green'], line['blue']])
            else:
                color = np.array([255, 255, 255])
            scalars = dict()
            for scalar_value_key in scalar_value_keys:
                scalars[scalar_value_key] = line[scalar_value_key]

            current_point = Point(coord=coord, color=color, measurements=None, id=point_index, scalars=None)
            vertices.append(current_point)

        ply_data_vertex_dtype = ply_data['vertex'].dtype
        ply_data_vertex_data_dtype = ply_data['vertex'].data.dtype

        return vertices, ply_data_vertex_dtype, ply_data_vertex_data_dtype


    @staticmethod
    def __vertices_to_ply_vertex_element(point_list, ply_data_vertex_data_dtype_list):

        ply_data_vertex_data_dtype = np.dtype(ply_data_vertex_data_dtype_list)

        # if measurements are used, then we do not know one dimension of the array
        vertex_output_array = np.empty((len(point_list),), dtype=ply_data_vertex_data_dtype)

        with_color = False
        if 'red' in ply_data_vertex_data_dtype.names and \
                        'green' in ply_data_vertex_data_dtype.names and \
                        'blue' in ply_data_vertex_data_dtype.names:
            with_color = True

        with_normals = False
        if 'nx' in ply_data_vertex_data_dtype.names and \
                        'ny' in ply_data_vertex_data_dtype.names and \
                        'nz' in ply_data_vertex_data_dtype.names:
            with_normals = True

        with_measurements = 'measurements' in ply_data_vertex_data_dtype.names

        # set all the values, offered / defined by property_type_list
        for index, point in enumerate(point_list):

            #row = np.empty(1, dtype=ply_data_vertex_data_dtype)
            vertex_output_array[index]['x'] = point.coord[0]
            vertex_output_array[index]['y'] = point.coord[1]
            vertex_output_array[index]['z'] = point.coord[2]

            if with_color:
                vertex_output_array[index]['red'] = point.color[0]
                vertex_output_array[index]['green'] = point.color[1]
                vertex_output_array[index]['blue'] = point.color[2]

            if with_normals:
                vertex_output_array[index]['nx'] = point.normal[0]
                vertex_output_array[index]['ny'] = point.normal[1]
                vertex_output_array[index]['nz'] = point.normal[2]

            for scalar_key in point.scalars:
                vertex_output_array[index][scalar_key] = point.scalars[scalar_key]

            if with_measurements:
                measurements = []
                for measurement in point.measurements:
                    measurements += measurement.to_list()
                vertex_output_array[index]['measurements'] = measurements

        description = PlyElement.describe(
            vertex_output_array,
            name='vertex',
            # possible values for val_types
            # ['int8', 'i1', 'char', 'uint8', 'u1', 'uchar', 'b1',
            # 'int16', 'i2', 'short', 'uint16', 'u2', 'ushort',
            # 'int32', 'i4', 'int', 'uint32', 'u4', 'uint',
            # 'float32', 'f4', 'float', 'float64', 'f8', 'double']
            val_types={'measurements':'float'})

        return description

    @staticmethod
    def __faces_to_ply_face_element(face_list, property_type_list):

        face_output_array = np.empty(len(face_list), dtype=property_type_list)
        for index, face in enumerate(face_list):

            # property_type_list defines keyword 'vertex_indices'
            row = np.empty(1, dtype=property_type_list)
            # We don't use face colors, the color of the faces is defined using the vertex colors!
            row['vertex_indices'] = face.vertex_indices      # face.vertex_indices is a np.array
            face_output_array[index] = row

        output_ply_data_face_element = PlyElement.describe(face_output_array, 'face')

        return output_ply_data_face_element

    @staticmethod
    def __cameras_2_ply_vertex_element(camera_list, property_type_list):

        camera_output_array = np.empty(len(camera_list), dtype=property_type_list)

        for index, camera in enumerate(camera_list):

            row = np.empty(1, dtype=property_type_list)
            row['x'] = camera.get_camera_center()[0]
            row['y'] = camera.get_camera_center()[1]
            row['z'] = camera.get_camera_center()[2]

            row['red'] = camera.color[0]
            row['green'] = camera.color[1]
            row['blue'] = camera.color[2]

            row['nx'] = camera.normal[0]
            row['ny'] = camera.normal[1]
            row['nz'] = camera.normal[2]

            camera_output_array[index] = row

        return PlyElement.describe(camera_output_array, 'vertex')

    @staticmethod
    def parse_ply_file(path_to_file):
        print('Parse PLY File: ...')
        print('path_to_file', path_to_file)
        ply_data = PlyData.read(path_to_file)

        vertices, _, _ = PLYFileHandler.__ply_data_vertices_to_vetex_list(ply_data)
        print('Parse PLY File: Done')
        return vertices

    @staticmethod
    def write_ply_file_from_vertex_mat(output_path_to_file,
                                       vertex_mat):
        vertices = []
        for entry in vertex_mat:
            vertices.append(Point(coord=entry))
        PLYFileHandler.write_ply_file(output_path_to_file, vertices)

    @staticmethod
    def build_type_list(vertices, with_colors, with_normals, with_measurements):
        ply_data_vertex_data_dtype_list = [('x', '<f4'), ('y', '<f4'), ('z', '<f4')]
        if with_colors:
            ply_data_vertex_data_dtype_list += [('red', 'u1'), ('green', 'u1'), ('blue', 'u1')]
        if with_normals:
            ply_data_vertex_data_dtype_list += [('nx', '<f4'), ('ny', '<f4'), ('nz', '<f4')]

        if len(vertices) > 0:
            for scalar_keys in vertices[0].scalars:
                ply_data_vertex_data_dtype_list += [(scalar_keys, '<f4')]

            if with_measurements:
                # since the length of the measurements varies, we use an object data type here
                ply_data_vertex_data_dtype_list += [('measurements', object)]
        return ply_data_vertex_data_dtype_list

    @staticmethod
    def write_ply_file(output_path_to_file,
                       vertices,
                       with_colors=True,
                       with_normals=False,
                       faces=None,
                       plain_text_output=True,
                       with_measurements=False):

        print('write_ply_file: ' + output_path_to_file)

        ply_data_vertex_data_dtype_list = PLYFileHandler.build_type_list(
            vertices, with_colors, with_normals, with_measurements)

        print('ply_data_vertex_data_dtype_list', ply_data_vertex_data_dtype_list)

        # PRINTING output_ply_data_vertex_element SHOWS ONLY THE HEADER
        output_ply_data_vertex_element = PLYFileHandler.__vertices_to_ply_vertex_element(
            vertices, ply_data_vertex_data_dtype_list)

        if faces is None or len(faces) == 0:
            print('Write File With Vertices Only (no faces)')
            output_data = PlyData([output_ply_data_vertex_element], text=plain_text_output)
        else:
            print('Write File With Faces')
            print('Number faces' + str(len(faces)))

            ply_data_face_data_type = [('vertex_indices', 'i4', (3,))]

            # we do not define colors for faces,
            # since we use the vertex colors to colorize the face

            output_ply_data_face_element = PLYFileHandler.__faces_to_ply_face_element(
                faces, ply_data_face_data_type)
            output_data = PlyData(
                [output_ply_data_vertex_element, output_ply_data_face_element],
                text=plain_text_output)

        output_data.write(output_path_to_file)

