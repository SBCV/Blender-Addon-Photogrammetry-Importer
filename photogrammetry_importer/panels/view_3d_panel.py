import os
import numpy as np
import bpy

from photogrammetry_importer.types.point import Point
from photogrammetry_importer.utility.blender_camera_utility import get_selected_camera
from photogrammetry_importer.utility.blender_opengl_utility import render_opengl_image
from photogrammetry_importer.utility.blender_opengl_draw_manager import DrawManager
from photogrammetry_importer.utility.blender_logging_utility import log_report

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       PointerProperty)

from bpy_extras.io_utils import (ExportHelper)


class OpenGLPanelVizSettings(bpy.types.PropertyGroup):
    viz_point_size : IntProperty(
        name="Point Size",
        description="OpenGL visualization point size.",
        default=10)


class OpenGLPanelWriteSettings(bpy.types.PropertyGroup):
    write_point_size : IntProperty(
        name="Point Size",
        description="OpenGL point size.",
        default=10)


class OpenGLPanelExportImageSettings(bpy.types.PropertyGroup):
    file_format : StringProperty(
        name="File format",
        description="File format of the exported file(s)",
        default='png')


class OpenGLPanelExportAnimationSettings(bpy.types.PropertyGroup):
    use_camera_keyframes : BoolProperty(
        name="Use Camera Keyframes",
        description="Use the Camera Keyframes instead of Animation Frames.",
        default=True)


class OpenGLPanel(bpy.types.Panel):
    bl_label = "OpenGL Panel"
    bl_idname = "EXPORT_OPENGL_PT_render_point_cloud"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PhotogrammetryImporter"

    @classmethod
    def poll(cls, context):
        return True

    @classmethod
    def register(cls):

        # https://blender.stackexchange.com/questions/35007/how-can-i-add-a-checkbox-in-the-tools-ui
        # https://blender.stackexchange.com/questions/28966/the-register-class-function-how-to-declare
        # https://blender.stackexchange.com/questions/17751/how-display-and-use-operator-properties-in-a-python-blender-ui-panel

        bpy.utils.register_class(OpenGLPanelVizSettings)
        bpy.types.Scene.opengl_panel_viz_settings = PointerProperty(
            type=OpenGLPanelVizSettings)

        bpy.utils.register_class(OpenGLPanelWriteSettings)
        bpy.types.Scene.opengl_panel_write_settings = PointerProperty(
            type=OpenGLPanelWriteSettings)

        bpy.utils.register_class(OpenGLPanelExportImageSettings)
        bpy.types.Scene.opengl_panel_export_image_settings = PointerProperty(
            type=OpenGLPanelExportImageSettings)

        bpy.utils.register_class(OpenGLPanelExportAnimationSettings)
        bpy.types.Scene.opengl_panel_export_animation_settings = PointerProperty(
            type=OpenGLPanelExportAnimationSettings)

        bpy.utils.register_class(UpdatePointCloudVisualizationOperator)
        bpy.utils.register_class(SaveOpenGLRenderImageOperator)
        bpy.utils.register_class(ExportOpenGLRenderImageOperator)
        bpy.utils.register_class(ExportOpenGLRenderAnimationOperator)

    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(OpenGLPanelVizSettings)
        del bpy.types.Scene.opengl_panel_viz_settings

        bpy.utils.unregister_class(OpenGLPanelWriteSettings)
        del bpy.types.Scene.opengl_panel_write_settings

        bpy.utils.unregister_class(OpenGLPanelExportImageSettings)
        del bpy.types.Scene.opengl_panel_export_image_settings

        bpy.utils.unregister_class(OpenGLPanelExportAnimationSettings)
        del bpy.types.Scene.opengl_panel_export_animation_settings

        bpy.utils.unregister_class(UpdatePointCloudVisualizationOperator)
        bpy.utils.unregister_class(SaveOpenGLRenderImageOperator)
        bpy.utils.unregister_class(ExportOpenGLRenderImageOperator)
        bpy.utils.unregister_class(ExportOpenGLRenderAnimationOperator)

    def draw(self, context):
        layout = self.layout
        viz_box = layout.box()
        viz_box.label(text="Visualization")
        row = viz_box.row()
        row.prop(
            context.scene.opengl_panel_viz_settings, 
            "viz_point_size", 
            text="OpenGL Visualization Point Size")
        row = viz_box.row()
        row.operator("photogrammetry_importer.update_point_cloud_viz")

        write_box = layout.box()
        write_box.label(text="Select a camera to save/export an OpenGL rendering:")
        row = write_box.row()
        row.prop(
            context.scene.opengl_panel_write_settings, 
            "write_point_size", 
            text="OpenGL Save/Exort Point Size")
        save_box = write_box.box()
        save_box.label(text="Save results:")
        row = save_box.row()
        row.operator("photogrammetry_importer.save_opengl_render_image")
        
        export_box = write_box.box()
        export_box.label(text="Export results:")
        row = export_box.row()
        row.prop(
            context.scene.opengl_panel_export_image_settings, 
            "file_format", 
            text="File Format")
        row = export_box.row()
        row.operator("photogrammetry_importer.export_opengl_render_image")
        row = export_box.row()
        row.prop(
            context.scene.opengl_panel_export_animation_settings, 
            "use_camera_keyframes", 
            text="Use Camera Keyframes")
        row = export_box.row()
        row.operator("photogrammetry_importer.export_opengl_render_animation")


class UpdatePointCloudVisualizationOperator(bpy.types.Operator):
    bl_idname = "photogrammetry_importer.update_point_cloud_viz"
    bl_label = "Update Visualization"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        draw_manager = DrawManager.get_singleton()
        viz_point_size = context.scene.opengl_panel_viz_settings.viz_point_size
        draw_manager.set_point_size(viz_point_size)
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
                break
        return {'FINISHED'}


class SaveOpenGLRenderImageOperator(bpy.types.Operator):
    bl_idname = "photogrammetry_importer.save_opengl_render_image"
    bl_label = "Save as Image"

    @classmethod
    def poll(cls, context):
        cam = get_selected_camera()
        return cam is not None

    def execute(self, context):
        self.report({'INFO'}, 'Save opengl render as image: ...')
        write_point_size = context.scene.opengl_panel_write_settings.write_point_size
        cam = get_selected_camera()
        image_name = "OpenGL Render"
        log_report('INFO', 'image_name: ' + image_name, self)
        render_opengl_image(image_name, cam, write_point_size)
        log_report('INFO', 'Save opengl render as image: Done', self)
        return {'FINISHED'}


class ExportOpenGLRenderImageOperator(bpy.types.Operator, ExportHelper):
    bl_idname = "photogrammetry_importer.export_opengl_render_image"
    bl_label = "Export as Image"
    
    filename_ext : StringProperty(default=".png")
    
    @classmethod
    def poll(cls, context): 
        cam = get_selected_camera()
        return cam is not None

    def execute(self, context):
        log_report('INFO', 'Export opengl render as image: ...', self)
        write_point_size = context.scene.opengl_panel_write_settings.write_point_size
        file_format = context.scene.opengl_panel_export_image_settings.file_format

        log_report('INFO', 'Output File Path: ' + str(self.filepath), self)

        # Used to cache the results 
        image_name = "Export Opengl"
        ext = '.' + file_format
        scene = bpy.context.scene

        cam = get_selected_camera()

        render_opengl_image(image_name, cam, write_point_size)
        bpy.data.images[image_name].save_render(self.filepath)
        log_report('INFO', 'Save opengl render as image: Done', self)
        return {'FINISHED'}


class ExportOpenGLRenderAnimationOperator(bpy.types.Operator, ExportHelper):
    bl_idname = "photogrammetry_importer.export_opengl_render_animation"
    bl_label = "Export as Animation"
    
    filename_ext = ""
    
    @classmethod
    def poll(cls, context):
        cam = get_selected_camera()
        return cam is not None and cam.animation_data is not None

    def get_animation_indices(self, obj):

        animation_data = obj.animation_data
        fcurves = animation_data.action.fcurves
        fcu = fcurves[0]
        # print(fcu.data_path, fcu.array_index)
        kp_indices = [int(kp.co[0]) for kp in fcu.keyframe_points]
        return kp_indices

    def get_indices(self, use_camera_keyframes, cam):
        if use_camera_keyframes:
            indices = self.get_animation_indices(cam)
        else:
            scene = bpy.context.scene
            indices = range(scene.frame_start, scene.frame_end)
        return indices

    def execute(self, context):
        log_report('INFO', 'Export opengl render as animation: ...', self)
        write_point_size = context.scene.opengl_panel_write_settings.write_point_size

        use_camera_keyframes = context.scene.opengl_panel_export_animation_settings.use_camera_keyframes
        file_format = context.scene.opengl_panel_export_image_settings.file_format

        # The export helper stores the path in self.filepath (even if its a directory)
        output_dp = self.filepath
        log_report('INFO', 'Output Directory Path: ' + str(output_dp), self)

        if not os.path.isdir(output_dp):
            os.mkdir(output_dp)

        # Used to cache the results 
        image_name = "Export Opengl"
        ext = '.' + file_format
        scene = bpy.context.scene
        cam = get_selected_camera()
        indices = self.get_indices(use_camera_keyframes, cam)
        for idx in indices:
            scene.frame_set(idx)
            current_frame_fn = str(idx).zfill(5) + ext
            current_frame_fp = os.path.join(output_dp, current_frame_fn)

            log_report('INFO', 'Output File Path: ' + str(current_frame_fp), self)
            render_opengl_image(image_name, cam, write_point_size)
            bpy.data.images[image_name].save_render(current_frame_fp)

        log_report('INFO', 'Save opengl render as animation: Done', self)
        return {'FINISHED'}

