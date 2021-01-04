import os
import bpy
from bpy_extras.io_utils import ExportHelper
from photogrammetry_importer.blender_utility.retrieval_utility import (
    get_selected_camera,
    get_scene_animation_indices,
    get_object_animation_indices,
)
from photogrammetry_importer.opengl.draw_manager import DrawManager
from photogrammetry_importer.opengl.utility import render_opengl_image
from photogrammetry_importer.blender_utility.logging_utility import log_report
from photogrammetry_importer.blender_utility.image_utility import (
    save_image_to_disk,
)


class SaveOpenGLRenderImageOperator(bpy.types.Operator):
    """An Operator to save a rendering of the point cloud as Blender image."""

    bl_idname = "photogrammetry_importer.save_opengl_render_image"
    bl_label = "Save as Blender Image"
    bl_description = "Use a single camera to render the point cloud."

    @classmethod
    def poll(cls, context):
        """Return the availability status of the operator."""
        cam = get_selected_camera()
        return cam is not None

    def execute(self, context):
        """Render the point cloud and save the result as image in Blender."""
        log_report("INFO", "Save opengl render as image: ...", self)
        save_point_size = context.scene.opengl_panel_settings.save_point_size
        cam = get_selected_camera()
        image_name = "OpenGL Render"
        log_report("INFO", "image_name: " + image_name, self)
        draw_manager = DrawManager.get_singleton()
        coords, colors = draw_manager.get_coords_and_colors(visible_only=True)
        render_opengl_image(image_name, cam, coords, colors, save_point_size)
        log_report("INFO", "Save opengl render as image: Done", self)
        return {"FINISHED"}


class ExportOpenGLRenderImageOperator(bpy.types.Operator, ExportHelper):
    """An Operator to save a rendering of the point cloud to disk."""

    bl_idname = "photogrammetry_importer.export_opengl_render_image"
    bl_label = "Export Point Cloud Rendering as Image"
    bl_description = "Use a single camera to render the point cloud."

    # Hide the porperty by using a normal string instad of a string property
    filename_ext = ""

    @classmethod
    def poll(cls, context):
        """Return the availability status of the operator."""
        cam = get_selected_camera()
        return cam is not None

    def execute(self, context):
        """Render the point cloud and export the result as image."""
        log_report("INFO", "Export opengl render as image: ...", self)
        scene = context.scene
        save_point_size = scene.opengl_panel_settings.save_point_size

        filename_ext = scene.opengl_panel_settings.render_file_format
        ofp = self.filepath + "." + filename_ext
        log_report("INFO", "Output File Path: " + ofp, self)

        # Used to cache the results
        image_name = "OpenGL Export"

        cam = get_selected_camera()
        draw_manager = DrawManager.get_singleton()
        coords, colors = draw_manager.get_coords_and_colors(visible_only=True)
        render_opengl_image(image_name, cam, coords, colors, save_point_size)

        save_alpha = scene.opengl_panel_settings.save_alpha
        save_image_to_disk(image_name, ofp, save_alpha)

        log_report("INFO", "Save opengl render as image: Done", self)
        return {"FINISHED"}


class ExportOpenGLRenderAnimationOperator(bpy.types.Operator, ExportHelper):
    """An Operator to save multiple renderings of the point cloud to disk."""

    bl_idname = "photogrammetry_importer.export_opengl_render_animation"
    bl_label = "Export Point Cloud Renderings as Image Sequence"
    bl_description = "Use an animated camera to render the point cloud."

    # Hide the porperty by using a normal string instad of a string property
    filename_ext = ""

    @classmethod
    def poll(cls, context):
        """Return the availability status of the operator."""
        cam = get_selected_camera()
        return cam is not None and cam.animation_data is not None

    def execute(self, context):
        """Render the point cloud and export the result as image sequence."""
        log_report(
            "INFO", "Export opengl render as image sequencemation: ...", self
        )
        scene = context.scene
        save_point_size = scene.opengl_panel_settings.save_point_size

        # The export helper stores the path in self.filepath (even if it is a
        # directory)
        output_dp = self.filepath
        log_report("INFO", "Output Directory Path: " + str(output_dp), self)

        if not os.path.isdir(output_dp):
            os.mkdir(output_dp)

        # Used to cache the results
        image_name = "OpenGL Export"
        ext = "." + scene.opengl_panel_settings.render_file_format
        save_alpha = scene.opengl_panel_settings.save_alpha
        selected_cam = get_selected_camera()
        use_camera_keyframes = (
            scene.opengl_panel_settings.use_camera_keyframes_for_rendering
        )
        if (
            use_camera_keyframes
            and selected_cam is not None
            and selected_cam.animation_data is not None
        ):
            animation_indices = get_object_animation_indices(selected_cam)
        else:
            animation_indices = get_scene_animation_indices()

        draw_manager = DrawManager.get_singleton()
        coords, colors = draw_manager.get_coords_and_colors(visible_only=True)
        for idx in animation_indices:
            bpy.context.scene.frame_set(idx)
            current_frame_fn = str(idx).zfill(5) + ext
            current_frame_fp = os.path.join(output_dp, current_frame_fn)

            log_report(
                "INFO", "Output File Path: " + str(current_frame_fp), self
            )
            render_opengl_image(
                image_name, selected_cam, coords, colors, save_point_size
            )
            save_image_to_disk(image_name, current_frame_fp, save_alpha)

        log_report("INFO", "Save opengl render as animation: Done", self)
        return {"FINISHED"}
