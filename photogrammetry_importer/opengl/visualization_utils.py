
from photogrammetry_importer.utils.blender_utils import add_empty
from photogrammetry_importer.opengl.draw_manager import DrawManager


def draw_points(op, points):

    op.report({'INFO'}, 'Drawing points: ...')

    object_anchor_handle = add_empty("point_cloud_drawing_handle")
    draw_manager = DrawManager.get_singleton()
    draw_manager.register_points_draw_callback(
        object_anchor_handle, points)

    op.report({'INFO'}, 'Drawing points: Done')

