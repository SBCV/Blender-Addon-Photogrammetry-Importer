import os
import shutil
from collections import namedtuple
import bpy
from mathutils import Quaternion
from mathutils import Matrix
from photogrammetry_importer.blender_utility.logging_utility import log_report

from photogrammetry_importer.importers.camera_utility import (
    add_camera_object,
    compute_principal_point_shift,
    compute_camera_matrix_world,
)

from photogrammetry_importer.blender_utility.object_utility import add_obj

from photogrammetry_importer.utility.os_utility import (
    get_image_file_paths_in_dir,
)

from photogrammetry_importer.types.camera import Camera


_CameraIntrinsics = namedtuple(
    "CameraIntrinsics", "field_of_view shift_x shift_y"
)


class _NonReconstructedCamera(Camera):
    """Class to distuingish reconstructed and non-reconstructed cameras."""

    pass


def _enhance_cameras_with_non_reconstructed_cameras(
    cameras, image_dp, image_fp_type, op=None
):
    rec_image_relative_fp = []
    for camera in cameras:
        if camera.has_undistorted_absolute_fp():
            rec_image_relative_fp.append(camera.get_undistorted_relative_fp())
        else:
            rec_image_relative_fp.append(camera.get_relative_fp())

    # rec_image_relative_fp = [camera.get_relative_fp() for camera in cameras]

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

    add_undistorted_paths = all(
        camera.has_undistorted_absolute_fp() for camera in cameras
    )

    for non_rec_image_path in non_rec_image_relative_paths:
        cam = _NonReconstructedCamera()
        cam._relative_fp = non_rec_image_path
        cam._absolute_fp = os.path.join(image_dp, cam._relative_fp)
        cam.image_fp_type = image_fp_type
        cam.image_dp = image_dp

        if add_undistorted_paths:
            cam._undistorted_relative_fp = non_rec_image_path
            cam._undistorted_absolute_fp = os.path.join(
                image_dp, cam._undistorted_relative_fp
            )

        cameras.append(cam)

    return cameras


def _remove_quaternion_discontinuities(target_obj):

    # the interpolation of quaternions may lead to discontinuities
    # if the quaternions show different signs

    # https://blender.stackexchange.com/questions/58866/keyframe-interpolation-instability
    action = target_obj.animation_data.action

    # quaternion curves
    fqw = action.fcurves.find("rotation_quaternion", index=0)
    fqx = action.fcurves.find("rotation_quaternion", index=1)
    fqy = action.fcurves.find("rotation_quaternion", index=2)
    fqz = action.fcurves.find("rotation_quaternion", index=3)

    # invert quaternion so that interpolation takes the shortest path
    if len(fqw.keyframe_points) > 0:
        current_quat = Quaternion(
            (
                fqw.keyframe_points[0].co[1],
                fqx.keyframe_points[0].co[1],
                fqy.keyframe_points[0].co[1],
                fqz.keyframe_points[0].co[1],
            )
        )

        for i in range(len(fqw.keyframe_points) - 1):
            last_quat = current_quat
            current_quat = Quaternion(
                (
                    fqw.keyframe_points[i + 1].co[1],
                    fqx.keyframe_points[i + 1].co[1],
                    fqy.keyframe_points[i + 1].co[1],
                    fqz.keyframe_points[i + 1].co[1],
                )
            )

            if last_quat.dot(current_quat) < 0:
                current_quat.negate()
                fqw.keyframe_points[i + 1].co[1] = -fqw.keyframe_points[
                    i + 1
                ].co[1]
                fqx.keyframe_points[i + 1].co[1] = -fqx.keyframe_points[
                    i + 1
                ].co[1]
                fqy.keyframe_points[i + 1].co[1] = -fqy.keyframe_points[
                    i + 1
                ].co[1]
                fqz.keyframe_points[i + 1].co[1] = -fqz.keyframe_points[
                    i + 1
                ].co[1]


def _set_fcurve_interpolation(some_obj, interpolation_type="LINEAR"):

    # interpolation_string: ['CONSTANT', 'LINEAR', 'BEZIER', 'SINE',
    # 'QUAD', 'CUBIC', 'QUART', 'QUINT', 'EXPO', 'CIRC',
    # 'BACK', 'BOUNCE', 'ELASTIC']
    fcurves = some_obj.animation_data.action.fcurves
    for fcurve in fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = interpolation_type


def _add_transformation_animation(
    animated_obj_name,
    transformations_sorted,
    number_interpolation_frames,
    interpolation_type=None,
    remove_rotation_discontinuities=True,
    op=None,
):
    log_report("INFO", "Adding transformation animation: ...", op)

    scene = bpy.context.scene
    scene.frame_start = 0
    step_size = number_interpolation_frames + 1
    scene.frame_end = step_size * len(transformations_sorted)
    animated_obj = bpy.data.objects[animated_obj_name]

    for index, transformation in enumerate(transformations_sorted):
        # log_report('INFO', 'index: ' + str(index), op)
        # log_report('INFO', 'transformation: ' + str(transformation), op)

        current_keyframe_index = (index + 1) * step_size

        if transformation is None:
            continue

        animated_obj.matrix_world = Matrix(transformation)

        animated_obj.keyframe_insert(
            data_path="location", index=-1, frame=current_keyframe_index
        )

        # Don't use euler rotations, they show too many discontinuties
        # animated_obj.keyframe_insert(
        #   data_path="rotation_euler",
        #   index=-1,
        #   frame=current_keyframe_index)

        animated_obj.rotation_mode = "QUATERNION"
        animated_obj.keyframe_insert(
            data_path="rotation_quaternion",
            index=-1,
            frame=current_keyframe_index,
        )

        if remove_rotation_discontinuities:
            # q and -q represent the same rotation
            _remove_quaternion_discontinuities(animated_obj)

        if interpolation_type is not None:
            _set_fcurve_interpolation(animated_obj, interpolation_type)

    log_report("INFO", "Adding transformation animation: Done", op)


def _add_camera_intrinsics_animation(
    animated_obj_name, intrinsics_sorted, number_interpolation_frames, op=None
):

    log_report("INFO", "Adding camera intrinsic parameter animation: ...", op)

    step_size = number_interpolation_frames + 1
    animated_obj = bpy.data.objects[animated_obj_name]

    for index, intrinsics in enumerate(intrinsics_sorted):
        current_keyframe_index = (index + 1) * step_size

        if intrinsics is None:
            continue

        animated_obj.data.angle = intrinsics.field_of_view
        animated_obj.data.shift_x = intrinsics.shift_x
        animated_obj.data.shift_y = intrinsics.shift_y

        animated_obj.data.keyframe_insert(
            data_path="lens", index=-1, frame=current_keyframe_index
        )
        animated_obj.data.keyframe_insert(
            data_path="shift_x", index=-1, frame=current_keyframe_index
        )
        animated_obj.data.keyframe_insert(
            data_path="shift_y", index=-1, frame=current_keyframe_index
        )

    log_report("INFO", "Adding camera intrinsic parameter animation: Done", op)


def _get_reorganized_file_name(cam, common_prefix, op=None):
    full_original_stem, _ = os.path.splitext(cam.get_absolute_fp())
    full_original_stem.startswith(full_original_stem)
    unique_original_stem = full_original_stem.split(common_prefix, 1)[1]
    unique_original_fn = unique_original_stem.replace(os.path.sep, "_")

    _, undistorted_ext = os.path.splitext(cam.get_undistorted_file_name())
    reorganized_fn = unique_original_fn + undistorted_ext
    return reorganized_fn


def _reorganize_undistorted_images(cameras_sorted, op):
    """Reorganize the undistorted images in the workspace."""

    log_report(
        "WARNING",
        "Writing (renamed) undistorted images to a single folder in the"
        " workspace!",
        op,
    )

    common_prefix = os.path.commonprefix(
        [
            cam.get_undistorted_absolute_fp()
            for cam in cameras_sorted
            if cam.has_undistorted_absolute_fp
        ]
    )
    # Remove trailing slash
    reorganized_dp = os.path.dirname(common_prefix)
    reorganized_undistorted_dp = reorganized_dp + "_restructured"

    log_report(
        "WARNING", f"Reorganized directory: {reorganized_undistorted_dp}", op
    )

    if not os.path.isdir(reorganized_undistorted_dp):
        os.mkdir(reorganized_undistorted_dp)

    for cam in cameras_sorted:
        reorganized_fn = _get_reorganized_file_name(cam, common_prefix)
        reorganized_fp = os.path.join(
            reorganized_undistorted_dp, reorganized_fn
        )
        shutil.copyfile(cam.get_undistorted_absolute_fp(), reorganized_fp)

    first_cam = cameras_sorted[0]
    first_fn = _get_reorganized_file_name(first_cam, common_prefix)
    log_report("WARNING", f"First file name: {first_fn}", op)

    return reorganized_undistorted_dp, first_fn


def _add_background_image_sequence(
    cam_obj, cameras_sorted, reorganize_undistorted_images, op=None
):
    # https://docs.blender.org/api/current/bpy.types.CameraBackgroundImage.html
    camera_data = bpy.data.objects[cam_obj.name].data
    camera_data.show_background_images = True
    bg_img = camera_data.background_images.new()

    first_cam = cameras_sorted[0]
    if (
        reorganize_undistorted_images
        and first_cam.has_undistorted_absolute_fp()
    ):
        dp, first_fn = _reorganize_undistorted_images(cameras_sorted, op)
    else:
        first_cam = cameras_sorted[0]
        dp = os.path.dirname(first_cam.get_absolute_fp())
        first_fn = first_cam.get_file_name()

    # Remove previously created movie clips
    movie_clip_name = os.path.basename(first_fn)
    if movie_clip_name in bpy.data.movieclips:
        bpy.data.movieclips.remove(bpy.data.movieclips[movie_clip_name])

    if os.path.isfile(os.path.join(dp, first_fn)):

        # in bpy.ops.clip.open() is used to determine the image in the
        # image sequence. All images with higher sequence numbers are added
        # to the movie clip.
        first_sequence_fn = [{"name": first_fn}]

        # https://docs.blender.org/api/current/bpy.types.MovieClip.html
        # https://docs.blender.org/api/current/bpy.types.Sequences.html
        # Using a video clip instead of an image sequence has the advantage
        # that Blender automatically adjusts the start offset of the image
        # sequence (e.g. if the first image of the sequence is
        #  100_7110.JPG, then one would have to set the offset to manually
        # to 7109)
        bpy.ops.clip.open(directory=dp, files=first_sequence_fn)
        bg_img.source = "MOVIE_CLIP"

        # The clip created with bpy.ops.clip.open() has the same name than
        # the first image name of the image sequence.
        bg_img.clip = bpy.data.movieclips[movie_clip_name]


def add_camera_animation(
    cameras,
    parent_collection,
    animation_frame_source="ORIGINAL",
    add_background_images=False,
    reorganize_undistorted_images=False,
    number_interpolation_frames=0,
    interpolation_type="LINEAR",
    remove_rotation_discontinuities=True,
    consider_missing_cameras_during_animation=False,
    image_dp=None,
    image_fp_type=None,
    op=None,
):
    """Add an animated camera from a set of reconstructed cameras."""
    log_report("INFO", "Adding Camera Animation: ...", op)

    if len(cameras) == 0:
        return

    if animation_frame_source == "ORIGINAL":
        number_interpolation_frames = 0
    elif animation_frame_source == "ADJUSTED":
        add_background_images = False
    else:
        assert False

    if consider_missing_cameras_during_animation:
        assert image_dp is not None and image_fp_type is not None
        cameras = _enhance_cameras_with_non_reconstructed_cameras(
            cameras, image_dp, image_fp_type, op
        )

    # Using the first reconstructed camera as template for the animated camera.
    # The values are adjusted with _add_transformation_animation() and
    # add_camera_intrinsics_animation().
    some_cam = cameras[0]
    cam_obj = add_camera_object(
        some_cam, "Animated Camera", parent_collection, copy_matrix_world=False
    )

    cameras_sorted = sorted(
        cameras, key=lambda camera: camera.get_relative_fp()
    )

    transformations_sorted = []
    camera_intrinsics_sorted = []
    for camera in cameras_sorted:
        if isinstance(camera, _NonReconstructedCamera):
            matrix_world = None
            camera_intrinsics = None
        else:
            matrix_world = compute_camera_matrix_world(camera)
            shift_x, shift_y = compute_principal_point_shift(
                camera, relativ_to_largest_extend=True
            )
            camera_intrinsics = _CameraIntrinsics(
                camera.get_field_of_view(), shift_x, shift_y
            )

        transformations_sorted.append(matrix_world)
        camera_intrinsics_sorted.append(camera_intrinsics)

    _add_transformation_animation(
        animated_obj_name=cam_obj.name,
        transformations_sorted=transformations_sorted,
        number_interpolation_frames=number_interpolation_frames,
        interpolation_type=interpolation_type,
        remove_rotation_discontinuities=remove_rotation_discontinuities,
        op=op,
    )

    _add_camera_intrinsics_animation(
        animated_obj_name=cam_obj.name,
        intrinsics_sorted=camera_intrinsics_sorted,
        number_interpolation_frames=number_interpolation_frames,
        op=op,
    )

    if add_background_images:
        _add_background_image_sequence(
            cam_obj, cameras_sorted, reorganize_undistorted_images, op
        )

    log_report("INFO", "Adding Camera Animation: Done", op)
    return cam_obj
