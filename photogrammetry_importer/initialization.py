import bpy
from photogrammetry_importer.blender_logging import log_report

class Initializer(object):

    custom_property_types = [
        bpy.types.BoolProperty,
        bpy.types.IntProperty,
        bpy.types.FloatProperty,
        bpy.types.StringProperty,
        bpy.types.EnumProperty]

    def is_custom_property(prop):
        return type(prop) in Initializer.custom_property_types

    def initialize_options(source, target):

        # Side note:
        #   "vars(my_obj)" does not work in Blender
        #   "dir(my_obj)" shows the attributesm, but not the corresponding type
        #   "my_obj.rna_type.properties.items()" lists attribute names with corresponding types

        for name, prop in source.rna_type.properties.items():

            if name == 'bl_idname':
                continue

            if not Initializer.is_custom_property(prop):
                continue

            if not hasattr(target, name):
                continue

            setattr(target, name, getattr(source, name))
