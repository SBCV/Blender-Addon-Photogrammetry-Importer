import numpy as np
import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    PointerProperty,
)
from photogrammetry_importer.panels.screenshot_operators import (
    ExportScreenshotImageOperator,
    ExportScreenshotAnimationOperator,
)
from photogrammetry_importer.panels.render_operators import (
    SaveOpenGLRenderImageOperator,
    ExportOpenGLRenderImageOperator,
    ExportOpenGLRenderAnimationOperator,
)
from photogrammetry_importer.types.point import Point
from photogrammetry_importer.opengl.draw_manager import DrawManager
from photogrammetry_importer.blender_utility.logging_utility import log_report
from photogrammetry_importer.blender_utility.retrieval_utility import (
    get_selected_empty,
    get_selected_camera,
)


class OpenGLPanelSettings(bpy.types.PropertyGroup):
    """Class that defines the properties of the OpenGL panel in the 3D view."""

    # https://docs.blender.org/api/current/bpy.props.html#getter-setter-example
    def get_viz_point_size(self):
        point_cloud_anchor = get_selected_empty()
        if point_cloud_anchor is not None:
            if "point_size" in point_cloud_anchor:
                return point_cloud_anchor["point_size"]
        return 1

    def set_viz_point_size(self, value):
        point_cloud_anchor = get_selected_empty()
        if point_cloud_anchor is not None:
            point_cloud_anchor["point_size"] = value

            draw_manager = DrawManager.get_singleton()
            draw_back_handler = draw_manager.get_draw_callback_handler(
                point_cloud_anchor
            )
            draw_back_handler.set_point_size(value)

    viz_point_size: IntProperty(
        name="Point Size",
        description="OpenGL visualization point size.",
        get=get_viz_point_size,
        set=set_viz_point_size,
        min=1,
    )
    only_3d_view: BoolProperty(
        name="Export Only 3D View",
        description="Export only the 3D view or the full UI of Blender",
        default=True,
    )
    use_camera_perspective: BoolProperty(
        name="Use Perspective of Selected Camera",
        description="",
        default=True,
    )
    screenshot_file_format: StringProperty(
        name="File format",
        description="File format of the exported screenshot(s)",
        default="png",
    )
    use_camera_keyframes_for_screenshots: BoolProperty(
        name="Use Keyframes of Selected Camera",
        description="Use the Camera Keyframes instead of Animation Frames",
        default=True,
    )
    save_point_size: IntProperty(
        name="Point Size", description="OpenGL point size.", default=10
    )
    render_file_format: StringProperty(
        name="File format",
        description="File format of the exported rendering(s)",
        default="png",
    )
    save_alpha: BoolProperty(
        name="Save Alpha Values",
        description="Save alpha values (if possible) to disk.",
        default=True,
    )
    use_camera_keyframes_for_rendering: BoolProperty(
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

        bpy.utils.register_class(ExportScreenshotImageOperator)
        bpy.utils.register_class(ExportScreenshotAnimationOperator)
        bpy.utils.register_class(SaveOpenGLRenderImageOperator)
        bpy.utils.register_class(ExportOpenGLRenderImageOperator)
        bpy.utils.register_class(ExportOpenGLRenderAnimationOperator)

    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(OpenGLPanelSettings)
        del bpy.types.Scene.opengl_panel_settings

        bpy.utils.unregister_class(ExportScreenshotImageOperator)
        bpy.utils.unregister_class(ExportScreenshotAnimationOperator)
        bpy.utils.unregister_class(SaveOpenGLRenderImageOperator)
        bpy.utils.unregister_class(ExportOpenGLRenderImageOperator)
        bpy.utils.unregister_class(ExportOpenGLRenderAnimationOperator)

    def draw(self, context):
        """Draw the panel with corrresponding properties and operators."""
        settings = context.scene.opengl_panel_settings
        layout = self.layout
        selected_empty = get_selected_empty()
        selected_cam = get_selected_camera()

        viz_box = layout.box()
        viz_box.label(
            text="Select a point cloud anchor (i.e. the correspinding empty)"
            " to adjust the point size."
        )
        anchor_selected = (
            selected_empty is not None and "point_size" in selected_empty
        )
        row = viz_box.row()
        row.prop(
            settings,
            "viz_point_size",
            text="OpenGL Visualization Point Size",
        )
        row.enabled = anchor_selected

        export_screenshot_box = layout.box()
        export_screenshot_box.label(
            text="Export a single or multiple"
            " screenshots (of the 3D view) to disk."
        )
        row = export_screenshot_box.row()
        row.prop(settings, "screenshot_file_format", text="File Format")
        row = export_screenshot_box.row()
        row.prop(settings, "only_3d_view", text="Export Only 3D view")
        row = export_screenshot_box.row()
        row.prop(
            settings,
            "use_camera_perspective",
            text="Use Perspective of selected Camera",
        )
        row.enabled = selected_cam is not None
        row = export_screenshot_box.row()
        row.operator(ExportScreenshotImageOperator.bl_idname)
        row = export_screenshot_box.row()
        row.prop(
            settings,
            "use_camera_keyframes_for_screenshots",
            text="Use Camera Keyframes",
        )
        row.enabled = (
            selected_cam is not None
            and selected_cam.animation_data is not None
        )
        row = export_screenshot_box.row()
        row.operator(ExportScreenshotAnimationOperator.bl_idname)

        write_point_cloud_box = layout.box()
        write_point_cloud_box.label(
            text="Select a camera to save or export an OpenGL point cloud"
            " rendering"
        )
        row = write_point_cloud_box.row()
        row.prop(
            settings,
            "save_point_size",
            text="Point Size of OpenGL Point Cloud",
        )
        row.enabled = selected_cam is not None
        save_point_cloud_box = write_point_cloud_box.box()
        save_point_cloud_box.label(text="Save point cloud rendering:")
        row = save_point_cloud_box.row()
        row.operator(SaveOpenGLRenderImageOperator.bl_idname)

        export_point_cloud_box = write_point_cloud_box.box()
        export_point_cloud_box.label(text="Export point cloud rendering:")
        row = export_point_cloud_box.row()
        row.prop(settings, "render_file_format", text="File Format")
        row.enabled = selected_cam is not None
        row = export_point_cloud_box.row()
        row.prop(settings, "save_alpha", text="Save Alpha Values")
        row.enabled = selected_cam is not None
        row = export_point_cloud_box.row()
        row.operator(ExportOpenGLRenderImageOperator.bl_idname)
        row = export_point_cloud_box.row()
        row.prop(
            settings,
            "use_camera_keyframes_for_rendering",
            text="Use Camera Keyframes",
        )
        row.enabled = (
            selected_cam is not None
            and selected_cam.animation_data is not None
        )
        row = export_point_cloud_box.row()
        row.operator(ExportOpenGLRenderAnimationOperator.bl_idname)
