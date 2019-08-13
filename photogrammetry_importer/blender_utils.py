"""
Collection of convenience functions to add and modify objects in Blender.
"""

import os
import math
import time
import bpy 
from mathutils import Matrix
from mathutils import Vector
from mathutils import Quaternion

from photogrammetry_importer.stop_watch import StopWatch

def invert_y_and_z_axis(input_matrix_or_vector):
    """
    VisualSFM and Blender use coordinate systems, which differ in the y and z coordinate
    This Function inverts the y and the z coordinates in the corresponding matrix / vector entries
    Iinvert y and z axis <==> rotation by 180 degree around the x axis
    """
    output_matrix_or_vector = input_matrix_or_vector.copy()
    output_matrix_or_vector[1] = -output_matrix_or_vector[1]
    output_matrix_or_vector[2] = -output_matrix_or_vector[2]
    return output_matrix_or_vector

def get_world_matrix_from_translation_vec(translation_vec, rotation):
    t = Vector(translation_vec).to_4d()
    camera_rotation = Matrix()
    for row in range(3):
        camera_rotation[row][0:3] = rotation[row]

    camera_rotation.transpose()  # = Inverse rotation

    camera_center = -(camera_rotation @ t)  # Camera position in world coordinates
    camera_center[3] = 1.0

    camera_rotation = camera_rotation.copy()
    camera_rotation.col[3] = camera_center  # Set translation to camera position
    return camera_rotation

def compute_camera_matrix_world(camera):
        translation_vec = camera.get_translation_vec()
        rotation_mat = camera.get_rotation_mat()
        # Transform the camera coordinate system from computer vision camera coordinate frames 
        # to the computer vision camera coordinate frames
        # That is, rotate the camera matrix around the x axis by 180 degrees,
        # i.e. invert the x and y axis
        rotation_mat = invert_y_and_z_axis(rotation_mat)
        translation_vec = invert_y_and_z_axis(translation_vec)
        return get_world_matrix_from_translation_vec(translation_vec, rotation_mat)

def add_obj(data, obj_name, collection=None):
    
    if collection is None:
        collection = bpy.context.collection

    new_obj = bpy.data.objects.new(obj_name, data)
    collection.objects.link(new_obj)
    new_obj.select_set(state=True)

    if bpy.context.view_layer.objects.active is None or bpy.context.view_layer.objects.active.mode == 'OBJECT':
        bpy.context.view_layer.objects.active = new_obj
    return new_obj

def add_collection(collection_name, parent_collection=None):

    if parent_collection is None:
        parent_collection = bpy.context.collection

    new_collection = bpy.data.collections.new(collection_name)
    parent_collection.children.link(new_collection)

    return new_collection

def add_points_as_mesh(op, points, add_points_as_particle_system, mesh_type, point_extent, add_particle_color_emission, reconstruction_collection):
    op.report({'INFO'}, 'Adding Points: ...')
    stop_watch = StopWatch()
    particle_obj_name = "Particle Shape" 
    point_cloud_obj_name = "Point Cloud"
    mesh = bpy.data.meshes.new(point_cloud_obj_name)
    mesh.update()
    mesh.validate()

    point_world_coordinates = [tuple(point.coord) for point in points]

    mesh.from_pydata(point_world_coordinates, [], [])
    meshobj = add_obj(mesh, point_cloud_obj_name, reconstruction_collection)

    if add_points_as_particle_system:
        op.report({'INFO'}, 'Representing Points in the Point Cloud with Meshes: True')
        op.report({'INFO'}, 'Mesh Type: ' + str(mesh_type))

        # The default size of elements added with 
        #   primitive_cube_add, primitive_uv_sphere_add, etc. is (2,2,2)
        point_scale = point_extent * 0.5 

        bpy.ops.object.select_all(action='DESELECT')
        if mesh_type == "PLANE":
            bpy.ops.mesh.primitive_plane_add(size=point_scale)
        elif mesh_type == "CUBE":
            bpy.ops.mesh.primitive_cube_add(size=point_scale)
        elif mesh_type == "SPHERE":
            bpy.ops.mesh.primitive_uv_sphere_add(radius=point_scale)
        else:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=point_scale)
        particle_obj = bpy.context.object
        particle_obj.name = particle_obj_name
        reconstruction_collection.objects.link(particle_obj)
        bpy.context.collection.objects.unlink(particle_obj)

        if add_points_as_particle_system:
            
            material_name = "PointCloudMaterial"
            material = bpy.data.materials.new(name=material_name)
            particle_obj.data.materials.append(material)
            
            # enable cycles, otherwise the material has no nodes
            bpy.context.scene.render.engine = 'CYCLES'
            material.use_nodes = True
            node_tree = material.node_tree

            # Print all available nodes with:
            # bpy.data.materials['material_name'].node_tree.nodes.keys()

            if 'Material Output' in node_tree.nodes:    # is created by default
                material_output_node = node_tree.nodes['Material Output']
            else:
                material_output_node = node_tree.nodes.new('ShaderNodeOutputMaterial')

            if 'Principled BSDF' in node_tree.nodes:       # is created by default
                principled_bsdf_node = node_tree.nodes['Principled BSDF']
            else:
                principled_bsdf_node = node_tree.nodes.new("ShaderNodeBsdfPrincipled")
            node_tree.links.new(
                principled_bsdf_node.outputs['BSDF'], 
                material_output_node.inputs['Surface'])
            
            if 'Image Texture' in node_tree.nodes:
                image_texture_node = node_tree.nodes['Image Texture']
            else:
                image_texture_node = node_tree.nodes.new("ShaderNodeTexImage")

            # Add links for base color and emission to improve color visibility
            node_tree.links.new(
                image_texture_node.outputs['Color'], 
                principled_bsdf_node.inputs['Base Color'])
            if add_particle_color_emission:
            	node_tree.links.new(
                    image_texture_node.outputs['Color'], 
                    principled_bsdf_node.inputs['Emission'])
            
            vis_image_height = 1
            
            # To view the texture we set the height of the texture to vis_image_height 
            image = bpy.data.images.new(
                'ParticleColor', 
                len(point_world_coordinates), 
                vis_image_height)
            
            # working on a copy of the pixels results in a MASSIVE performance speed
            local_pixels = list(image.pixels[:])
            
            num_points = len(points)
            
            for j in range(vis_image_height):
                for point_index, point in enumerate(points):
                    column_offset = point_index * 4     # (R,G,B,A)
                    row_offset = j * 4 * num_points
                    color = point.color 
                    # Order is R,G,B, opacity
                    local_pixels[row_offset + column_offset] = color[0] / 255.0
                    local_pixels[row_offset + column_offset + 1] = color[1] / 255.0
                    local_pixels[row_offset + column_offset + 2] = color[2] / 255.0
                    # opacity (0 = transparent, 1 = opaque)
                    #local_pixels[row_offset + column_offset + 3] = 1.0    # already set by default   
                
            image.pixels = local_pixels[:] 
            
            image_texture_node.image = image
            particle_info_node = node_tree.nodes.new('ShaderNodeParticleInfo')
            divide_node = node_tree.nodes.new('ShaderNodeMath')
            divide_node.operation = 'DIVIDE'
            node_tree.links.new(
                particle_info_node.outputs['Index'], 
                divide_node.inputs[0])
            divide_node.inputs[1].default_value = num_points
            shader_node_combine = node_tree.nodes.new('ShaderNodeCombineXYZ')
            node_tree.links.new(
                divide_node.outputs['Value'], 
                shader_node_combine.inputs['X'])
            node_tree.links.new(
                shader_node_combine.outputs['Vector'], 
                image_texture_node.inputs['Vector'])
            
            if len(meshobj.particle_systems) == 0:
                meshobj.modifiers.new("particle sys", type='PARTICLE_SYSTEM')
                particle_sys = meshobj.particle_systems[0]
                settings = particle_sys.settings
                settings.type = 'HAIR'
                settings.use_advanced_hair = True
                settings.emit_from = 'VERT'
                settings.count = len(point_world_coordinates)
                # The final object extent is hair_length * obj.scale 
                settings.hair_length = 100           # This must not be 0
                settings.use_emit_random = False
                settings.render_type = 'OBJECT'
                settings.instance_object = particle_obj
            
        bpy.context.view_layer.update()
    else:
        op.report({'INFO'}, 'Representing Points in the Point Cloud with Meshes: False')
    op.report({'INFO'}, 'Duration: ' + str(stop_watch.get_elapsed_time()))
    op.report({'INFO'}, 'Adding Points: Done')

def add_single_camera(op, camera_name, camera):
    # Add camera:
    bcamera = bpy.data.cameras.new(camera_name)

    focal_length = camera.get_focal_length()

    #  Adjust field of view
    assert camera.width is not None and camera.height is not None
    bcamera.angle = math.atan(max(camera.width, camera.height) / (focal_length * 2.0)) * 2.0

    # Adjust principal point
    p_x, p_y = camera.get_principal_point()
    
    # https://blender.stackexchange.com/questions/58235/what-are-the-units-for-camera-shift
    # This is measured however in relation to the largest dimension of the rendered frame size. 
    # So lets say you are rendering in Full HD, that is 1920 x 1080 pixel image; 
    # a frame shift if 1 unit will shift exactly 1920 pixels in any direction, that is up/down/left/right.
    max_extent = max(camera.width, camera.height)
    bcamera.shift_x = (camera.width / 2.0 - p_x) / float(max_extent)
    bcamera.shift_y = (camera.height / 2.0 - p_y) / float(max_extent)

    # op.report({'INFO'}, 'focal_length: ' + str(focal_length))
    # op.report({'INFO'}, 'camera.get_calibration_mat(): ' + str(camera.get_calibration_mat()))
    # op.report({'INFO'}, 'width: ' + str(camera.width))
    # op.report({'INFO'}, 'height: ' + str(camera.height))
    # op.report({'INFO'}, 'p_x: ' + str(p_x))
    # op.report({'INFO'}, 'p_y: ' + str(p_y))

    return bcamera

def remove_quaternion_discontinuities(cam_obj):

    # the interpolation of quaternions may lead to discontinuities 
    # if the quaternions show different signs

    # https://blender.stackexchange.com/questions/58866/keyframe-interpolation-instability
    action = cam_obj.animation_data.action

    # quaternion curves
    fqw = action.fcurves.find('rotation_quaternion', index = 0)
    fqx = action.fcurves.find('rotation_quaternion', index = 1)
    fqy = action.fcurves.find('rotation_quaternion', index = 2)
    fqz = action.fcurves.find('rotation_quaternion', index = 3)  

    # invert quaternion so that interpolation takes the shortest path
    if (len(fqw.keyframe_points) > 0):
        current_quat = Quaternion((
            fqw.keyframe_points[0].co[1],
            fqx.keyframe_points[0].co[1],
            fqy.keyframe_points[0].co[1],
            fqz.keyframe_points[0].co[1]))

        for i in range(len(fqw.keyframe_points)-1):
            last_quat = current_quat
            current_quat = Quaternion((
                fqw.keyframe_points[i+1].co[1],
                fqx.keyframe_points[i+1].co[1],
                fqy.keyframe_points[i+1].co[1],
                fqz.keyframe_points[i+1].co[1]))

            if last_quat.dot(current_quat) < 0:
                current_quat.negate()
                fqw.keyframe_points[i+1].co[1] = -fqw.keyframe_points[i+1].co[1]
                fqx.keyframe_points[i+1].co[1] = -fqx.keyframe_points[i+1].co[1]
                fqy.keyframe_points[i+1].co[1] = -fqy.keyframe_points[i+1].co[1]
                fqz.keyframe_points[i+1].co[1] = -fqz.keyframe_points[i+1].co[1]


class DummyCamera(object):
    def __init__(self):
        self.file_name = None

def is_image_file(fn):
    image_ext = ['.jpg', '.png']
    return os.path.splitext(fn)[1].lower() in image_ext

def enhance_cameras_with_dummy_cameras(cameras, path_to_images):
    all_image_names = [
        image_name for image_name in os.listdir(path_to_images) 
        if is_image_file(image_name)]
    rec_image_names = [camera.file_name for camera in cameras]
    non_rec_image_names = [
        image_name for image_name in all_image_names 
        if image_name not in rec_image_names]
    for non_rec_image_name in non_rec_image_names:
        cam = DummyCamera()
        cam.file_name = non_rec_image_name
        cameras.append(cam)
    return cameras

def set_fcurve_interpolation(some_obj, interpolation_type='LINEAR'):

    # interpolation_string: ['CONSTANT', 'LINEAR', 'BEZIER', 'SINE',
    # 'QUAD', 'CUBIC', 'QUART', 'QUINT', 'EXPO', 'CIRC',
    # 'BACK', 'BOUNCE', 'ELASTIC']
    fcurves = some_obj.animation_data.action.fcurves
    for fcurve in fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = interpolation_type


def add_camera_animation(op, 
                        cameras, 
                        parent_collection, 
                        number_interpolation_frames, 
                        interpolation_type,
                        consider_missing_cameras_during_animation,
                        path_to_images):
    op.report({'INFO'}, 'Adding Camera Animation: ...')

    if consider_missing_cameras_during_animation:
        cameras = enhance_cameras_with_dummy_cameras(
            cameras, path_to_images)

    some_cam = cameras[0]
    bcamera = add_single_camera(op, "Animated Camera", some_cam)
    cam_obj = add_obj(bcamera, "Animated Camera", parent_collection)

    scn = bpy.context.scene
    scn.frame_start = 0
    step_size = number_interpolation_frames + 1
    scn.frame_end = step_size * len(cameras) 

    cameras_sorted = sorted(cameras, key=lambda x: x.file_name)

    for index, camera in enumerate(cameras_sorted):
        #op.report({'INFO'}, 'index: ' + str(index))

        current_keyframe_index = index * step_size

        if isinstance(camera, DummyCamera):
            continue 

        cam_obj.matrix_world = compute_camera_matrix_world(camera)

        cam_obj.keyframe_insert(
            data_path="location", 
            index=-1, 
            frame=current_keyframe_index)

        # Don't use euler rotations, they show too many discontinuties
        #cam_obj.keyframe_insert(
        #   data_path="rotation_euler", 
        #   index=-1, 
        #   frame=current_keyframe_index)

        cam_obj.rotation_mode = 'QUATERNION'
        cam_obj.keyframe_insert(
            data_path="rotation_quaternion", 
            index=-1, 
            frame=current_keyframe_index)
        # q and -q represent the same rotation
        remove_quaternion_discontinuities(cam_obj)

        set_fcurve_interpolation(
            cam_obj,
            interpolation_type)

def add_cameras(op, 
                cameras,
                parent_collection,
                path_to_images=None,
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

        start_time = stop_watch.get_elapsed_time()
        
        # camera_name = "Camera %d" % index     # original code
        # Replace the camera name so it matches the image name (without extension)
        image_file_name_stem = os.path.splitext(os.path.basename(camera.file_name))[0]
        camera_name = image_file_name_stem + '_cam'
        bcamera = add_single_camera(op, camera_name, camera)
        camera_object = add_obj(bcamera, camera_name, camera_collection)
        matrix_world = compute_camera_matrix_world(camera)
        camera_object.matrix_world = matrix_world
        camera_object.scale *= camera_scale

        if add_image_planes:
            path_to_image = os.path.join(path_to_images, os.path.basename(camera.file_name))
            
            if os.path.isfile(path_to_image):
                
                op.report({'INFO'}, 'Adding image plane for: ' + str(path_to_image))

                # Group image plane and camera:
                camera_image_plane_pair_collection_current = add_collection(
                    "Camera Image Plane Pair Collection %s" % image_file_name_stem,
                    camera_image_plane_pair_collection)
                
                image_plane_name = image_file_name_stem + '_image_plane'
                px, py = camera.get_principal_point()

                # do not add image planes by default, this is slow !
                image_plane_obj = add_camera_image_plane(
                    matrix_world, 
                    path_to_image, 
                    camera.width, 
                    camera.height, 
                    camera.get_focal_length(), 
                    px=px,
                    py=py,
                    name=image_plane_name,
                    transparency=image_plane_transparency,
                    add_image_plane_emission=add_image_plane_emission,
                    image_planes_collection=image_planes_collection,
                    op=op)
                
                camera_image_plane_pair_collection_current.objects.link(camera_object)
                camera_image_plane_pair_collection_current.objects.link(image_plane_obj)

        end_time = stop_watch.get_elapsed_time()

    op.report({'INFO'}, 'Duration: ' + str(stop_watch.get_elapsed_time()))
    op.report({'INFO'}, 'Adding Cameras: Done')

def add_camera_image_plane(matrix_world, path_to_image, width, height, focal_length, px, py, name, transparency, add_image_plane_emission, image_planes_collection, op):
    """
    Create mesh for image plane
    """
    op.report({'INFO'}, 'add_camera_image_plane: ...')
    op.report({'INFO'}, 'name: ' + str(name))

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
    
    relative_shift_x = float((width / 2.0 - px) / float(width))
    relative_shift_y = float((height / 2.0 - py) / float(height))
    
    op.report({'INFO'}, 'relative_shift_x: ' + str(relative_shift_x))
    op.report({'INFO'}, 'relative_shift_y:' + str(relative_shift_y))

    corners = ((-0.5, -0.5), (+0.5, -0.5), (+0.5, +0.5), (-0.5, +0.5))
    points = [(plane_center + (c[0] + relative_shift_x) * right + (c[1] + relative_shift_y) * up)[0:3] for c in corners]
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
    
    bimage = bpy.data.images.load(path_to_image)
    shader_node_tex_image.image = bimage
    
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
    op.report({'INFO'}, 'add_camera_image_plane: Done')
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

def adjust_render_settings_if_possible(op, cameras):
    
    possible = True
    width = cameras[0].width
    height = cameras[0].height
    for cam in cameras:
        if cam.width != width or cam.height != height:
            possible = False
            break
    if possible:
        bpy.context.scene.render.resolution_x = width
        bpy.context.scene.render.resolution_y = height
