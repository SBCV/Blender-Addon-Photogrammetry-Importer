import bpy
from photogrammetry_importer.types.point import Point
from photogrammetry_importer.importers.camera_utility import (
    get_computer_vision_camera,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report


class ExportOperator(bpy.types.Operator):
    """Abstract basic export operator."""

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
                cam = get_computer_vision_camera(
                    obj, obj_name, odp, camera_index
                )
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
