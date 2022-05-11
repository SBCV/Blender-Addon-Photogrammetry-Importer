import os
import bpy
from bpy_extras.io_utils import ExportHelper
from photogrammetry_importer.blender_utility.retrieval_utility import (
    get_selected_camera,
    get_scene_animation_indices,
    get_object_animation_indices,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report


def _update_ui(context):
    for area in context.screen.areas:
        area.tag_redraw()


class ExportScreenshotImageOperator(bpy.types.Operator, ExportHelper):
    """An Operator to export a screenshot (of the 3D view)."""

    bl_idname = "photogrammetry_importer.export_screenshot"
    bl_label = "Export Screenshot"
    bl_description = "Create a screenshot (using a camera perspective)."

    # Hide the porperty by using a normal string instad of a string property
    filename_ext = ""

    @classmethod
    def poll(cls, context):
        """Return the availability status of the operator."""
        return True

    def execute(self, context):
        """Export a screenshot (of the 3D view)."""
        log_report("INFO", "Export screenshot: ...", self)

        panel_settings = context.scene.opengl_panel_settings
        filename_ext = panel_settings.screenshot_file_format
        ofp = self.filepath + "." + filename_ext

        # Get panel settings
        full_screenshot = not panel_settings.only_3d_view
        use_camera_perspective = panel_settings.use_camera_perspective

        # Cache previous settings
        previous_cam = bpy.context.scene.camera
        area_3d = next(
            area for area in bpy.context.screen.areas if area.type == "VIEW_3D"
        )
        previous_perspective = area_3d.spaces[0].region_3d.view_perspective

        # Create Screenshot
        selected_cam = get_selected_camera()
        if use_camera_perspective and selected_cam is not None:
            bpy.context.scene.camera = selected_cam
            area_3d.spaces[0].region_3d.view_perspective = "CAMERA"
            _update_ui(context)
        if full_screenshot:
            bpy.ops.screen.screenshot(filepath=ofp, check_existing=False)
        else:
            bpy.ops.screen.screenshot_area(filepath=ofp, check_existing=False)

        # Restore previous settings
        area_3d.spaces[0].region_3d.view_perspective = previous_perspective
        bpy.context.scene.camera = previous_cam

        log_report("INFO", "Export screenshot: Done", self)
        return {"FINISHED"}


class ExportScreenshotAnimationOperator(bpy.types.Operator, ExportHelper):
    """An Operator to export a screenshot sequence (of the 3D view)."""

    bl_idname = "photogrammetry_importer.export_screenshot_sequence"
    bl_label = "Export Screenshot Sequence"
    bl_description = "Use the animation data to create a screenshot sequence."

    # Hide the porperty by using a normal string instad of a string property
    filename_ext = ""

    @classmethod
    def poll(cls, context):
        """Return the availability status of the operator."""
        return True

    def execute(self, context):
        """Export a sequence of screenshots using the selected camera."""
        log_report("INFO", "Export screenshot sequence: ...", self)

        scene = context.scene
        panel_settings = scene.opengl_panel_settings
        filename_ext = panel_settings.screenshot_file_format
        output_dp = self.filepath

        # Get panel settings
        full_screenshot = not panel_settings.only_3d_view
        use_camera_perspective = panel_settings.use_camera_perspective

        # Cache previous settings
        previous_cam = bpy.context.scene.camera
        area_3d = next(
            area for area in bpy.context.screen.areas if area.type == "VIEW_3D"
        )
        previous_perspective = area_3d.spaces[0].region_3d.view_perspective

        # Create Screenshots
        selected_cam = get_selected_camera()
        use_camera_keyframes = (
            scene.opengl_panel_settings.use_camera_keyframes_for_screenshots
        )
        if (
            use_camera_keyframes
            and selected_cam is not None
            and selected_cam.animation_data is not None
        ):
            animation_indices = get_object_animation_indices(selected_cam)
        else:
            animation_indices = get_scene_animation_indices()
        # called_view_camera_op = False
        if use_camera_perspective and selected_cam is not None:
            bpy.context.scene.camera = selected_cam
            # Option 1
            area_3d.spaces[0].region_3d.view_perspective = "CAMERA"
            # Option 2
            # https://docs.blender.org/api/current/bpy.ops.view3d.html#bpy.ops.view3d.view_camera
            # if area_3d.spaces[0].region_3d.view_perspective != "CAMERA":
            #     bpy.ops.view3d.view_camera()
            #     called_view_camera_op = True
        for idx in animation_indices:
            bpy.context.scene.frame_set(idx)
            _update_ui(context)

            current_frame_fn = str(idx).zfill(5) + "." + filename_ext
            current_frame_fp = os.path.join(output_dp, current_frame_fn)
            log_report(
                "INFO", "Output File Path: " + str(current_frame_fp), self
            )
            if full_screenshot:
                bpy.ops.screen.screenshot(
                    filepath=current_frame_fp,
                    check_existing=False,
                )
            else:
                bpy.ops.screen.screenshot_area(
                    filepath=current_frame_fp,
                    check_existing=False,
                )

        # Restore previous settings
        # Option 1
        area_3d.spaces[0].region_3d.view_perspective = previous_perspective
        # Option 2
        # if called_view_camera_op:
        #     bpy.ops.view3d.view_camera()

        bpy.context.scene.camera = previous_cam
        log_report("INFO", "Export screenshot sequence: Done", self)
        return {"FINISHED"}
