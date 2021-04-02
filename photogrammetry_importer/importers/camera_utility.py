import os
import bpy
import colorsys
from mathutils import Matrix
from mathutils import Vector

from photogrammetry_importer.blender_utility.object_utility import (
    add_collection,
    add_obj,
)

from photogrammetry_importer.opengl.utility import draw_coords
from photogrammetry_importer.utility.timing_utility import StopWatch
from photogrammetry_importer.utility.type_utility import is_int
from photogrammetry_importer.blender_utility.logging_utility import log_report


def compute_principal_point_shift(camera, relativ_to_largest_extend):
    """Return the shift of the principal point in the 3D view port."""
    # https://blender.stackexchange.com/questions/58235/what-are-the-units-for-camera-shift

    width = camera.width
    height = camera.height
    p_x, p_y = camera.get_principal_point()

    if relativ_to_largest_extend:
        width_denominator = max(width, height)
        height_denominator = max(width, height)
    else:
        width_denominator = width
        height_denominator = height

    # Note, that the direction of the y coordinate is inverted - reflecting the
    # difference between computer vision vs computer graphics coordinate
    # system.
    shift_x = float((width / 2.0 - p_x) / float(width_denominator))
    shift_y = -float((height / 2.0 - p_y) / float(height_denominator))

    # log_report('INFO', 'shift_x: ' + str(shift_x), op)
    # log_report('INFO', 'shift_y: ' + str(shift_y), op)

    return shift_x, shift_y


def adjust_render_settings_if_possible(cameras, op=None):
    """Adjust the render settings according to the camera parameters."""

    if len(cameras) == 0:
        return

    possible = True
    width = cameras[0].width
    height = cameras[0].height

    # Check if the cameras have same resolution
    for cam in cameras:
        if cam.width != width or cam.height != height:
            possible = False
            break

    if possible:
        bpy.context.scene.render.resolution_x = width
        bpy.context.scene.render.resolution_y = height
    else:
        log_report(
            "WARNING",
            "Adjustment of render settings not possible, "
            + "since the reconstructed cameras show different resolutions.",
            op,
        )


def _add_camera_data(camera, camera_name):
    """Add a camera as Blender data entity."""
    bcamera = bpy.data.cameras.new(camera_name)
    if camera.is_panoramic():
        bcamera.type = "PANO"
        bcamera.cycles.panorama_type = camera.get_panoramic_type()
    #  Adjust field of view
    bcamera.angle = camera.get_field_of_view()
    bcamera.shift_x, bcamera.shift_y = compute_principal_point_shift(
        camera, relativ_to_largest_extend=True
    )
    return bcamera


def add_camera_object(
    camera, camera_name, camera_collection, copy_matrix_world=True
):
    """Add a camera as Blender object."""
    bcamera = _add_camera_data(camera, camera_name)
    camera_object = add_obj(bcamera, camera_name, camera_collection)
    if copy_matrix_world:
        camera_object.matrix_world = compute_camera_matrix_world(camera)
    return camera_object


def _color_from_value(val, min_val, max_val):
    # source: http://stackoverflow.com/questions/10901085/range-values-to-pseudocolor

    # convert val in range minval..maxval to the range 0..120 degrees which
    # correspond to the colors red..green in the HSV colorspace

    h = (float(val - min_val) / (max_val - min_val)) * 120
    # convert hsv color (h, 1, 1) to its rgb equivalent
    # note: the hsv_to_rgb() function expects h to be in the range 0..1 and not
    # in 0..360
    r, g, b = colorsys.hsv_to_rgb(h / 360, 1.0, 1.0)
    return r, g, b, 1


def _get_camera_obj_gui_str(camera):
    """Get a string suitable for Blender's GUI describing the camera."""
    # Replace special characters
    # image_fp_clean = image_fp.replace("/", "_").replace("\\", "_").replace(":", "_")
    image_fp_stem = os.path.splitext(camera.get_relative_fp())[0]
    # Blender supports only object names with length 63
    # However, we need also space for additional suffixes
    image_fp_suffix = image_fp_stem[-40:]
    return image_fp_suffix


def invert_y_and_z_axis(input_matrix_or_vector):
    """Invert the y and z axis of a given matrix or vector.

    Many SfM / MVS libraries use coordinate systems that differ from Blender's
    coordinate system in the y and the z coordinate. This function inverts the
    y and the z coordinates in the corresponding matrix / vector entries, which
    is equivalent to a rotation by 180 degree around the x axis.
    """
    output_matrix_or_vector = input_matrix_or_vector.copy()
    output_matrix_or_vector[1] = -output_matrix_or_vector[1]
    output_matrix_or_vector[2] = -output_matrix_or_vector[2]
    return output_matrix_or_vector


def _get_world_matrix_from_translation_vec(translation_vec, rotation):
    t = Vector(translation_vec).to_4d()
    camera_rotation = Matrix()
    for row in range(3):
        camera_rotation[row][0:3] = rotation[row]

    camera_rotation.transpose()  # = Inverse rotation

    # Camera position in world coordinates
    camera_center = -(camera_rotation @ t)
    camera_center[3] = 1.0

    camera_rotation = camera_rotation.copy()
    camera_rotation.col[
        3
    ] = camera_center  # Set translation to camera position
    return camera_rotation


def compute_camera_matrix_world(camera, convert_coordinate_system=True):
    """Compute Blender's :code:`matrix_world` for a given camera."""
    translation_vec = camera.get_translation_vec()
    rotation_mat = camera.get_rotation_as_rotation_mat()
    if convert_coordinate_system:
        # Transform the camera coordinate system from computer vision camera
        # coordinate frames to the computer vision camera coordinate frames.
        # That is, rotate the camera matrix around the x axis by 180 degrees,
        # i.e. invert the x and y axis.
        rotation_mat = invert_y_and_z_axis(rotation_mat)
        translation_vec = invert_y_and_z_axis(translation_vec)
    return _get_world_matrix_from_translation_vec(
        translation_vec, rotation_mat
    )


def add_cameras(
    cameras,
    parent_collection,
    add_background_images=False,
    add_image_planes=False,
    add_depth_maps_as_point_cloud=True,
    convert_camera_coordinate_system=True,
    camera_collection_name="Cameras",
    image_plane_collection_name="Image Planes",
    depth_map_collection_name="Depth Maps",
    camera_scale=1.0,
    image_plane_transparency=0.5,
    add_image_plane_emission=True,
    depth_map_point_size=1,
    use_default_depth_map_color=False,
    depth_map_default_color=(1.0, 0.0, 0.0),
    depth_map_display_sparsity=10,
    depth_map_id_or_name_str="",
    op=None,
):
    """Add a set of reconstructed cameras to Blender's 3D view port."""
    log_report("INFO", "Adding Cameras: ...", op)
    stop_watch = StopWatch()
    camera_collection = add_collection(
        camera_collection_name, parent_collection
    )

    if add_image_planes:
        log_report("INFO", "Adding image planes: True", op)
        image_planes_collection = add_collection(
            image_plane_collection_name, parent_collection
        )
        camera_image_plane_pair_collection = add_collection(
            "Camera Image Plane Pair Collection", parent_collection
        )
    else:
        log_report("INFO", "Adding image planes: False", op)

    if add_depth_maps_as_point_cloud:
        log_report("INFO", "Adding depth maps as point cloud: True", op)
        depth_map_collection = add_collection(
            depth_map_collection_name, parent_collection
        )
        camera_depth_map_pair_collection = add_collection(
            "Camera Depth Map Pair Collection", parent_collection
        )
    else:
        log_report("INFO", "Adding depth maps as point cloud: False", op)

    depth_map_id_or_name_str = depth_map_id_or_name_str.rstrip()
    if depth_map_id_or_name_str == "":
        depth_map_indices = None
    else:
        depth_map_indices = []
        cam_rel_fp_to_idx = {}
        for idx, camera in enumerate(cameras):
            rel_fp = camera.get_relative_fp()
            cam_rel_fp_to_idx[rel_fp] = idx
        for id_or_name in depth_map_id_or_name_str.split(" "):
            if is_int(id_or_name):
                depth_map_indices.append(int(id_or_name))
            else:
                if id_or_name in cam_rel_fp_to_idx:
                    depth_map_indices.append(cam_rel_fp_to_idx[id_or_name])
                else:
                    log_report(
                        "WARNING",
                        "Could not find depth map name "
                        + id_or_name
                        + ". "
                        + "Possible values are: "
                        + str(cam_rel_fp_to_idx.keys()),
                        op,
                    )

    # Adding cameras and image planes:
    for index, camera in enumerate(cameras):

        # camera_name = "Camera %d" % index     # original code
        # Replace the camera name so it matches the image name (without extension)
        blender_image_name_stem = _get_camera_obj_gui_str(camera)
        camera_name = blender_image_name_stem + "_cam"
        camera_object = add_camera_object(
            camera, camera_name, camera_collection
        )
        camera_object.scale *= camera_scale

        if not add_image_planes and not add_background_images:
            continue

        if camera.has_undistorted_absolute_fp():
            image_path = camera.get_undistorted_absolute_fp()
        else:
            image_path = camera.get_absolute_fp()

        if not os.path.isfile(image_path):
            log_report(
                "WARNING", "Could not find image at " + str(image_path), op
            )
            continue
        else:
            log_report("INFO", "Found image at " + str(image_path), op)

        blender_image = bpy.data.images.load(image_path)

        if add_background_images:
            camera_data = bpy.data.objects[camera_name].data
            camera_data.show_background_images = True
            background_image = camera_data.background_images.new()
            background_image.image = blender_image

        if add_image_planes and not camera.is_panoramic():
            # Group image plane and camera:
            camera_image_plane_pair_collection_current = add_collection(
                "Camera Image Plane Pair Collection %s"
                % blender_image_name_stem,
                camera_image_plane_pair_collection,
            )

            image_plane_name = blender_image_name_stem + "_image_plane"

            image_plane_obj = add_camera_image_plane(
                camera_object.matrix_world,
                blender_image,
                camera=camera,
                name=image_plane_name,
                transparency=image_plane_transparency,
                add_image_plane_emission=add_image_plane_emission,
                image_planes_collection=image_planes_collection,
                op=op,
            )

            camera_image_plane_pair_collection_current.objects.link(
                camera_object
            )
            camera_image_plane_pair_collection_current.objects.link(
                image_plane_obj
            )

        if not add_depth_maps_as_point_cloud:
            continue

        if camera.get_depth_map_fp() is None:
            continue

        if depth_map_indices is not None:
            if index not in depth_map_indices:
                continue

        # Group image plane and camera:
        camera_depth_map_pair_collection_current = add_collection(
            "Camera Depth Map Pair Collection %s"
            % os.path.basename(camera.get_depth_map_fp()),
            camera_depth_map_pair_collection,
        )

        depth_map_world_coords = camera.convert_depth_map_to_world_coords(
            depth_map_display_sparsity=depth_map_display_sparsity
        )
        depth_map_world_coords = depth_map_world_coords.tolist()

        if use_default_depth_map_color:
            color = depth_map_default_color
        else:
            color = _color_from_value(
                val=index, min_val=0, max_val=len(cameras)
            )

        depth_map_anchor_handle = draw_coords(
            depth_map_world_coords,
            color=color,
            point_size=depth_map_point_size,
            add_points_to_point_cloud_handle=True,
            reconstruction_collection=depth_map_collection,
            object_anchor_handle_name=_get_camera_obj_gui_str(camera)
            + "_depth_point_cloud",
            op=op,
        )

        camera_depth_map_pair_collection_current.objects.link(camera_object)
        camera_depth_map_pair_collection_current.objects.link(
            depth_map_anchor_handle
        )

    log_report("INFO", "Duration: " + str(stop_watch.get_elapsed_time()), op)
    log_report("INFO", "Adding Cameras: Done", op)


def add_camera_image_plane(
    matrix_world,
    blender_image,
    camera,
    name,
    transparency,
    add_image_plane_emission,
    image_planes_collection,
    op=None,
):
    """Add an image plane corresponding to a reconstructed camera."""
    # log_report('INFO', 'add_camera_image_plane: ...', op)
    # log_report('INFO', 'name: ' + str(name), op)

    width = camera.width
    height = camera.height
    focal_length = camera.get_focal_length()

    assert width is not None and height is not None

    bpy.context.scene.render.engine = "CYCLES"
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

    shift_x, shift_y = compute_principal_point_shift(
        camera, relativ_to_largest_extend=False
    )

    corners = ((-0.5, -0.5), (+0.5, -0.5), (+0.5, +0.5), (-0.5, +0.5))
    points = [
        (plane_center + (c[0] + shift_x) * right + (c[1] + shift_y) * up)[0:3]
        for c in corners
    ]
    mesh.from_pydata(points, [], [[0, 1, 2, 3]])
    mesh.uv_layers.new()

    # Add mesh to new image plane object:
    mesh_obj = add_obj(mesh, name, image_planes_collection)

    image_plane_material = bpy.data.materials.new(name="image_plane_material")
    # Adds "Principled BSDF" and a "Material Output" node
    image_plane_material.use_nodes = True

    nodes = image_plane_material.node_tree.nodes
    links = image_plane_material.node_tree.links

    shader_node_tex_image = nodes.new(type="ShaderNodeTexImage")
    shader_node_principled_bsdf = nodes.get("Principled BSDF")
    shader_node_principled_bsdf.inputs["Alpha"].default_value = transparency

    links.new(
        shader_node_tex_image.outputs["Color"],
        shader_node_principled_bsdf.inputs["Base Color"],
    )

    if add_image_plane_emission:
        links.new(
            shader_node_tex_image.outputs["Color"],
            shader_node_principled_bsdf.inputs["Emission"],
        )

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
    # log_report('INFO', 'add_camera_image_plane: Done', op)
    return mesh_obj
