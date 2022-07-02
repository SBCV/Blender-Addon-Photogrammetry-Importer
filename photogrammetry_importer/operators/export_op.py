import bpy
import os
import numpy as np
from photogrammetry_importer.types.point import Point
from photogrammetry_importer.types.camera import Camera
from photogrammetry_importer.importers.camera_utility import (
    invert_y_and_z_axis,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report


class ExportOperator(bpy.types.Operator):
    """Abstract basic export operator."""

    def _get_calibration_mat(self, blender_camera):
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

    def _get_computer_vision_camera_matrix(self, blender_camera):

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

        # Important: Blender uses a camera coordinate frame system, which looks
        # down the negative z-axis. This differs from the camera coordinate
        # systems used by most SfM tools/frameworks. Thus, rotate the camera
        # rotation matrix by 180 degrees (i.e. invert the y and z axis).
        gt_camera_rotation = invert_y_and_z_axis(gt_camera_rotation)
        gt_camera_rotation_inverse = gt_camera_rotation.T

        rotated_camera_matrix_around_x_by_180 = camera_matrix.copy()
        rotated_camera_matrix_around_x_by_180[
            0:3, 0:3
        ] = gt_camera_rotation_inverse
        return rotated_camera_matrix_around_x_by_180

    def get_selected_cameras_and_vertices_of_meshes(self, odp):
        """Get selected cameras and vertices."""
        log_report(
            "INFO", "get_selected_cameras_and_vertices_of_meshes: ...", self
        )
        cameras = []
        points = []

        point_index = 0
        camera_index = 0
        for obj in bpy.context.selected_objects:
            if obj.type == "CAMERA":
                obj_name = str(obj.name).replace(" ", "_")
                log_report("INFO", "obj_name: " + obj_name, self)
                calibration_mat = self._get_calibration_mat(obj)
                # log_report('INFO', 'calibration_mat:', self)
                # log_report('INFO', str(calibration_mat), self)

                camera_matrix_computer_vision = (
                    self._get_computer_vision_camera_matrix(obj)
                )

                cam = Camera()
                cam.id = camera_index
                cam.set_relative_fp(obj_name, Camera.IMAGE_FP_TYPE_NAME)
                cam.image_dp = odp
                cam.width = bpy.context.scene.render.resolution_x
                cam.height = bpy.context.scene.render.resolution_y

                cam.set_calibration(calibration_mat, radial_distortion=0)
                cam.set_4x4_cam_to_world_mat(camera_matrix_computer_vision)
                cameras.append(cam)
                camera_index += 1

            else:
                obj_points = []
                # Option 1: Mesh Object
                if obj.data is not None:
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
                # Option 2: Empty with OpenGL information
                elif (
                    "particle_coords" in obj
                    and "particle_colors" in obj
                    and "point_size" in obj
                ):
                    coords = obj["particle_coords"]
                    colors = obj["particle_colors"]
                    for coord, color in zip(coords, colors):
                        coord_world = coord
                        scaled_color = [round(value * 255) for value in color]
                        obj_points.append(
                            Point(
                                coord=coord_world,
                                color=scaled_color[:3],
                                id=point_index,
                                scalars=[],
                            )
                        )
                        point_index += 1
                    points += obj_points
        log_report(
            "INFO",
            "get_selected_cameras_and_vertices_of_meshes: Done",
            self,
        )
        return cameras, points

    def execute(self, context):
        """Abstract method that must be overriden by a subclass."""
        # Pythons ABC class and Blender's operators do not work well
        # together in the context of multiple inheritance.
        raise NotImplementedError("Subclasses must override this function!")
