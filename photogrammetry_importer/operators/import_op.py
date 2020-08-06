import os
import numpy as np
import bpy
import math

# Notes:
#   http://sinestesia.co/blog/tutorials/using-blenders-filebrowser-with-python/
#       Nice blender tutorial
#   https://blog.michelanders.nl/2014/07/inheritance-and-mixin-classes-vs_13.html
#       - The class that is actually used as operator must inherit from bpy.types.Operator and ImportHelper
#       - Properties defined in the parent class, which inherits from bpy.types.Operator and ImportHelper
#         are not considered

from bpy.props import (CollectionProperty,
                       StringProperty,
                       BoolProperty,
                       EnumProperty,
                       FloatProperty,
                       IntProperty)

from bpy_extras.io_utils import ImportHelper
from bpy_extras.io_utils import axis_conversion

custom_property_types = [
    bpy.types.BoolProperty,
    bpy.types.IntProperty,
    bpy.types.FloatProperty,
    bpy.types.StringProperty,
    bpy.types.EnumProperty]

def is_custom_property(prop):
    return type(prop) in custom_property_types

class ImportOperator(bpy.types.Operator):

    def initialize_options(self, source):
        # Side note:
        #   "vars(my_obj)" does not work in Blender
        #   "dir(my_obj)" shows the attributes, but not the corresponding type
        #   "my_obj.rna_type.properties.items()" lists attribute names with corresponding types
        for name, prop in source.rna_type.properties.items():
            if name == 'bl_idname':
                continue
            if not is_custom_property(prop):
                continue
            if not hasattr(self, name):
                continue
            setattr(self, name, getattr(source, name))

    def get_addon_name(self):
        return __name__.split('.')[0]

    def get_default_image_path(self, reconstruction_fp, image_dp):
        if image_dp is None:
            return None
        elif image_dp == '':
            image_default_same_dp = os.path.dirname(reconstruction_fp)
            image_default_sub_dp = os.path.join(image_default_same_dp, 'images')
            if os.path.isdir(image_default_sub_dp):
                image_dp = image_default_sub_dp
            else:
                image_dp = image_default_same_dp
        return image_dp
