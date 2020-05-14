import bpy
import bgl
import gpu
from mathutils import Matrix
from gpu.types import GPUOffScreen
from gpu_extras.batch import batch_for_shader
from photogrammetry_importer.opengl.visualization_utils import DrawManager


def render_opengl_image(image_name, cam, point_size):
    draw_manager = DrawManager.get_singleton()
    coords, colors = draw_manager.get_coords_and_colors()

    scene = bpy.context.scene
    render = bpy.context.scene.render

    width = render.resolution_x
    height = render.resolution_y
    # TODO Provide an option to render from the 3D view perspective
    # width = bpy.context.region.width
    # height = bpy.context.region.height

    offscreen = gpu.types.GPUOffScreen(width, height)
    with offscreen.bind():

        bgl.glPointSize(point_size)
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

    image = create_image_lazy(image_name, width, height)
    copy_buffer_to_pixel(buffer, image)


def create_image_lazy(image_name, width, height):
    if image_name not in bpy.data.images:
        image = bpy.data.images.new(image_name, width, height)
    else:
        image = bpy.data.images[image_name]
        if image.size[0] != width or image.size[1] != height:
            image.scale(width, height)
    return image


def copy_buffer_to_pixel(buffer, image):

    # According to 
    #   https://developer.blender.org/D2734
    #   https://docs.blender.org/api/current/gpu.html#copy-offscreen-rendering-result-back-to-ram
    # the buffer protocol is currently not implemented for 
    # bgl.Buffer and bpy.types.Image.pixels
    # (this makes the extraction very slow)
    
    # # from photogrammetry_importer.utils.stop_watch import StopWatch
    # Option 1 (faster)
    # sw = StopWatch()
    image.pixels = [v / 255 for v in buffer]
    # print('sw.get_elapsed_time()', sw.get_elapsed_time())

    # Option 2 (slower)
    # sw = StopWatch()
    # image.pixels = (np.asarray(buffer, dtype=np.uint8) / 255).tolist()
    # print('sw.get_elapsed_time()', sw.get_elapsed_time())
