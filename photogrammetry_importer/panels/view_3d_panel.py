import os
import numpy as np
import bpy

from photogrammetry_importer.types.point import Point

from photogrammetry_importer.blender_utility.image_utility import (
    save_image_to_disk,
)
from photogrammetry_importer.opengl.utility import render_opengl_image

from photogrammetry_importer.opengl.draw_manager import DrawManager

from photogrammetry_importer.blender_utility.logging_utility import log_report

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    PointerProperty,
)

from bpy_extras.io_utils import ExportHelper


def _get_selected_camera():
    selection_names = [obj.name for obj in bpy.context.selected_objects]
    if len(selection_names) == 0:
        return None
    selected_obj = bpy.data.objects[selection_names[0]]
    if selected_obj.type == "CAMERA":
        return selected_obj
    else:
        return None


class OpenGLPanelSettings(bpy.types.PropertyGroup):
    """Class that defines the properties of the OpenGL panel in the 3D view."""

    viz_point_size: IntProperty(
        name="Point Size",
        description="OpenGL visualization point size.",
        default=10,
    )
    save_point_size: IntProperty(
        name="Point Size", description="OpenGL point size.", default=10
    )
    file_format: StringProperty(
        name="File format",
        description="File format of the exported file(s)",
        default="png",
    )
    save_alpha: BoolProperty(
        name="Save Alpha Values",
        description="Save alpha values (if possible) to disk.",
        default=True,
    )
    use_camera_keyframes: BoolProperty(
        name="Use Camera Keyframes",
        description="Use the Camera Keyframes instead of Animation Frames.",
        default=True,
    )


class OpenGLPanel(bpy.types.Panel):
    """Class that defines the OpenGL panel in the 3D view."""

    bl_label = "OpenGL Panel"
    bl_idname = "EXPORT_OPENGL_PT_render_point_cloud"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PhotogrammetryImporter"

    @classmethod
    def poll(cls, context):
        """Return the availability status of the panel."""
        return True

    @classmethod
    def register(cls):
        """Register properties and operators corresponding to this panel."""

        bpy.utils.register_class(OpenGLPanelSettings)
        bpy.types.Scene.opengl_panel_settings = PointerProperty(
            type=OpenGLPanelSettings
        )

        bpy.utils.register_class(UpdatePointCloudVisualizationOperator)
        bpy.utils.register_class(SaveOpenGLRenderImageOperator)
        bpy.utils.register_class(ExportOpenGLRenderImageOperator)
        bpy.utils.register_class(ExportOpenGLRenderAnimationOperator)

    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(OpenGLPanelSettings)
        del bpy.types.Scene.opengl_panel_settings

        bpy.utils.unregister_class(UpdatePointCloudVisualizationOperator)
        bpy.utils.unregister_class(SaveOpenGLRenderImageOperator)
        bpy.utils.unregister_class(ExportOpenGLRenderImageOperator)
        bpy.utils.unregister_class(ExportOpenGLRenderAnimationOperator)

    def draw(self, context):
        """Draw the panel with corrresponding properties and operators."""
        settings = context.scene.opengl_panel_settings
        layout = self.layout
        viz_box = layout.box()
        viz_box.label(text="Visualization")
        row = viz_box.row()
        row.prop(
            settings,
            "viz_point_size",
            text="OpenGL Visualization Point Size",
        )
        row = viz_box.row()
        row.operator(UpdatePointCloudVisualizationOperator.bl_idname)

        write_box = layout.box()
        write_box.label(
            text="Select a camera to save / export an OpenGL rendering"
        )
        row = write_box.row()
        row.prop(
            settings,
            "save_point_size",
            text="OpenGL Save / Export Point Size",
        )
        save_box = write_box.box()
        save_box.label(text="Save results:")
        row = save_box.row()
        row.operator(SaveOpenGLRenderImageOperator.bl_idname)

        export_box = write_box.box()
        export_box.label(text="Export results:")
        row = export_box.row()
        row.prop(settings, "file_format", text="File Format")
        row = export_box.row()
        row.prop(settings, "save_alpha", text="Save Alpha Values")
        row = export_box.row()
        row.operator(ExportOpenGLRenderImageOperator.bl_idname)
        row = export_box.row()
        row.prop(settings, "use_camera_keyframes", text="Use Camera Keyframes")
        row = export_box.row()
        row.operator(ExportOpenGLRenderAnimationOperator.bl_idname)


class UpdatePointCloudVisualizationOperator(bpy.types.Operator):
    """Operator to update the point cloud visualization in the 3D view."""

    bl_idname = "photogrammetry_importer.update_point_cloud_viz"
    bl_label = "Update Visualization"
    bl_description = "Update Visualization"

    @classmethod
    def poll(cls, context):
        """Return the availability status of the operator."""
        return True

    def execute(self, context):
        """Update the visualization of the point cloud in the 3D view."""
        draw_manager = DrawManager.get_singleton()
        viz_point_size = context.scene.opengl_panel_settings.viz_point_size
        draw_manager.set_point_size(viz_point_size)
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()
                break
        return {"FINISHED"}


class SaveOpenGLRenderImageOperator(bpy.types.Operator):
    """An Operator to save a rendering of the point cloud as Blender image."""

    bl_idname = "photogrammetry_importer.save_opengl_render_image"
    bl_label = "Save as Blender Image"
    bl_description = "Use a single camera to render the point cloud."

    @classmethod
    def poll(cls, context):
        """Return the availability status of the operator."""
        cam = _get_selected_camera()
        return cam is not None

    def execute(self, context):
        """Render the point cloud and save the result as image in Blender."""
        log_report("INFO", "Save opengl render as image: ...", self)
        save_point_size = context.scene.opengl_panel_settings.save_point_size
        cam = _get_selected_camera()
        image_name = "OpenGL Render"
        log_report("INFO", "image_name: " + image_name, self)
        render_opengl_image(image_name, cam, save_point_size)
        log_report("INFO", "Save opengl render as image: Done", self)
        return {"FINISHED"}


class ExportOpenGLRenderImageOperator(bpy.types.Operator, ExportHelper):
    """An Operator to save a rendering of the point cloud to disk."""

    bl_idname = "photogrammetry_importer.export_opengl_render_image"
    bl_label = "Export as Image"
    bl_description = "Use a single camera to render the point cloud."

    # Hide the porperty by using a normal string instad of a string property
    filename_ext = ""

    @classmethod
    def poll(cls, context):
        """Return the availability status of the operator."""
        cam = _get_selected_camera()
        return cam is not None

    def execute(self, context):
        """Render the point cloud and export the result as image."""
        log_report("INFO", "Export opengl render as image: ...", self)
        scene = context.scene
        save_point_size = scene.opengl_panel_settings.save_point_size

        filename_ext = scene.opengl_panel_settings.file_format
        ofp = self.filepath + "." + filename_ext
        log_report("INFO", "Output File Path: " + ofp, self)

        # Used to cache the results
        image_name = "OpenGL Export"

        cam = _get_selected_camera()
        render_opengl_image(image_name, cam, save_point_size)

        save_alpha = scene.opengl_panel_settings.save_alpha
        save_image_to_disk(image_name, ofp, save_alpha)

        log_report("INFO", "Save opengl render as image: Done", self)
        return {"FINISHED"}


class ExportOpenGLRenderAnimationOperator(bpy.types.Operator, ExportHelper):
    """An Operator to save multiple renderings of the point cloud to disk."""

    bl_idname = "photogrammetry_importer.export_opengl_render_animation"
    bl_label = "Export as Image Sequence"
    bl_description = "Use an animated camera to render the point cloud."

    # Hide the porperty by using a normal string instad of a string property
    filename_ext = ""

    @classmethod
    def poll(cls, context):
        """Return the availability status of the operator."""
        cam = _get_selected_camera()
        return cam is not None and cam.animation_data is not None

    def _get_animation_indices(self, obj):

        animation_data = obj.animation_data
        fcurves = animation_data.action.fcurves
        fcu = fcurves[0]
        kp_indices = [int(kp.co[0]) for kp in fcu.keyframe_points]
        return kp_indices

    def _get_indices(self, use_camera_keyframes, cam):
        if use_camera_keyframes:
            indices = self._get_animation_indices(cam)
        else:
            scene = bpy.context.scene
            indices = range(scene.frame_start, scene.frame_end)
        return indices

    def execute(self, context):
        """Render the point cloud and export the result as image sequence."""
        log_report(
            "INFO", "Export opengl render as image sequencemation: ...", self
        )
        scene = context.scene
        save_point_size = scene.opengl_panel_settings.save_point_size

        use_camera_keyframes = scene.opengl_panel_settings.use_camera_keyframes
        file_format = scene.opengl_panel_settings.file_format

        # The export helper stores the path in self.filepath (even if it is a
        # directory)
        output_dp = self.filepath
        log_report("INFO", "Output Directory Path: " + str(output_dp), self)

        if not os.path.isdir(output_dp):
            os.mkdir(output_dp)

        # Used to cache the results
        image_name = "OpenGL Export"
        ext = "." + file_format
        save_alpha = scene.opengl_panel_settings.save_alpha
        cam = _get_selected_camera()
        indices = self._get_indices(use_camera_keyframes, cam)
        for idx in indices:
            bpy.context.scene.frame_set(idx)
            current_frame_fn = str(idx).zfill(5) + ext
            current_frame_fp = os.path.join(output_dp, current_frame_fn)

            log_report(
                "INFO", "Output File Path: " + str(current_frame_fp), self
            )
            render_opengl_image(image_name, cam, save_point_size)
            save_image_to_disk(image_name, current_frame_fp, save_alpha)

        log_report("INFO", "Save opengl render as animation: Done", self)
        return {"FINISHED"}
