import bpy
from bpy.app.handlers import persistent
from photogrammetry_importer.point import Point
from photogrammetry_importer.opengl.draw_manager import DrawManager

from photogrammetry_importer.utils.blender_utils import add_empty
from photogrammetry_importer.utils.blender_point_utils import compute_particle_coord_texture
from photogrammetry_importer.utils.blender_point_utils import compute_particle_color_texture
from photogrammetry_importer.blender_logging import log_report

def draw_points(op, points, add_points_to_point_cloud_handle, reconstruction_collection=None):

    log_report('INFO', 'Add particle draw handlers', op)

    coords, colors = Point.split_points(points)
    object_anchor_handle = add_empty(
        "OpenGL Point Cloud", reconstruction_collection)
    if add_points_to_point_cloud_handle:
        object_anchor_handle['particle_coords'] = coords
        object_anchor_handle['particle_colors'] = colors
        bpy.context.scene['contains_opengl_point_clouds'] = True

    draw_manager = DrawManager.get_singleton()
    draw_manager.register_points_draw_callback(
        object_anchor_handle, coords, colors)


@persistent
def redraw_points(dummy):

    # This test is very cheap, so it will not cause 
    # huge overheads for scenes without point clouds
    if 'contains_opengl_point_clouds' in bpy.context.scene:

        log_report('INFO', 'Checking scene for missing point cloud draw handlers', dummy)
        for obj in bpy.data.objects:
            if 'particle_coords' in obj and 'particle_colors' in obj:
                coords = obj['particle_coords']
                colors = obj['particle_colors']

                draw_manager = DrawManager.get_singleton()
                draw_manager.register_points_draw_callback(
                    obj, coords, colors)
                viz_point_size = bpy.context.scene.opengl_panel_viz_settings.viz_point_size
                draw_manager.set_point_size(viz_point_size)

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
                break
