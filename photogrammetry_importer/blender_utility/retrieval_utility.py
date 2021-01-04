import bpy


def get_selected_camera():
    """Get the selected camera or return None."""
    selection_names = [obj.name for obj in bpy.context.selected_objects]
    if len(selection_names) == 0:
        return None
    selected_obj = bpy.data.objects[selection_names[0]]
    if selected_obj.type == "CAMERA":
        return selected_obj
    else:
        return None


def get_scene_animation_indices():
    """Get the animation indices of the scene."""
    scene = bpy.context.scene
    return range(scene.frame_start, scene.frame_end)


def get_object_animation_indices(obj):
    """Get the animation indices of the object."""
    animation_data = obj.animation_data
    fcurves = animation_data.action.fcurves
    fcu = fcurves[0]
    kp_indices = [int(kp.co[0]) for kp in fcu.keyframe_points]
    return kp_indices
