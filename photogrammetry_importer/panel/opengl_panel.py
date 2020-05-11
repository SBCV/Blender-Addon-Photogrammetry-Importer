import os
import numpy as np

import bpy
import bgl
import gpu
from gpu.types import GPUOffScreen, GPUShader, GPUBatch, GPUVertBuf, GPUVertFormat
from gpu_extras.batch import batch_for_shader

from mathutils import Vector, Matrix

from photogrammetry_importer.opengl.visualization_utils import DrawManager
from photogrammetry_importer.utils.blender_camera_utils import get_selected_camera
from photogrammetry_importer.point import Point

from bpy.props import (#CollectionProperty,
                       StringProperty,
                       #BoolProperty,
                       #EnumProperty,
                       #FloatProperty,
                       #IntProperty,
                       )

from bpy_extras.io_utils import (ImportHelper,
                                 ExportHelper)

class OpenGLPanel(bpy.types.Panel):
    bl_label = "OpenGL Panel"
    bl_idname = "export_opengl.render_point_cloud"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PhotogrammetryImporter"

    @classmethod
    def poll(cls,context):
        return True

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("export_opengl.save_opengl_render_image")
        row = layout.row()
        row.operator("export_opengl.export_opengl_render_image")


class OpenGLImageRenderer():
    def render_opengl_image(self):
        draw_manager = DrawManager.get_singleton()
        coords, colors = draw_manager.get_coords_and_colors()
    
        image_name = "Enhanced OpenGL Render"
        scene = bpy.context.scene
        render = bpy.context.scene.render
        cam = get_selected_camera()
        if cam is None:
            cam = scene.camera

        width = render.resolution_x
        height = render.resolution_y
       
        # TODO Provide an option to render from the 3D view perspective
        # width = bpy.context.region.width
        # height = bpy.context.region.height

        offscreen = gpu.types.GPUOffScreen(width, height)
        with offscreen.bind():

            bgl.glPointSize(5)
            #bgl.glClear(bgl.GL_COLOR_BUFFER_BIT)
            #bgl.glClear(bgl.GL_DEPTH_BUFFER_BIT)

            view_matrix = cam.matrix_world.inverted()
            projection_matrix = cam.calc_matrix_camera(
                bpy.context.evaluated_depsgraph_get(), 
                x=width,
                y=height)
            perspective_matrix = projection_matrix @ view_matrix

            gpu.matrix.load_matrix(perspective_matrix)
            gpu.matrix.load_projection_matrix(Matrix.Identity(4))
            
            shader = gpu.shader.from_builtin('3D_FLAT_COLOR')
            shader.bind()
            batch = batch_for_shader(shader, "POINTS", {"pos": coords, "color": colors})
            batch.draw(shader)
           
            buffer = bgl.Buffer(bgl.GL_BYTE, width * height * 4)
            bgl.glReadPixels(0, 0, width, height, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, buffer)

        offscreen.free()

        if image_name not in bpy.data.images:
            bpy.data.images.new(image_name, width, height)
        else:
            bpy.data.images[image_name].scale(width, height)
        image = bpy.data.images[image_name]
        image.pixels = [v / 255 for v in buffer]
        return image_name


class SaveOpenGLRenderImageOperator(bpy.types.Operator, OpenGLImageRenderer):
    bl_idname = "export_opengl.save_opengl_render_image"
    bl_label = "Save Render as Image"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        self.report({'INFO'}, 'Save opengl render as image: ...')
        self.render_opengl_image()
        self.report({'INFO'}, 'Save opengl render as image: Done')
        return {'FINISHED'}

class ExportOpenGLRenderImageOperator(bpy.types.Operator, ExportHelper, OpenGLImageRenderer):
    bl_idname = "export_opengl.export_opengl_render_image"
    bl_label = "Export Render to Disk"
    
    filename_ext : StringProperty(default=".png")
    
    @classmethod
    def poll(cls, context): 
        return True

    def execute(self, context):
        self.report({'INFO'}, 'Export opengl render as image: ...')
        self.report({'INFO'}, 'Output File Path: ' + str(self.filepath))
        image_name = self.render_opengl_image()
        bpy.data.images[image_name].save_render(self.filepath)
        self.report({'INFO'}, 'Save opengl render as image: Done')
        return {'FINISHED'}

