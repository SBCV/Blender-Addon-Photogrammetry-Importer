import numpy as np
import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from random import random
from photogrammetry_importer.utils.blender_utils import add_empty
import bgl

draw_manager = None

class DrawManager():

    def __init__(self):
        self.draw_call_back_handler_list = []

    def get_call_back_handler(self):
        draw_call_back_handler = DrawCallBackHandler()
        self.draw_call_back_handler_list.append(draw_call_back_handler)
        return draw_call_back_handler

class DrawCallBackHandler():

    def __init__(self):
        self.shader = gpu.shader.from_builtin("3D_FLAT_COLOR")
        
        # Handle to the function
        self.draw_handler_handle = None

        # Handle to the object
        self.object_anchor_handle = None
        self.object_anchor_pose_previous = np.array([])
        self.batch_cached = None

    def draw_points_callback(self, object_handle, positions, colors):

        handle_is_valid = True
        try:
            # Check if object still exists
            object_handle_name = object_handle.name
        except:
            handle_is_valid = False

        if handle_is_valid:
            if object_handle_name in bpy.data.objects:

                # Use the visibility of the object to enable / 
                # disable the drawing of the point cloud
                if bpy.data.objects[object_handle_name].visible_get():

                    # Update the batch depending on the anchor pose (only if necessary)
                    object_anchor_has_changed = not np.array_equal(
                        self.object_anchor_pose_previous, object_handle.matrix_world)
                    if  self.batch_cached is None or object_anchor_has_changed:
                        
                        self.object_anchor_pose_previous = np.copy(object_handle.matrix_world)

                        pos_arr = np.asarray(positions)
                        ones_arr = np.ones((pos_arr.shape[0],1))
                        pos_hom_arr = np.hstack((pos_arr, ones_arr))

                        # Transpose the matrix with the coordinates, 
                        # so they can be transformed with a single matrix multiplication
                        pos_hom_arr_transposed = np.transpose(pos_hom_arr)
                        transf_pos_hom_transposed_arr = np.matmul(
                            object_handle.matrix_world, pos_hom_arr_transposed)
                        transf_pos_arr_hom = transf_pos_hom_transposed_arr.T

                        # Delete the homogeneous entries
                        transf_pos_arr = np.delete(transf_pos_arr_hom, -1, axis=1)
                        transf_pos_list = transf_pos_arr.tolist()

                        self.batch_cached = batch_for_shader(
                            self.shader, "POINTS", {"pos": transf_pos_list, "color": colors})

                    self.shader.bind()

                    bgl.glEnable(bgl.GL_DEPTH_TEST)
                    bgl.glDepthMask(bgl.GL_TRUE)

                    self.batch_cached.draw(self.shader)

        else:
            print("Removing draw handler")
            if self.draw_handler_handle is not None:
                bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler_handle, 'WINDOW')
                self.draw_handler_handle = None


    def split_points(self, points):
        positions = []
        colors = []
        for point in points:
            positions.append(point.coord)
            color_with_alpha = [
                point.color[0] / 255.0, point.color[1] / 255.0, point.color[2] / 255.0, 1.0]
            colors.append(color_with_alpha)
        return positions, colors

    def register_points_draw_call_back(self, object_anchor_handle, points):

        positions, colors = self.split_points(points)
        args = (object_anchor_handle, positions, colors)
        self.draw_handler_handle = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_points_callback, args, "WINDOW", "POST_VIEW")

def draw_points(op, points):

    op.report({'INFO'}, 'Drawing points: ...')

    global draw_manager
    if draw_manager is None:
        draw_manager = DrawManager()

    object_anchor_handle = add_empty("point_cloud_drawing_handle")
    call_back_handler = draw_manager.get_call_back_handler()
    call_back_handler.register_points_draw_call_back(
        object_anchor_handle, points)

    op.report({'INFO'}, 'Drawing points: Done')

