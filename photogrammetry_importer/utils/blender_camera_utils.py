import os
import math
import bpy
from mathutils import Vector
from collections import namedtuple

from photogrammetry_importer.utils.blender_utils import compute_camera_matrix_world
from photogrammetry_importer.utils.blender_utils import add_collection
from photogrammetry_importer.utils.blender_utils import add_obj
from photogrammetry_importer.utils.blender_animation_utils import add_transformation_animation
from photogrammetry_importer.utils.blender_animation_utils import add_camera_intrinsics_animation
from photogrammetry_importer.utils.stop_watch import StopWatch

class DummyCamera(object):
    def __init__(self):
        self.file_name = None

CameraIntrinsics = namedtuple('CameraIntrinsics', 'field_of_view shift_x shift_y')

def compute_shift(camera, relativ_to_largest_extend):
    # https://blender.stackexchange.com/questions/58235/what-are-the-units-for-camera-shift
    # This is measured however in relation to the largest dimension of the rendered frame size. 
    # So lets say you are rendering in Full HD, that is 1920 x 1080 pixel image; 
    # a frame shift if 1 unit will shift exactly 1920 pixels in any direction, that is up/down/left/right.
    
    width = camera.width 
    height = camera.height 
    p_x, p_y = camera.get_principal_point()

    if relativ_to_largest_extend:
        width_denominator = max(width, height)
        height_denominator = max(width, height)
    else:
        width_denominator = width
        height_denominator = height

    # Note, that the direction of the y coordinate is inverted 
    # (Difference between computer vision vs computer graphics coordinate system)
    shift_x = float((width / 2.0 - p_x) / float(width_denominator))
    shift_y = -float((height / 2.0 - p_y) / float(height_denominator))

    # op.report({'INFO'}, 'shift_x: ' + str(shift_x))
    # op.report({'INFO'}, 'shift_y: ' + str(shift_y))

    return shift_x, shift_y


def add_single_camera(op, camera_name, camera):
    # Add camera:
    bcamera = bpy.data.cameras.new(camera_name)

    if camera.is_panoramic():
        focal_length = 0.001 # minimal focal length
        bcamera.type = 'PANO'
        bcamera.cycles.panorama_type = camera.get_panoramic_type()
    else:
        focal_length = camera.get_focal_length()
        
    #  Adjust field of view
    bcamera.angle = camera.get_field_of_view()
    
    bcamera.shift_x, bcamera.shift_y = compute_shift(
        camera, relativ_to_largest_extend=True)

    # op.report({'INFO'}, 'focal_length: ' + str(focal_length))
    # op.report({'INFO'}, 'camera.get_calibration_mat(): ' + str(camera.get_calibration_mat()))
    # op.report({'INFO'}, 'width: ' + str(camera.width))
    # op.report({'INFO'}, 'height: ' + str(camera.height))
    # op.report({'INFO'}, 'p_x: ' + str(p_x))
    # op.report({'INFO'}, 'p_y: ' + str(p_y))

    return bcamera

def is_image_file(file_path):
    img_ext_list = ['.rgb', '.gif', '.pbm', '.pgm', '.ppm', '.pnm', '.tiff', '.tif', 
                    '.rast', '.xbm', '.jpg', '.jpeg', '.png', '.bmp', '.png',
                    '.webp', '.exr', '.hdr', '.svg']
    return os.path.splitext(file_path)[1].lower() in img_ext_list

def enhance_cameras_with_dummy_cameras(op, cameras, path_to_images):
    
    rec_image_names = [os.path.basename(camera.file_name) for camera in cameras]
    file_paths = [os.path.join(path_to_images, fn) for fn in os.listdir(path_to_images) 
                  if os.path.isfile(os.path.join(path_to_images, fn))] 
    all_image_paths = [
        image_path for image_path in file_paths
        if is_image_file(image_path)]
    non_rec_image_paths = [
        image_path for image_path in all_image_paths 
        if os.path.basename(image_path) not in rec_image_names]

    for non_rec_image_path in non_rec_image_paths:
        cam = DummyCamera()
        cam.file_name = non_rec_image_path
        cameras.append(cam)

    return cameras

def add_camera_animation(op, 
                        cameras, 
                        parent_collection, 
                        number_interpolation_frames, 
                        interpolation_type,
                        consider_missing_cameras_during_animation,
                        remove_rotation_discontinuities,
                        path_to_images):
    op.report({'INFO'}, 'Adding Camera Animation: ...')

    if len(cameras) == 0:
        return

    if consider_missing_cameras_during_animation:
        cameras = enhance_cameras_with_dummy_cameras(
            op, cameras, path_to_images)

    # Using the first reconstructed camera as template for the animated camera. The values
    # are adjusted with add_transformation_animation() and add_camera_intrinsics_animation().
    some_cam = cameras[0]
    bcamera = add_single_camera(op, "Animated Camera", some_cam)
    cam_obj = add_obj(bcamera, "Animated Camera", parent_collection)
    cameras_sorted = sorted(cameras, key=lambda camera: os.path.basename(camera.file_name))

    transformations_sorted = []
    camera_intrinsics_sorted = []
    for camera in cameras_sorted:
        if isinstance(camera, DummyCamera):
            matrix_world = None
            camera_intrinsics = None
        else:
            matrix_world = compute_camera_matrix_world(camera)
            shift_x, shift_y = compute_shift(
                camera, relativ_to_largest_extend=True)
            camera_intrinsics = CameraIntrinsics(
                camera.get_field_of_view(), shift_x, shift_y)
        
        transformations_sorted.append(matrix_world)
        camera_intrinsics_sorted.append(camera_intrinsics)

    add_transformation_animation(
        op=op,
        animated_obj_name=cam_obj.name,
        transformations_sorted=transformations_sorted, 
        number_interpolation_frames=number_interpolation_frames, 
        interpolation_type=interpolation_type,
        remove_rotation_discontinuities=remove_rotation_discontinuities)

    add_camera_intrinsics_animation(
        op=op,
        animated_obj_name=cam_obj.name,
        intrinsics_sorted=camera_intrinsics_sorted, 
        number_interpolation_frames=number_interpolation_frames
    )

def add_cameras(op, 
                cameras,
                parent_collection,
                path_to_images=None,
                add_background_images=False,
                add_image_planes=False,
                convert_camera_coordinate_system=True,
                camera_collection_name='Cameras',
                image_plane_collection_name='Image Planes',
                camera_scale=1.0,
                image_plane_transparency=0.5,
                add_image_plane_emission=True):

    """
    ======== The images are currently only shown in BLENDER RENDER ========
    ======== Make sure to enable TEXTURE SHADING in the 3D view to make the images visible ========

    :param cameras:
    :param path_to_images:
    :param add_image_planes:
    :param convert_camera_coordinate_system:
    :param camera_collection_name:
    :param image_plane_collection_name:
    :return:
    """
    op.report({'INFO'}, 'Adding Cameras: ...')
    stop_watch = StopWatch()
    camera_collection = add_collection(
        camera_collection_name, 
        parent_collection)

    if add_image_planes:
        op.report({'INFO'}, 'Adding image planes: True')
        image_planes_collection = add_collection(
            image_plane_collection_name, 
            parent_collection)
        camera_image_plane_pair_collection = add_collection(
            "Camera Image Plane Pair Collection",
            parent_collection)
    else:
        op.report({'INFO'}, 'Adding image planes: False')

    # Adding cameras and image planes:
    for index, camera in enumerate(cameras):

        # camera_name = "Camera %d" % index     # original code
        # Replace the camera name so it matches the image name (without extension)
        image_file_name_stem = os.path.splitext(os.path.basename(camera.file_name))[0]
        camera_name = image_file_name_stem + '_cam'
        bcamera = add_single_camera(op, camera_name, camera)
        camera_object = add_obj(bcamera, camera_name, camera_collection)
        matrix_world = compute_camera_matrix_world(camera)
        camera_object.matrix_world = matrix_world
        camera_object.scale *= camera_scale

        if not add_image_planes and not add_background_images:
            continue 

        use_original_image = True
        if camera.undistorted_file_name is not None:
            path_to_image = os.path.join(
                path_to_images, os.path.basename(camera.undistorted_file_name))
            if os.path.isfile(path_to_image):
                use_original_image = False

        if use_original_image:
            path_to_image = os.path.join(
                path_to_images, os.path.basename(camera.file_name))

        if not os.path.isfile(path_to_image):
            continue

        blender_image = bpy.data.images.load(path_to_image)

        if add_background_images:
            # op.report({'INFO'}, 'Adding background image for: ' + camera_name)

            camera_data = bpy.data.objects[camera_name].data
            camera_data.show_background_images = True
            background_image = camera_data.background_images.new()
            background_image.image = blender_image

        if add_image_planes and not camera.is_panoramic():
            # op.report({'INFO'}, 'Adding image plane for: ' + camera_name)

            # Group image plane and camera:
            camera_image_plane_pair_collection_current = add_collection(
                "Camera Image Plane Pair Collection %s" % image_file_name_stem,
                camera_image_plane_pair_collection)
            
            image_plane_name = image_file_name_stem + '_image_plane'

            # do not add image planes by default, this is slow !
            image_plane_obj = add_camera_image_plane(
                matrix_world, 
                blender_image, 
                camera=camera,
                name=image_plane_name,
                transparency=image_plane_transparency,
                add_image_plane_emission=add_image_plane_emission,
                image_planes_collection=image_planes_collection,
                op=op)
            
            camera_image_plane_pair_collection_current.objects.link(camera_object)
            camera_image_plane_pair_collection_current.objects.link(image_plane_obj)

    op.report({'INFO'}, 'Duration: ' + str(stop_watch.get_elapsed_time()))
    op.report({'INFO'}, 'Adding Cameras: Done')

def add_camera_image_plane(matrix_world, 
                           blender_image, 
                           camera,
                           name, 
                           transparency, 
                           add_image_plane_emission, 
                           image_planes_collection, 
                           op):
    """
    Create mesh for image plane
    """
    # op.report({'INFO'}, 'add_camera_image_plane: ...')
    # op.report({'INFO'}, 'name: ' + str(name))

    width = camera.width 
    height = camera.height 
    focal_length = camera.get_focal_length() 
    p_x, p_y = camera.get_principal_point()

    assert width is not None and height is not None

    bpy.context.scene.render.engine = 'CYCLES'
    mesh = bpy.data.meshes.new(name)
    mesh.update()
    mesh.validate()

    plane_distance = 1.0  # Distance from camera position
    # Right vector in view frustum at plane_distance:
    right = Vector((1, 0, 0)) * (width / focal_length) * plane_distance
    # Up vector in view frustum at plane_distance:
    up = Vector((0, 1, 0)) * (height / focal_length) * plane_distance
    # Camera view direction:
    view_dir = -Vector((0, 0, 1)) * plane_distance
    plane_center = view_dir
    
    shift_x, shift_y = compute_shift(
        camera, relativ_to_largest_extend=False)

    corners = ((-0.5, -0.5), (+0.5, -0.5), (+0.5, +0.5), (-0.5, +0.5))
    points = [(plane_center + (c[0] + shift_x) * right + (c[1] + shift_y) * up)[0:3] for c in corners]
    mesh.from_pydata(points, [], [[0, 1, 2, 3]])
    mesh.uv_layers.new()
    
    # Add mesh to new image plane object:
    mesh_obj = add_obj(mesh, name, image_planes_collection)

    image_plane_material = bpy.data.materials.new(
        name="image_plane_material")
    # Adds "Principled BSDF" and a "Material Output" node
    image_plane_material.use_nodes = True
    
    nodes = image_plane_material.node_tree.nodes
    links = image_plane_material.node_tree.links
    
    shader_node_tex_image = nodes.new(type='ShaderNodeTexImage')
    shader_node_principled_bsdf = nodes.get('Principled BSDF')
    shader_node_principled_bsdf.inputs['Alpha'].default_value = transparency
    
    links.new(
        shader_node_tex_image.outputs['Color'], 
        shader_node_principled_bsdf.inputs['Base Color'])

    if add_image_plane_emission:
        links.new(
            shader_node_tex_image.outputs['Color'], 
            shader_node_principled_bsdf.inputs['Emission'])
    
    shader_node_tex_image.image = blender_image
    
    # Assign it to object
    if mesh_obj.data.materials:
        # assign to 1st material slot
        mesh_obj.data.materials[0] = image_plane_material
    else:
        # no slots
        mesh_obj.data.materials.append(image_plane_material)
    
    mesh_obj.matrix_world = matrix_world
    mesh.update()
    mesh.validate()
    # op.report({'INFO'}, 'add_camera_image_plane: Done')
    return mesh_obj

def set_principal_point_for_cameras(cameras, default_pp_x, default_pp_y, op):
    
    if not math.isnan(default_pp_x) and not math.isnan(default_pp_y):
        op.report({'WARNING'}, 'Setting principal points to default values!')
    else:
        op.report({'WARNING'}, 'Setting principal points to image centers!')
        default_pp_x = cameras[0].width / 2.0
        default_pp_y = cameras[0].height / 2.0
    
    for camera in cameras:
        if not camera.is_principal_point_initialized():
            camera.set_principal_point([default_pp_x, default_pp_y])

def principal_points_initialized(cameras):
    principal_points_initialized = True
    for camera in cameras:
        if not camera.is_principal_point_initialized():
            principal_points_initialized = False
            break
    return principal_points_initialized