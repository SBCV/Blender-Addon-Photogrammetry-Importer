import bpy
import os
from mathutils import Matrix, Vector
import math
from math import radians

from bpy.props import (CollectionProperty,
                       StringProperty,
                       BoolProperty,
                       EnumProperty,
                       FloatProperty,
                       )
                       
from bpy_extras.io_utils import (ImportHelper,
                                 ExportHelper,
                                 axis_conversion)

def get_world_matrix_from_translation_vec(translation_vec, rotation):
    t = Vector(translation_vec).to_4d()
    camera_rotation = Matrix()
    for row in range(3):
        camera_rotation[row][0:3] = rotation[row]

    camera_rotation.transpose()  # = Inverse rotation

    camera_center = -(camera_rotation * t)  # Camera position in world coordinates
    camera_center[3] = 1.0

    camera_rotation = camera_rotation.copy()
    camera_rotation.col[3] = camera_center  # Set translation to camera position
    return camera_rotation

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

def add_obj(data, obj_name):
    scene = bpy.context.scene

    for obj in scene.objects:
        obj.select = False

    new_obj = bpy.data.objects.new(obj_name, data)
    scene.objects.link(new_obj)
    new_obj.select = True

    if scene.objects.active is None or scene.objects.active.mode == 'OBJECT':
        scene.objects.active = new_obj
    return new_obj

def set_object_parent(child_object_name, parent_object_name, keep_transform=False):
    child_object_name.parent = parent_object_name
    if keep_transform:
        child_object_name.matrix_parent_inverse = parent_object_name.matrix_world.inverted()

def add_empty(empty_name):
    empty_obj = bpy.data.objects.new(empty_name, None)
    bpy.context.scene.objects.link(empty_obj)
    return empty_obj

def add_points_as_mesh(points):
    name = "Point_Cloud"
    mesh = bpy.data.meshes.new(name)
    mesh.update()
    mesh.validate()

    points = [tuple(point.coord) for point in points]

    mesh.from_pydata(points, [], [])
    meshobj = add_obj(mesh, name)

    # TODO replace matrix with identity matrix
    meshobj.matrix_world = Matrix.Rotation(radians(0), 4, 'X')
    
def add_cameras(cameras, path_to_images=None,
                add_image_planes=False,
                convert_camera_coordinate_system=True,
                cameras_parent='Cameras',
                camera_group_name='Camera Group',
                image_planes_parent='Image Planes',
                image_plane_group_name='Image Plane Group'):

    """
    ======== The images are currently only shown in BLENDER RENDER ========
    ======== Make sure to enable TEXTURE SHADING in the 3D view to make the images visible ========

    :param cameras:
    :param path_to_images:
    :param add_image_planes:
    :param convert_camera_coordinate_system:
    :param cameras_parent:
    :param camera_group_name:
    :param image_plane_group_name:
    :return:
    """

    cameras_parent = add_empty(cameras_parent)
    camera_group = bpy.data.groups.new(camera_group_name)

    if add_image_planes:
        image_planes_parent = add_empty(image_planes_parent)
        image_planes_group = bpy.data.groups.new(image_plane_group_name)

    # Adding cameras and image planes:
    for index, camera in enumerate(cameras):

        assert camera.width is not None and camera.height is not None

        # camera_name = "Camera %d" % index     # original code
        # Replace the camera name so it matches the image name (without extension)
        image_file_name_stem = os.path.splitext(os.path.basename(camera.file_name))[0]
        camera_name = image_file_name_stem + '_cam'

        focal_length = camera.calibration_mat[0][0]

        # Add camera:
        bcamera = bpy.data.cameras.new(camera_name)
        bcamera.angle_x = math.atan(camera.width / (focal_length * 2.0)) * 2.0
        bcamera.angle_y = math.atan(camera.height / (focal_length * 2.0)) * 2.0
        camera_object = add_obj(bcamera, camera_name)

        translation_vec = camera.get_translation_vec()
        rotation_mat = camera.get_rotation_mat()
        # Transform the camera coordinate system from computer vision camera coordinate frames to the computer
        # vision camera coordinate frames
        # That is, rotate the camera matrix around the x axis by 180 degree, i.e. invert the x and y axis
        rotation_mat = invert_y_and_z_axis(rotation_mat)
        translation_vec = invert_y_and_z_axis(translation_vec)
        camera_object.matrix_world = get_world_matrix_from_translation_vec(translation_vec, rotation_mat)
        set_object_parent(camera_object, cameras_parent, keep_transform=True)
        camera_group.objects.link(camera_object)

        if add_image_planes:

            # Group image plane and camera:
            camera_image_plane_pair = bpy.data.groups.new(
                "Camera Image Plane Pair Group %s" % image_file_name_stem)
            camera_image_plane_pair.objects.link(camera_object)

            image_plane_name = image_file_name_stem + '_image_plane'
            # do not add image planes by default, this is slow !
            bimage = bpy.data.images.load(os.path.join(path_to_images, camera.file_name))
            image_plane_obj = add_camera_image_plane(
                rotation_mat, translation_vec, bimage, camera.width, 
                camera.height, focal_length, name=image_plane_name)
            camera_image_plane_pair.objects.link(image_plane_obj)

            set_object_parent(image_plane_obj, image_planes_parent, keep_transform=True)
            image_planes_group.objects.link(image_plane_obj)

def add_camera_image_plane(rotation_mat, translation_vec, bimage, width, height, focal_length, name):
    """
    Create mesh for image plane
    """
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

    corners = ((-0.5, -0.5),
               (+0.5, -0.5),
               (+0.5, +0.5),
               (-0.5, +0.5))
    points = [(plane_center + c[0] * right + c[1] * up)[0:3] for c in corners]
    mesh.from_pydata(points, [], [[0, 1, 2, 3]])

    # Assign image to face of image plane:
    uvmap = mesh.uv_textures.new()
    face = uvmap.data[0]
    face.image = bimage

    # Add mesh to new image plane object:
    mesh_obj = add_obj(mesh, name)

    image_plane_material = bpy.data.materials.new(name="image_plane_material")
    image_plane_material.use_shadeless = True

    # Assign it to object
    if mesh_obj.data.materials:
        # assign to 1st material slot
        mesh_obj.data.materials[0] = image_plane_material
    else:
        # no slots
        mesh_obj.data.materials.append(image_plane_material)
    world_matrix = get_world_matrix_from_translation_vec(translation_vec, rotation_mat)
    mesh_obj.matrix_world = world_matrix
    mesh.update()
    mesh.validate()
    return mesh_obj


class ImportNVM(bpy.types.Operator, ImportHelper):
    """Load a NVM file"""
    bl_idname = "import_scene.nvm"
    bl_label = "Import NVM"
    bl_options = {'UNDO'}

    files = CollectionProperty(name="File Path",
                          description="File path used for importing "
                                      "the NVM file",
                          type=bpy.types.OperatorFileListElement)

    directory = StringProperty()

    filename_ext = ".nvm"
    filter_glob = StringProperty(default="*.nvm", options={'HIDDEN'})

    def execute(self, context):
        paths = [os.path.join(self.directory, name.name)
                 for name in self.files]
        if not paths:
            paths.append(self.filepath)

        from nvm_import.nvm_file_handler import NVMFileHandler

        for path in paths:
            
            path_to_images = os.path.dirname(path)
            cameras, points = NVMFileHandler.parse_nvm_file(path)
            cameras = NVMFileHandler.parse_camera_image_files(cameras, path_to_images)
            print(len(cameras))
            print(len(points))
            add_points_as_mesh(points)
            add_cameras(cameras, path_to_images=path_to_images, add_image_planes=True)

        return {'FINISHED'}
