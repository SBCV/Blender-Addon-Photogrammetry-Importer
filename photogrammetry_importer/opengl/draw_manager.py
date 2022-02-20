import numpy as np
import atexit
import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from photogrammetry_importer.blender_utility.logging_utility import log_report


def _compute_transformed_coords(object_anchor_matrix_world, positions):

    if len(positions) == 0:
        return []

    pos_arr = np.asarray(positions)
    ones_arr = np.ones((pos_arr.shape[0], 1))
    pos_hom_arr = np.hstack((pos_arr, ones_arr))

    # Transpose the matrix to transform the coordinates
    # with a single matrix multiplication
    pos_hom_arr_transposed = np.transpose(pos_hom_arr)
    transf_pos_hom_transposed_arr = np.matmul(
        object_anchor_matrix_world, pos_hom_arr_transposed
    )
    transf_pos_arr_hom = transf_pos_hom_transposed_arr.T

    # Delete the homogeneous entries
    transf_pos_arr = np.delete(transf_pos_arr_hom, -1, axis=1)
    transf_pos_list = transf_pos_arr.tolist()
    return transf_pos_list


class DrawManager:
    """Class that allows to represent point clouds with OpenGL in Blender."""

    def __init__(self):
        self._anchor_to_draw_callback_handler = {}
        self._anchor_to_point_coords = {}
        self._anchor_to_point_colors = {}

    @classmethod
    def get_singleton(cls):
        """Return a singleton of this class."""
        if hasattr(bpy.types.Object, "current_draw_manager"):
            draw_manger = bpy.types.Object.current_draw_manager
        else:
            draw_manger = cls()
            bpy.types.Object.current_draw_manager = draw_manger
        return draw_manger

    def register_points_draw_callback(
        self, object_anchor, coords, colors, point_size
    ):
        """Register a callback to draw a point cloud."""
        draw_callback_handler = _DrawCallBackHandler()
        draw_callback_handler.register_points_draw_callback(
            self, object_anchor, coords, colors, point_size
        )
        self._anchor_to_draw_callback_handler[
            object_anchor
        ] = draw_callback_handler
        self._anchor_to_point_coords[object_anchor] = coords
        self._anchor_to_point_colors[object_anchor] = colors

    def get_coords_and_colors(self, visible_only=False):
        """Return the coordinates and the colors of the maintained points."""
        transf_coord_list = []
        color_list = []
        for object_anchor in self._anchor_to_point_coords:

            if visible_only and not object_anchor.visible_get():
                continue

            coords = self._anchor_to_point_coords[object_anchor]
            transf_coord_list = (
                transf_coord_list
                + _compute_transformed_coords(
                    object_anchor.matrix_world, coords
                )
            )

            colors = self._anchor_to_point_colors[object_anchor]
            color_list = color_list + colors

        return transf_coord_list, color_list

    def delete_anchor(self, object_anchor):
        """Delete the anchor used to control the pose of the point cloud."""
        del self._anchor_to_point_coords[object_anchor]
        del self._anchor_to_point_colors[object_anchor]
        # del self._anchor_to_draw_callback_handler[object_anchor]

    def get_draw_callback_handler(self, object_anchor):
        """Get the draw callback handler corresponding to the object anchor."""
        return self._anchor_to_draw_callback_handler[object_anchor]


class _DrawCallBackHandler:
    """Class that allows to handle point drawing callbacks."""

    def __init__(self):
        self._shader = gpu.shader.from_builtin("3D_FLAT_COLOR")

        # Handle to the function
        self._draw_handler_handle = None

        # Handle to the object
        self._object_anchor_pose_previous = np.array([])
        self._batch_cached = None
        self._point_size = 5

        # If Blender is closed and self._batch_cached is not properly deleted,
        # this causes something like the following:
        # "Error: Not freed memory blocks: 2, total unfreed memory 0.001358 MB"
        atexit.register(self._clean_batch_cached)

    def _clean_batch_cached(self):
        """Clean the cached batch used to draw the points."""
        self._batch_cached = None

    def set_point_size(self, point_size):
        """Set the point size used to draw the points in the 3D point cloud."""
        self._point_size = point_size

    def _draw_points_callback(
        self, draw_manager, object_anchor, positions, colors
    ):
        """A callback function to draw a point cloud in Blender's 3D view."""
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

                    # Update the batch depending on the anchor pose (only if
                    # necessary)
                    object_anchor_has_changed = not np.array_equal(
                        self._object_anchor_pose_previous,
                        object_anchor.matrix_world,
                    )
                    if self._batch_cached is None or object_anchor_has_changed:

                        self._object_anchor_pose_previous = np.copy(
                            object_anchor.matrix_world
                        )
                        transf_pos_list = _compute_transformed_coords(
                            object_anchor.matrix_world, positions
                        )

                        self._batch_cached = batch_for_shader(
                            self._shader,
                            "POINTS",
                            {"pos": transf_pos_list, "color": colors},
                        )

                    self._shader.bind()
                    gpu.state.point_size_set(self._point_size)

                    previous_depth_mask_value = gpu.state.depth_mask_get()
                    previous_depth_test_value = gpu.state.depth_test_get()
                    gpu.state.depth_mask_set(True)
                    gpu.state.depth_test_set("LESS_EQUAL")

                    self._batch_cached.draw(self._shader)

                    gpu.state.depth_mask_set(previous_depth_mask_value)
                    gpu.state.depth_test_set(previous_depth_test_value)

        else:
            if self._draw_handler_handle is not None:
                log_report(
                    "INFO",
                    "Removing draw handler of deleted point cloud handle",
                )
                bpy.types.SpaceView3D.draw_handler_remove(
                    self._draw_handler_handle, "WINDOW"
                )
                self._draw_handler_handle = None
                self._batch_cached = None
                draw_manager.delete_anchor(object_anchor)

    def register_points_draw_callback(
        self, draw_manager, object_anchor, positions, colors, point_size
    ):
        """Register a callback to draw a point cloud."""
        self.set_point_size(point_size)
        args = (draw_manager, object_anchor, positions, colors)
        self._draw_handler_handle = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_points_callback, args, "WINDOW", "POST_VIEW"
        )
