"""
Collection of convenience functions to add and modify objects in Blender.
"""

import os
import math
import time
import bpy
from mathutils import Matrix
from mathutils import Vector
from photogrammetry_importer.utility.blender_logging_utility import log_report


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

    camera_center = -(
        camera_rotation @ t
    )  # Camera position in world coordinates
    camera_center[3] = 1.0

    camera_rotation = camera_rotation.copy()
    camera_rotation.col[
        3
    ] = camera_center  # Set translation to camera position
    return camera_rotation


def compute_camera_matrix_world(camera, convert_coordinate_system=True):
    translation_vec = camera.get_translation_vec()
    rotation_mat = camera.get_rotation_mat()
    if convert_coordinate_system:
        # Transform the camera coordinate system from computer vision camera coordinate frames
        # to the computer vision camera coordinate frames
        # That is, rotate the camera matrix around the x axis by 180 degrees,
        # i.e. invert the x and y axis
        rotation_mat = invert_y_and_z_axis(rotation_mat)
        translation_vec = invert_y_and_z_axis(translation_vec)
    return get_world_matrix_from_translation_vec(translation_vec, rotation_mat)


def add_empty(empty_name, collection=None):
    if collection is None:
        collection = bpy.context.collection
    empty_obj = bpy.data.objects.new(empty_name, None)
    collection.objects.link(empty_obj)
    return empty_obj


def add_obj(data, obj_name, collection=None):

    if collection is None:
        collection = bpy.context.collection

    new_obj = bpy.data.objects.new(obj_name, data)
    collection.objects.link(new_obj)
    new_obj.select_set(state=True)

    if (
        bpy.context.view_layer.objects.active is None
        or bpy.context.view_layer.objects.active.mode == "OBJECT"
    ):
        bpy.context.view_layer.objects.active = new_obj
    return new_obj


def add_collection(collection_name, parent_collection=None):

    if parent_collection is None:
        parent_collection = bpy.context.collection

    new_collection = bpy.data.collections.new(collection_name)
    parent_collection.children.link(new_collection)

    return new_collection


def adjust_render_settings_if_possible(cameras, op):

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
