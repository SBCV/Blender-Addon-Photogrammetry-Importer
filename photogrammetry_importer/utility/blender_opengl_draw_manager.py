import numpy as np
import atexit
import bpy
import bgl
import gpu
from gpu_extras.batch import batch_for_shader
from photogrammetry_importer.utility.blender_logging_utility import log_report

def compute_transformed_coords(object_anchor_matrix_world, positions):

    if len(positions) == 0:
        return []

    pos_arr = np.asarray(positions)
    ones_arr = np.ones((pos_arr.shape[0],1))
    pos_hom_arr = np.hstack((pos_arr, ones_arr))

    # Transpose the matrix with the coordinates, 
    # so they can be transformed with a single matrix multiplication
    pos_hom_arr_transposed = np.transpose(pos_hom_arr)
    transf_pos_hom_transposed_arr = np.matmul(
        object_anchor_matrix_world, pos_hom_arr_transposed)
    transf_pos_arr_hom = transf_pos_hom_transposed_arr.T

    # Delete the homogeneous entries
    transf_pos_arr = np.delete(transf_pos_arr_hom, -1, axis=1)
    transf_pos_list = transf_pos_arr.tolist()
    return transf_pos_list


class DrawManager():

    def __init__(self):
        self.draw_callback_handler_list = []
        self.anchor_to_point_coords = {}
        self.anchor_to_point_colors = {}

    @classmethod
    def get_singleton(cls):

        if hasattr(bpy.types.Object, 'current_draw_manager'):
            draw_manger = bpy.types.Object.current_draw_manager
        else:  
           draw_manger = cls()
           bpy.types.Object.current_draw_manager = draw_manger
        return draw_manger

    def register_points_draw_callback(self, object_anchor, coords, colors):
        draw_callback_handler = DrawCallBackHandler()
        draw_callback_handler.register_points_draw_callback(
            self, object_anchor, coords, colors)
        self.draw_callback_handler_list.append(draw_callback_handler)

        self.anchor_to_point_coords[object_anchor] = coords
        self.anchor_to_point_colors[object_anchor] = colors
    
    def get_coords_and_colors(self):

        transf_coord_list = []
        color_list = []
        for object_anchor in self.anchor_to_point_coords:

            coords = self.anchor_to_point_coords[object_anchor]
            transf_coord_list = transf_coord_list + compute_transformed_coords(
                object_anchor.matrix_world, coords)

            colors = self.anchor_to_point_colors[object_anchor]
            color_list = color_list + colors

        return transf_coord_list, color_list

    def delete_anchor(self, object_anchor):
        del self.anchor_to_point_coords[object_anchor]
        del self.anchor_to_point_colors[object_anchor]

    def set_point_size(self, point_size):
        for draw_back_handler in self.draw_callback_handler_list:
            draw_back_handler.point_size = point_size


class DrawCallBackHandler():

    def __init__(self):
        self.shader = gpu.shader.from_builtin("3D_FLAT_COLOR")
        
        # Handle to the function
        self.draw_handler_handle = None

        # Handle to the object
        self.object_anchor_handle = None
        self.object_anchor_pose_previous = np.array([])
        self.batch_cached = None
        self.point_size = 5

        # If Blender is closed and self.batch_cached is not properly deleted, 
        # this causes something like the following:
        # "Error: Not freed memory blocks: 2, total unfreed memory 0.001358 MB"
        atexit.register(self.clean_batch_cached)

    def clean_batch_cached(self):
        self.batch_cached = None

    def draw_points_callback(self, draw_manager, object_anchor, positions, colors):

        handle_is_valid = True
        try:
            # Check if object still exists
            object_anchor_name = object_anchor.name
        except:
            handle_is_valid = False

        if handle_is_valid:
            if object_anchor_name in bpy.data.objects:

                # Use the visibility of the object to enable / 
                # disable the drawing of the point cloud
                if bpy.data.objects[object_anchor_name].visible_get():

                    # Update the batch depending on the anchor pose (only if necessary)
                    object_anchor_has_changed = not np.array_equal(
                        self.object_anchor_pose_previous, object_anchor.matrix_world)
                    if self.batch_cached is None or object_anchor_has_changed:
                        
                        self.object_anchor_pose_previous = np.copy(object_anchor.matrix_world)
                        transf_pos_list = compute_transformed_coords(
                            object_anchor.matrix_world, positions)

                        self.batch_cached = batch_for_shader(
                            self.shader, "POINTS", {"pos": transf_pos_list, "color": colors})

                    self.shader.bind()
                    bgl.glPointSize(self.point_size)
                    bgl.glEnable(bgl.GL_DEPTH_TEST)
                    bgl.glDepthMask(bgl.GL_TRUE)

                    self.batch_cached.draw(self.shader)

        else:
            log_report('INFO', 'Removing draw handler of deleted point cloud handle')
            if self.draw_handler_handle is not None:
                bpy.types.SpaceView3D.draw_handler_remove(
                    self.draw_handler_handle, 'WINDOW')
                self.draw_handler_handle = None
                self.batch_cached = None
                draw_manager.delete_anchor(object_anchor)

    def register_points_draw_callback(self, draw_manager, object_anchor, positions, colors):

        args = (draw_manager, object_anchor, positions, colors)
        self.draw_handler_handle = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_points_callback, args, "WINDOW", "POST_VIEW")

