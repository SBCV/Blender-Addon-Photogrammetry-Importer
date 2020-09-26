import bpy
import os
import numpy as np
from photogrammetry_importer.types.point import Point
from photogrammetry_importer.types.camera import Camera
from photogrammetry_importer.utility.blender_logging_utility import log_report


class ExportOperator(bpy.types.Operator):
    def invert_y_and_z_axis(self, input_matrix_or_vector):
        """
        VisualSFM and Blender use coordinate systems, which differ in the y and z coordinate
        This Function inverts the y and the z coordinates in the corresponding matrix / vector entries
        Iinvert y and z axis <==> rotation by 180 degree around the x axis
        """
        output_matrix_or_vector = input_matrix_or_vector.copy()
        output_matrix_or_vector[1] = -output_matrix_or_vector[1]
        output_matrix_or_vector[2] = -output_matrix_or_vector[2]
        return output_matrix_or_vector

    def get_calibration_mat(self, blender_camera):
        log_report("INFO", "get_calibration_mat: ...", self)
        scene = bpy.context.scene
        render_resolution_width = scene.render.resolution_x
        render_resolution_height = scene.render.resolution_y
        focal_length_in_mm = float(blender_camera.data.lens)
        sensor_width_in_mm = float(blender_camera.data.sensor_width)
        focal_length_in_pixel = (
            float(max(scene.render.resolution_x, scene.render.resolution_y))
            * focal_length_in_mm
            / sensor_width_in_mm
        )

        max_extent = max(render_resolution_width, render_resolution_height)
        p_x = (
            render_resolution_width / 2.0
            - blender_camera.data.shift_x * max_extent
        )
        p_y = (
            render_resolution_height / 2.0
            - blender_camera.data.shift_y * max_extent
        )

        calibration_mat = Camera.compute_calibration_mat(
            focal_length_in_pixel, cx=p_x, cy=p_y
        )

        log_report(
            "INFO",
            "render_resolution_width: " + str(render_resolution_width),
            self,
        )
        log_report(
            "INFO",
            "render_resolution_height: " + str(render_resolution_height),
            self,
        )
        log_report(
            "INFO",
            "focal_length_in_pixel: " + str(focal_length_in_pixel),
            self,
        )

        log_report("INFO", "get_calibration_mat: Done", self)
        return calibration_mat

    def get_computer_vision_camera_matrix(self, blender_camera):

        """
        Blender and Computer Vision Camera Coordinate Frame Systems (like VisualSfM, Bundler)
        differ by their y and z axis
        :param blender_camera:
        :return:
        """

        # Only if the objects have a scale of 1, the 3x3 part
        # of the corresponding matrix_world contains a pure rotation.
        # Otherwise, it also contains scale or shear information
        if not np.allclose(tuple(blender_camera.scale), (1, 1, 1)):
            log_report(
                "ERROR",
                "blender_camera.scale: " + str(blender_camera.scale),
                self,
            )
            assert False

        camera_matrix = np.array(blender_camera.matrix_world)
        gt_camera_rotation_inverse = camera_matrix.copy()[0:3, 0:3]
        gt_camera_rotation = gt_camera_rotation_inverse.T

        # Important: Blender uses a camera coordinate frame system, which looks down the negative z-axis.
        # This differs from the camera coordinate systems used by most SfM tools/frameworks.
        # Thus, rotate the camera rotation matrix by 180 degrees (i.e. invert the y and z axis).
        gt_camera_rotation = self.invert_y_and_z_axis(gt_camera_rotation)
        gt_camera_rotation_inverse = gt_camera_rotation.T

        rotated_camera_matrix_around_x_by_180 = camera_matrix.copy()
        rotated_camera_matrix_around_x_by_180[
            0:3, 0:3
        ] = gt_camera_rotation_inverse
        return rotated_camera_matrix_around_x_by_180

    def export_selected_cameras_and_vertices_of_meshes(self, odp):
        log_report(
            "INFO", "export_selected_cameras_and_vertices_of_meshes: ...", self
        )
        cameras = []
        points = []

        point_index = 0
        camera_index = 0
        for obj in bpy.context.selected_objects:
            if obj.type == "CAMERA":
                log_report("INFO", "obj.name: " + str(obj.name), self)
                calibration_mat = self.get_calibration_mat(obj)
                # log_report('INFO', 'calibration_mat:', self)
                # log_report('INFO', str(calibration_mat), self)

                camera_matrix_computer_vision = (
                    self.get_computer_vision_camera_matrix(obj)
                )

                cam = Camera()
                cam.id = camera_index
                cam.set_relative_fp(str(obj.name), Camera.IMAGE_FP_TYPE_NAME)
                cam.image_dp = odp
                cam.width = bpy.context.scene.render.resolution_x
                cam.height = bpy.context.scene.render.resolution_y

                cam.set_calibration(calibration_mat, radial_distortion=0)
                cam.set_4x4_cam_to_world_mat(camera_matrix_computer_vision)
                cameras.append(cam)
                camera_index += 1

            else:
                if obj.data is not None:
                    obj_points = []
                    for vert in obj.data.vertices:
                        coord_world = obj.matrix_world @ vert.co
                        obj_points.append(
                            Point(
                                coord=coord_world,
                                color=[0, 255, 0],
                                id=point_index,
                                scalars=[],
                            )
                        )

                        point_index += 1
                    points += obj_points
        log_report(
            "INFO",
            "export_selected_cameras_and_vertices_of_meshes: Done",
            self,
        )
        return cameras, points
