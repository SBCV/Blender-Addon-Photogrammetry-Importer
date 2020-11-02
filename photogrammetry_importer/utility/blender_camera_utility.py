import os
import math
import bpy
import colorsys
import numpy as np
from mathutils import Vector
from collections import namedtuple

from photogrammetry_importer.types.camera import Camera

from photogrammetry_importer.utility.os_utility import (
    get_image_file_paths_in_dir,
)
from photogrammetry_importer.utility.blender_utility import (
    compute_camera_matrix_world,
    add_collection,
    add_obj,
)
from photogrammetry_importer.utility.blender_animation_utility import (
    add_transformation_animation,
    add_camera_intrinsics_animation,
)
from photogrammetry_importer.utility.blender_opengl_utility import draw_coords
from photogrammetry_importer.utility.stop_watch import StopWatch
from photogrammetry_importer.utility.type_utility import is_int
from photogrammetry_importer.utility.blender_logging_utility import log_report


class DummyCamera(object):
    def __init__(self):
        self._relative_fp = None
        self._absolute_fp = None
        self.image_fp_type = None
        self.image_dp = None

    def get_file_name(self):
        return os.path.basename(self.get_relative_fp())

    def get_relative_fp(self):
        return self._relative_fp

    def get_absolute_fp(self):
        return self._get_absolute_fp(self._relative_fp, self._absolute_fp)

    def _get_absolute_fp(self, relative_fp, absolute_fp):
        if self.image_fp_type == Camera.IMAGE_FP_TYPE_NAME:
            assert self.image_dp is not None
            assert relative_fp is not None
            return os.path.join(self.image_dp, os.path.basename(relative_fp))
        elif self.image_fp_type == Camera.IMAGE_FP_TYPE_RELATIVE:
            assert self.image_dp is not None
            assert relative_fp is not None
            return os.path.join(self.image_dp, relative_fp)
        elif self.image_fp_type == Camera.IMAGE_FP_TYPE_ABSOLUTE:
            assert absolute_fp is not None
            return absolute_fp
        else:
            assert False


CameraIntrinsics = namedtuple(
    "CameraIntrinsics", "field_of_view shift_x shift_y"
)


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

    # log_report('INFO', 'shift_x: ' + str(shift_x))
    # log_report('INFO', 'shift_y: ' + str(shift_y))

    return shift_x, shift_y


def add_single_camera(op, camera_name, camera):
    # Add camera:
    bcamera = bpy.data.cameras.new(camera_name)

    if camera.is_panoramic():
        focal_length = 0.001  # minimal focal length
        bcamera.type = "PANO"
        bcamera.cycles.panorama_type = camera.get_panoramic_type()
    else:
        focal_length = camera.get_focal_length()

    #  Adjust field of view
    bcamera.angle = camera.get_field_of_view()

    bcamera.shift_x, bcamera.shift_y = compute_shift(
        camera, relativ_to_largest_extend=True
    )

    # log_report('INFO', 'focal_length: ' + str(focal_length))
    # log_report('INFO', 'camera.get_calibration_mat(): ' + str(camera.get_calibration_mat()))
    # log_report('INFO', 'width: ' + str(camera.width))
    # log_report('INFO', 'height: ' + str(camera.height))
    # log_report('INFO', 'p_x: ' + str(p_x))
    # log_report('INFO', 'p_y: ' + str(p_y))

    return bcamera


def enhance_cameras_with_dummy_cameras(op, cameras, image_dp, image_fp_type):

    rec_image_relative_fp = [camera.get_relative_fp() for camera in cameras]

    all_image_relative_paths = get_image_file_paths_in_dir(
        image_dp,
        base_name_only=image_fp_type == Camera.IMAGE_FP_TYPE_NAME,
        relative_path_only=image_fp_type == Camera.IMAGE_FP_TYPE_RELATIVE,
        sort_result=True,
        recursive=True,
    )

    non_rec_image_relative_paths = [
        image_path
        for image_path in all_image_relative_paths
        if os.path.basename(image_path) not in rec_image_relative_fp
    ]

    for non_rec_image_path in non_rec_image_relative_paths:
        cam = DummyCamera()
        cam._relative_fp = non_rec_image_path
        cam._absolute_fp = os.path.join(image_dp, cam._relative_fp)
        cam.image_fp_type = image_fp_type
        cam.image_dp = image_dp

        cameras.append(cam)

    return cameras


def add_camera_animation(
    op,
    cameras,
    parent_collection,
    animation_frame_source,
    add_background_images,
    number_interpolation_frames,
    interpolation_type,
    consider_missing_cameras_during_animation,
    remove_rotation_discontinuities,
    image_dp,
    image_fp_type,
):
    log_report("INFO", "Adding Camera Animation: ...")

    if len(cameras) == 0:
        return

    if animation_frame_source == "ORIGINAL":
        number_interpolation_frames = 0
    elif animation_frame_source == "ADJUSTED":
        add_background_images = False
    else:
        assert False

    if consider_missing_cameras_during_animation:
        cameras = enhance_cameras_with_dummy_cameras(
            op, cameras, image_dp, image_fp_type
        )

    # Using the first reconstructed camera as template for the animated camera.
    # The values are adjusted with add_transformation_animation() and
    # add_camera_intrinsics_animation().
    some_cam = cameras[0]
    bcamera = add_single_camera(op, "Animated Camera", some_cam)
    cam_obj = add_obj(bcamera, "Animated Camera", parent_collection)
    cameras_sorted = sorted(
        cameras, key=lambda camera: camera.get_relative_fp()
    )

    transformations_sorted = []
    camera_intrinsics_sorted = []
    for camera in cameras_sorted:
        if isinstance(camera, DummyCamera):
            matrix_world = None
            camera_intrinsics = None
        else:
            matrix_world = compute_camera_matrix_world(camera)
            shift_x, shift_y = compute_shift(
                camera, relativ_to_largest_extend=True
            )
            camera_intrinsics = CameraIntrinsics(
                camera.get_field_of_view(), shift_x, shift_y
            )

        transformations_sorted.append(matrix_world)
        camera_intrinsics_sorted.append(camera_intrinsics)

    add_transformation_animation(
        op=op,
        animated_obj_name=cam_obj.name,
        transformations_sorted=transformations_sorted,
        number_interpolation_frames=number_interpolation_frames,
        interpolation_type=interpolation_type,
        remove_rotation_discontinuities=remove_rotation_discontinuities,
    )

    add_camera_intrinsics_animation(
        op=op,
        animated_obj_name=cam_obj.name,
        intrinsics_sorted=camera_intrinsics_sorted,
        number_interpolation_frames=number_interpolation_frames,
    )

    if add_background_images:
        # https://docs.blender.org/api/current/bpy.types.CameraBackgroundImage.html
        camera_data = bpy.data.objects[cam_obj.name].data
        camera_data.show_background_images = True
        bg_img = camera_data.background_images.new()
        dp = os.path.dirname(cameras_sorted[0].get_absolute_fp())
        # The first entry (ALL OTHERS ARE IGNORED) in the "files" parameter
        # in bpy.ops.clip.open() is used to determine the image in the image
        # sequence. All images with higher sequence numbers are added to the
        # movie clip.
        first_sequence_fn = [{"name": cameras_sorted[0].get_file_name()}]

        # Remove previously created movie clips
        movie_clip_name = os.path.basename(first_sequence_fn[0]["name"])
        if movie_clip_name in bpy.data.movieclips:
            bpy.data.movieclips.remove(bpy.data.movieclips[movie_clip_name])

        # https://docs.blender.org/api/current/bpy.types.MovieClip.html
        # https://docs.blender.org/api/current/bpy.types.Sequences.html
        # Using a video clip instead of an image sequence has the advantage that
        # Blender automatically adjusts the start offset of the image sequence.
        # (e.g. if the first image of the sequence is 100_7110.JPG, then one
        # would have to set the offset to 7109)
        bpy.ops.clip.open(directory=dp, files=first_sequence_fn)
        bg_img.source = "MOVIE_CLIP"

        # The clip created with bpy.ops.clip.open() has the same name than the
        # first image name of the image sequence.
        bg_img.clip = bpy.data.movieclips[movie_clip_name]


def color_from_value(val, min_val, max_val):
    # source: http://stackoverflow.com/questions/10901085/range-values-to-pseudocolor

    # convert val in range minval..maxval to the range 0..120 degrees which
    # correspond to the colors red..green in the HSV colorspace

    h = (float(val - min_val) / (max_val - min_val)) * 120
    # convert hsv color (h, 1, 1) to its rgb equivalent
    # note: the hsv_to_rgb() function expects h to be in the range 0..1 and not
    # in 0..360
    r, g, b = colorsys.hsv_to_rgb(h / 360, 1.0, 1.0)
    return r, g, b, 1


def add_cameras(
    op,
    cameras,
    parent_collection,
    image_dp=None,
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
    use_default_depth_map_color=False,
    depth_map_default_color=(1.0, 0.0, 0.0),
    depth_map_display_sparsity=10,
    depth_map_id_or_name_str="",
):

    """
    ======== The images are currently only shown in BLENDER RENDER ========
    ======== Make sure to enable TEXTURE SHADING in the 3D view to make the images visible ========

    :param cameras:
    :param image_dp:
    :param add_image_planes:
    :param convert_camera_coordinate_system:
    :param camera_collection_name:
    :param image_plane_collection_name:
    :return:
    """
    log_report("INFO", "Adding Cameras: ...")
    stop_watch = StopWatch()
    camera_collection = add_collection(
        camera_collection_name, parent_collection
    )

    if add_image_planes:
        log_report("INFO", "Adding image planes: True")
        image_planes_collection = add_collection(
            image_plane_collection_name, parent_collection
        )
        camera_image_plane_pair_collection = add_collection(
            "Camera Image Plane Pair Collection", parent_collection
        )
    else:
        log_report("INFO", "Adding image planes: False")

    if add_depth_maps_as_point_cloud:
        log_report("INFO", "Adding depth maps as point cloud: True")
        depth_map_collection = add_collection(
            depth_map_collection_name, parent_collection
        )
        camera_depth_map_pair_collection = add_collection(
            "Camera Depth Map Pair Collection", parent_collection
        )
    else:
        log_report("INFO", "Adding depth maps as point cloud: False")

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
                    )

    # Adding cameras and image planes:
    for index, camera in enumerate(cameras):

        # camera_name = "Camera %d" % index     # original code
        # Replace the camera name so it matches the image name (without extension)
        blender_image_name_stem = camera.get_blender_obj_gui_str()
        camera_name = blender_image_name_stem + "_cam"
        bcamera = add_single_camera(op, camera_name, camera)
        camera_object = add_obj(bcamera, camera_name, camera_collection)
        matrix_world = compute_camera_matrix_world(camera)
        camera_object.matrix_world = matrix_world
        camera_object.scale *= camera_scale

        if not add_image_planes and not add_background_images:
            continue

        if camera.has_undistorted_absolute_fp():
            image_path = camera.get_undistored_absolute_fp()
        else:
            image_path = camera.get_absolute_fp()

        if not os.path.isfile(image_path):
            log_report("WARNING", "Could not find image at " + str(image_path))
            continue

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
                matrix_world,
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

        if camera.depth_map_fp is None:
            continue

        if depth_map_indices is not None:
            if index not in depth_map_indices:
                continue

        depth_map_fp = camera.depth_map_fp

        # Group image plane and camera:
        camera_depth_map_pair_collection_current = add_collection(
            "Camera Depth Map Pair Collection %s"
            % os.path.basename(depth_map_fp),
            camera_depth_map_pair_collection,
        )

        depth_map_world_coords = camera.convert_depth_map_to_world_coords(
            depth_map_display_sparsity=depth_map_display_sparsity
        )

        if use_default_depth_map_color:
            color = depth_map_default_color
        else:
            color = color_from_value(
                val=index, min_val=0, max_val=len(cameras)
            )

        depth_map_anchor_handle = draw_coords(
            op,
            depth_map_world_coords,
            # TODO Setting this to true causes an error message
            add_points_to_point_cloud_handle=False,
            reconstruction_collection=depth_map_collection,
            object_anchor_handle_name=camera.get_blender_obj_gui_str()
            + "_depth_point_cloud",
            color=color,
        )

        camera_depth_map_pair_collection_current.objects.link(camera_object)
        camera_depth_map_pair_collection_current.objects.link(
            depth_map_anchor_handle
        )

    log_report("INFO", "Duration: " + str(stop_watch.get_elapsed_time()))
    log_report("INFO", "Adding Cameras: Done")


def add_camera_image_plane(
    matrix_world,
    blender_image,
    camera,
    name,
    transparency,
    add_image_plane_emission,
    image_planes_collection,
    op,
):
    """
    Create mesh for image plane
    """
    # log_report('INFO', 'add_camera_image_plane: ...')
    # log_report('INFO', 'name: ' + str(name))

    width = camera.width
    height = camera.height
    focal_length = camera.get_focal_length()
    p_x, p_y = camera.get_principal_point()

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

    shift_x, shift_y = compute_shift(camera, relativ_to_largest_extend=False)

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
    # log_report('INFO', 'add_camera_image_plane: Done')
    return mesh_obj


def set_principal_point_for_cameras(cameras, default_pp_x, default_pp_y, op):

    if not math.isnan(default_pp_x) and not math.isnan(default_pp_y):
        log_report("WARNING", "Setting principal points to default values!")
    else:
        log_report("WARNING", "Setting principal points to image centers!")
        assert cameras[0].width is not None and cameras[0].height is not None
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


def get_selected_camera():
    selection_names = [obj.name for obj in bpy.context.selected_objects]
    if len(selection_names) == 0:
        return None
    selected_obj = bpy.data.objects[selection_names[0]]
    if selected_obj.type == "CAMERA":
        return selected_obj
    else:
        return None


def check_radial_distortion(radial_distortion, camera_name, op):
    # TODO
    # Integrate lens distortion nodes
    # https://docs.blender.org/manual/en/latest/compositing/types/distort/lens_distortion.html
    # to properly support radial distortion consisting of a single parameter

    if radial_distortion is None:
        return
    if np.array_equal(
        np.asarray(radial_distortion), np.zeros_like(radial_distortion)
    ):
        return

    output = (
        "Blender does not support radial distortion of cameras in the 3D View."
    )
    output += (
        " Distortion of camera "
        + camera_name
        + ": "
        + str(radial_distortion)
        + "."
    )
    output += " If possible, re-compute the reconstruction using a camera model without radial distortion parameters."
    output += ' Use "Suppress Distortion Warnings" in the import settings to suppress this message.'
    log_report("WARNING", output, op)
