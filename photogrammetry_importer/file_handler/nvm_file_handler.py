
import os
from collections import defaultdict
import numpy as np

try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None

from photogrammetry_importer.camera import Camera
from collections import namedtuple

Measurement = namedtuple('Measurement', ['image_index', 'feature_index', 'x', 'y'])
Point = namedtuple('Point', ['coord', 'color', 'measurements', 'id', 'scalars']) 


class NVMFileHandler(object):

    @staticmethod
    def parse_camera_image_files(cameras, path_to_images, default_width, default_height, op):
        op.report({'INFO'}, 'parse_camera_image_files: ' + path_to_images)
        success = True 
        for camera in cameras:
            image_path = os.path.join(path_to_images, camera.file_name)
            if PILImage is not None and os.path.isfile(image_path):
                # this does NOT load the data into memory -> should be fast!
                image = PILImage.open(image_path)
                camera.width, camera.height = image.size
            elif default_width > 0 and default_height > 0:
                camera.width = default_width
                camera.height = default_height
                op.report({'WARNING'}, 'Set width and height to provided default values! (' + str(default_width) + ', ' + str(default_height) + ')')
            else:
                if PILImage is None:
                    op.report({'ERROR'}, 'PIL/PILLOW is not installed. Can not read image from disc to get image size.')
                else:
                    op.report({'ERROR'}, 'Corresponding image not found at: ' + image_path)
                op.report({'ERROR'}, 'Invalid default values provided for width (' + str(default_width) + ') and height (' + str(default_height) + ')')
                if PILImage is None:
                    op.report({'ERROR'}, 'Adjust the default width/height values to import the NVM file.')
                else:
                    op.report({'ERROR'}, 'Adjust the image path or the default width/height values to import the NVM file.')
                success = False
                break

        op.report({'INFO'}, 'parse_camera_image_files: Done')
        return cameras, success

    # Check the LoadNVM function in util.h of Multicore bundle adjustment code for more details.
    # http://grail.cs.washington.edu/projects/mcba/
    # pba/src/pba/util.h


    @staticmethod
    def _parse_cameras(input_file, num_cameras, camera_calibration_matrix, op):

        """
        VisualSFM CAMERA coordinate system is the standard CAMERA coordinate system in computer vision (not the same
        as in computer graphics like in bundler, blender, etc.)
        That means
              the y axis in the image is pointing downwards (not upwards)
              the camera is looking along the positive z axis (points in front of the camera show a positive z value)

        The camera coordinate system in computer vision VISUALSFM uses camera matrices,
        which are rotated around the x axis by 180 degree
        i.e. the y and z axis of the CAMERA MATRICES are inverted
        therefore, the y and z axis of the TRANSLATION VECTOR are also inverted
        """
        # op.report({'INFO'}, '_parse_cameras: ...')
        cameras = []

        for i in range(num_cameras):
            line = input_file.readline()

            # Read the camera section
            # From the docs:
            # <Camera> = <File name> <focal length> <quaternion WXYZ> <camera center> <radial distortion> 0
            line_values = line.split()
            file_name = os.path.basename(line_values[0])
            focal_length = float(line_values[1])

            quaternion_w = float(line_values[2])
            quaternion_x = float(line_values[3])
            quaternion_y = float(line_values[4])
            quaternion_z = float(line_values[5])
            quaternion = np.array([quaternion_w, quaternion_x, quaternion_y, quaternion_z], dtype=float)

            camera_center_x = float(line_values[6])
            camera_center_y = float(line_values[7])
            camera_center_z = float(line_values[8])
            center_vec = np.array([camera_center_x, camera_center_y, camera_center_z])

            radial_distortion = float(line_values[9])

            # TODO radial_distortion in camera_calibration_matrix
            if camera_calibration_matrix is None:
                camera_calibration_matrix = np.array([[focal_length, 0, 0],
                                          [0, focal_length, 0],
                                          [0, 0, 1]])

            zero_value = float(line_values[10])
            assert(zero_value == 0)

            current_camera = Camera()
            # Setting the quaternion also sets the rotation matrix
            current_camera.set_quaternion(quaternion)

            # Set the camera center after rotation
            # COMMENT FROM PBA CODE:
            #   older format for compability
            #   camera_data[i].SetQuaternionRotation(q); // quaternion from the file
            #   camera_data[i].SetCameraCenterAfterRotation(c); // camera center from the file
            current_camera._center = center_vec

            # set the camera view direction as normal w.r.t world coordinates
            cam_view_vec_cam_coord = np.array([0, 0, 1]).T
            cam_rotation_matrix_inv = np.linalg.inv(current_camera.get_rotation_mat())
            cam_view_vec_world_coord = cam_rotation_matrix_inv.dot(cam_view_vec_cam_coord)
            current_camera.normal = cam_view_vec_world_coord

            translation_vec = NVMFileHandler.compute_camera_coordinate_system_translation_vector(center_vec, current_camera.get_rotation_mat())
            current_camera._translation_vec = translation_vec

            current_camera.set_calibration_mat(camera_calibration_matrix)
            # op.report({'INFO'}, 'Calibration mat:')
            # op.report({'INFO'}, str(camera_calibration_matrix))
            current_camera.file_name = file_name
            current_camera.id = i
            cameras.append(current_camera)
        # op.report({'INFO'}, '_parse_cameras: Done')
        return cameras

    @staticmethod
    def _parse_nvm_points(input_file, num_3D_points):

        points = []
        for point_index in range(num_3D_points):
            # From the VSFM docs:
            # <Point>  = <XYZ> <RGB> <number of measurements> <List of Measurements>
            point_line = input_file.readline()
            point_line_elements = (point_line.rstrip()).split()
            xyz_vec = list(map(float, point_line_elements[0:3]))
            rgb_vec = list(map(int, point_line_elements[3:6]))
            number_measurements = int(point_line_elements[6])
            measurements = point_line_elements[7:]

            current_point_measurement = []
            for measurement_index in range(0, number_measurements):
                # From the VSFM docs:
                # <Measurement> = <Image index> <Feature Index> <xy>
                current_measurement = measurements[measurement_index*4:(measurement_index+1)*4]
                image_index = int(current_measurement[0])
                feature_index = int(current_measurement[1])
                x_in_nvm_file = float(current_measurement[2])
                y_in_nvm_file = float(current_measurement[3])
                current_point_measurement.append(
                    Measurement(image_index, feature_index, x_in_nvm_file, y_in_nvm_file))
            current_point = Point(coord=xyz_vec, color=rgb_vec, measurements = current_point_measurement, id=point_index, scalars=None)
            points.append(current_point)

        return points

    @staticmethod
    def parse_fixed_calibration(line, op):
        
        line_elements = line.split()
        if len(line_elements) == 1:
            assert line.startswith('NVM_V3')
            calib_mat = None
        elif len(line_elements) == 7:
            _,_, fx, cx, fy, cy, r = line_elements
            calib_mat = np.array(
                [[float(fx), 0, float(cx)],
                 [0, float(fy), float(cy)],
                 [0, 0, 1]])
        else:
            assert False
        if calib_mat is not None:
            op.report({'INFO'}, 'Found Fixed Calibration in NVM File.')
            # op.report({'INFO'}, 'Fixed calibration mat:')
            # op.report({'INFO'}, str(calib_mat))
        return calib_mat

    @staticmethod
    def parse_nvm_file(input_visual_fsm_file_name, op):

        op.report({'INFO'}, 'Parse NVM file: ' + input_visual_fsm_file_name)
        input_file = open(input_visual_fsm_file_name, 'r')
        # Documentation of *.NVM data format
        # http://ccwu.me/vsfm/doc.html#nvm

        # In a simple case there is only one model

        # Each reconstructed <model> contains the following
        # <Number of cameras>   <List of cameras>
        # <Number of 3D points> <List of points>

        # Read the first two lines (fixed)
        current_line = (input_file.readline()).rstrip()
        calibration_matrix = NVMFileHandler.parse_fixed_calibration(current_line, op)
        current_line = (input_file.readline()).rstrip()
        assert current_line == ''

        amount_cameras = int((input_file.readline()).rstrip())
        print('Amount Cameras (Images in NVM file): ' + str(amount_cameras))

        cameras = NVMFileHandler._parse_cameras(input_file, amount_cameras, calibration_matrix, op)
        current_line = (input_file.readline()).rstrip()
        assert current_line == ''
        current_line = (input_file.readline()).rstrip()
        if current_line.isdigit():
            amount_points = int(current_line)
            print('Amount Sparse Points (Points in NVM file): ' + str(amount_points))
            points = NVMFileHandler._parse_nvm_points(input_file, amount_points)
        else:
            points = []

        op.report({'INFO'}, 'Parse NVM file: Done')
        return cameras, points

    @staticmethod
    def create_nvm_first_line(cameras, op):

        op.report({'INFO'}, 'create_nvm_first_line: ...')
        # The first line can be either
        #   'NVM_V3'
        # or
        #   'NVM_V3 FixedK fx cx fy cy r'

        calib_mat = cameras[0].get_calibration_mat()
        op.report({'INFO'}, 'calib_mat: ' + str(calib_mat))
        # radial_dist = None
        # if cameras[0].has_radial_distortion():
        #     radial_dist = cameras[0].has_radial_distortion()

        fixed_calibration = True
        for cam in cameras:
            op.report({'INFO'}, 'cam.get_calibration_mat(): ' + str(cam.get_calibration_mat()))
            if not np.allclose(cam.get_calibration_mat(), calib_mat):
                op.report({'INFO'}, 'calib_mat: ' + str(calib_mat))
                fixed_calibration = False
                break
        op.report({'INFO'}, 'fixed_calibration: ' + str(fixed_calibration))
        if fixed_calibration:
            fl = 'NVM_V3 FixedK'
            fl += ' ' + str(calib_mat[0][0])
            fl += ' ' + str(calib_mat[0][2])
            fl += ' ' + str(calib_mat[1][1])
            fl += ' ' + str(calib_mat[1][2])
            fl += ' ' + str(0)      # TODO Radial distortion
        else:
            fl = 'NVM_V3'
        op.report({'INFO'}, 'fl: ' + fl)
        op.report({'INFO'}, 'create_nvm_first_line: Done')
        return fl

    @staticmethod
    def nvm_line(content):
        return content + ' ' + os.linesep

    @staticmethod
    def write_nvm_file(op, output_nvm_file_name, cameras, points):

        op.report({'INFO'}, 'Write NVM file: ' + output_nvm_file_name)

        nvm_content = []
        nvm_content.append(NVMFileHandler.nvm_line(
            NVMFileHandler.create_nvm_first_line(cameras, op)))
        nvm_content.append(NVMFileHandler.nvm_line(''))
        amount_cameras = len(cameras)
        nvm_content.append(NVMFileHandler.nvm_line(str(amount_cameras)))
        print('Amount Cameras (Images in NVM file):', amount_cameras)

        # Write the camera section
        # From the VSFM docs:
        # <Camera> = <File name> <focal length> <quaternion WXYZ> <camera center> <radial distortion> 0

        for camera in cameras:

            #quaternion = TransformationFunctions.rotation_matrix_to_quaternion(camera.rotation_mat)
            quaternion = camera.get_quaternion()

            current_line = camera.file_name
            current_line += '\t' + str(camera.get_calibration_mat()[0][0])
            current_line += ' ' + ' '.join(list(map(str, quaternion)))
            current_line += ' ' + ' '.join(list(map(str, camera.get_camera_center())))
            current_line += ' ' + '0'   # TODO USE RADIAL DISTORTION
            current_line += ' ' + '0'
            nvm_content.append(current_line + ' ' + os.linesep)

        nvm_content.append(' ' + os.linesep)
        number_points = len(points)
        nvm_content.append(str(number_points) + ' ' + os.linesep)
        print('Found ' + str(number_points) + ' object points')

        for point in points:
            # From the VSFM docs:
            # <Point>  = <XYZ> <RGB> <number of measurements> <List of Measurements>
            current_line = ' '.join(list(map(str, point.coord)))
            current_line += ' ' + ' '.join(list(map(str, point.color)))
            current_line += ' ' + str(len(point.measurements))
            for measurement in point.measurements:
                current_line += ' ' + str(measurement)

            nvm_content.append(current_line + ' ' + os.linesep)

        nvm_content.append(' ' + os.linesep)
        nvm_content.append(' ' + os.linesep)
        nvm_content.append(' ' + os.linesep)
        nvm_content.append('0' + os.linesep)
        nvm_content.append(' ' + os.linesep)
        nvm_content.append('#the last part of NVM file points to the PLY files ' + os.linesep)
        nvm_content.append('#the first number is the number of associated PLY files ' + os.linesep)
        nvm_content.append('#each following number gives a model-index that has PLY ' + os.linesep)
        nvm_content.append('0' + os.linesep)

        output_file = open(output_nvm_file_name, 'wb')
        output_file.writelines([item.encode() for item in nvm_content])

        op.report({'INFO'}, 'Write NVM file: Done')

    @staticmethod
    def compute_camera_coordinate_system_translation_vector(c, R):

        """
        x_cam = R (X - C) = RX - RC == RX + t
        <=> t = -RC
        """
        t = np.zeros(3, dtype=float)
        for j in range(0, 3):
            t[j] = -float(R[j][0] * c[0] + R[j][1] * c[1] + R[j][2] * c[2])
        return t