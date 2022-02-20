import bpy
import gpu
from bpy.app.handlers import persistent
from mathutils import Matrix
from gpu.types import GPUOffScreen
from gpu_extras.batch import batch_for_shader

from photogrammetry_importer.types.point import Point
from photogrammetry_importer.opengl.draw_manager import DrawManager
from photogrammetry_importer.blender_utility.object_utility import add_empty
from photogrammetry_importer.blender_utility.logging_utility import log_report


def _draw_coords_with_color(
    coords,
    colors,
    point_size,
    add_points_to_point_cloud_handle,
    reconstruction_collection=None,
    object_anchor_handle_name="OpenGL Point Cloud",
    op=None,
):

    object_anchor_handle = add_empty(
        object_anchor_handle_name, reconstruction_collection
    )
    if add_points_to_point_cloud_handle:
        object_anchor_handle["particle_coords"] = coords
        object_anchor_handle["particle_colors"] = colors
        object_anchor_handle["point_size"] = point_size
        bpy.context.scene["contains_opengl_point_clouds"] = True

    draw_manager = DrawManager.get_singleton()
    draw_manager.register_points_draw_callback(
        object_anchor_handle, coords, colors, point_size
    )
    return object_anchor_handle


def draw_points(
    points,
    point_size,
    add_points_to_point_cloud_handle,
    reconstruction_collection=None,
    object_anchor_handle_name="OpenGL Point Cloud",
    op=None,
):
    """Draw points using OpenGL."""
    log_report("INFO", "Add particle draw handlers", op)

    coords, colors = Point.split_points(points, normalize_colors=True)
    object_anchor_handle = _draw_coords_with_color(
        coords,
        colors,
        point_size,
        add_points_to_point_cloud_handle,
        reconstruction_collection,
        object_anchor_handle_name,
        op=op,
    )
    return object_anchor_handle


def draw_coords(
    coords,
    color=(0, 0, 255, 1.0),
    point_size=1,
    add_points_to_point_cloud_handle=True,
    reconstruction_collection=None,
    object_anchor_handle_name="OpenGL Coord Point Cloud",
    op=None,
):
    """Draw coordinates using OpenGL."""
    if len(color) == 3:
        color = (color[0], color[1], color[2], 1)
    assert len(color) == 4
    colors = [color for coord in coords]
    object_anchor_handle = _draw_coords_with_color(
        coords,
        colors,
        point_size,
        add_points_to_point_cloud_handle,
        reconstruction_collection,
        object_anchor_handle_name,
        op=op,
    )
    return object_anchor_handle


@persistent
def redraw_points(dummy):
    """Redraw points of the previous Blender session."""

    # This test is very cheap, so it will not cause
    # huge overheads for scenes without point clouds
    if "contains_opengl_point_clouds" in bpy.context.scene:

        log_report(
            "INFO",
            "Checking scene for missing point cloud draw handlers",
            op=None,
        )
        for obj in bpy.data.objects:
            if (
                "particle_coords" in obj
                and "particle_colors" in obj
                and "point_size" in obj
            ):
                coords = obj["particle_coords"]
                colors = obj["particle_colors"]
                point_size = obj["point_size"]

                draw_manager = DrawManager.get_singleton()
                draw_manager.register_points_draw_callback(
                    obj, coords, colors, point_size
                )

        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()
                break


def render_opengl_image(image_name, cam, coords, colors, point_size):
    """Render the given coordinates with :code:`OpenGL`."""

    render = bpy.context.scene.render

    width = render.resolution_x
    height = render.resolution_y
    # TODO Provide an option to render from the 3D view perspective
    # width = bpy.context.region.width
    # height = bpy.context.region.height

    offscreen = gpu.types.GPUOffScreen(width, height)
    with offscreen.bind():

        gpu.state.point_size_set(point_size)

        previous_depth_mask_value = gpu.state.depth_mask_get()
        previous_depth_test_value = gpu.state.depth_test_get()
        gpu.state.depth_mask_set(True)
        gpu.state.depth_test_set("LESS_EQUAL")

        frame_buffer = gpu.state.active_framebuffer_get()
        frame_buffer.clear(color=(0.0, 0.0, 0.0, 0.0), depth=1.0)

        view_matrix = cam.matrix_world.inverted()
        projection_matrix = cam.calc_matrix_camera(
            bpy.context.evaluated_depsgraph_get(), x=width, y=height
        )
        perspective_matrix = projection_matrix @ view_matrix

        gpu.matrix.load_matrix(perspective_matrix)
        gpu.matrix.load_projection_matrix(Matrix.Identity(4))

        shader = gpu.shader.from_builtin("3D_FLAT_COLOR")
        shader.bind()
        batch = batch_for_shader(
            shader, "POINTS", {"pos": coords, "color": colors}
        )
        batch.draw(shader)

        gpu.state.depth_mask_set(previous_depth_mask_value)
        gpu.state.depth_test_set(previous_depth_test_value)

        buffer = frame_buffer.read_color(0, 0, width, height, 4, 0, "UBYTE")

    offscreen.free()

    image = _create_image_lazy(image_name, width, height)
    _copy_buffer_to_pixel(buffer, image, width, height)


def _create_image_lazy(image_name, width, height):
    if image_name not in bpy.data.images:
        image = bpy.data.images.new(image_name, width, height)
    else:
        image = bpy.data.images[image_name]
        if image.size[0] != width or image.size[1] != height:
            image.scale(width, height)
    return image


def _copy_buffer_to_pixel(buffer, image, width, height):

    # According to
    #   https://developer.blender.org/D2734
    #   https://docs.blender.org/api/current/gpu.html#copy-offscreen-rendering-result-back-to-ram
    # the buffer protocol is currently not implemented for
    # gpu.types.Buffer and bpy.types.Image.pixels
    # (this makes the extraction very slow)

    # # from photogrammetry_importer.utility.timing_utility import StopWatch
    # Option 1 (faster)
    # sw = StopWatch()
    buffer.dimensions = width * height * 4
    image.pixels = [v / 255 for v in buffer]
    # log_report('INFO', 'sw.get_elapsed_time(): ' + str(sw.get_elapsed_time()))

    # Option 2 (slower)
    # sw = StopWatch()
    # buffer.dimensions = width * height * 4
    # image.pixels = (np.asarray(buffer, dtype=np.uint8) / 255).tolist()
    # log_report('INFO', 'sw.get_elapsed_time(): ' + str(sw.get_elapsed_time()))
