import bpy
from mathutils import Quaternion
from mathutils import Matrix
from photogrammetry_importer.utility.blender_logging_utility import log_report


def remove_quaternion_discontinuities(target_obj):

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


def set_fcurve_interpolation(some_obj, interpolation_type="LINEAR"):

    # interpolation_string: ['CONSTANT', 'LINEAR', 'BEZIER', 'SINE',
    # 'QUAD', 'CUBIC', 'QUART', 'QUINT', 'EXPO', 'CIRC',
    # 'BACK', 'BOUNCE', 'ELASTIC']
    fcurves = some_obj.animation_data.action.fcurves
    for fcurve in fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = interpolation_type


def add_transformation_animation(
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
            remove_quaternion_discontinuities(animated_obj)

        if interpolation_type is not None:
            set_fcurve_interpolation(animated_obj, interpolation_type)

    log_report("INFO", "Adding transformation animation: Done", op)


def add_camera_intrinsics_animation(
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
