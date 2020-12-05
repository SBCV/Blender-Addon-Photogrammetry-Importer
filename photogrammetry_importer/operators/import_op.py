import os
import numpy as np
import bpy
import math

from bpy.props import (
    CollectionProperty,
    StringProperty,
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
)

from bpy_extras.io_utils import ImportHelper, axis_conversion


class ImportOperator(bpy.types.Operator):
    """Abstract basic import operator."""

    @staticmethod
    def _is_custom_property(prop):
        custom_property_types = [
            bpy.types.BoolProperty,
            bpy.types.IntProperty,
            bpy.types.FloatProperty,
            bpy.types.StringProperty,
            bpy.types.EnumProperty,
        ]
        return type(prop) in custom_property_types

    def _get_addon_name(self):
        return __name__.split(".")[0]

    def _initialize_options(self, source):
        # Side note:
        #   "vars(my_obj)" does not work in Blender
        #   "dir(my_obj)" shows the attributes, but not the corresponding type
        #   "my_obj.rna_type.properties.items()" lists attribute names with
        #   corresponding types
        for name, prop in source.rna_type.properties.items():
            if name == "bl_idname":
                continue
            if not ImportOperator._is_custom_property(prop):
                continue
            if not hasattr(self, name):
                continue
            setattr(self, name, getattr(source, name))

    def initialize_options_from_addon_preferences(self):
        """Initialize the import options from the current addon preferences."""
        addon_name = self._get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[
            addon_name
        ].preferences
        self._initialize_options(import_export_prefs)

    def get_default_image_path(self, reconstruction_fp, image_dp):
        """Get the (default) path that defines where to look for images."""
        if image_dp is None:
            return None
        elif image_dp == "":
            image_default_same_dp = os.path.dirname(reconstruction_fp)
            image_default_sub_dp = os.path.join(
                image_default_same_dp, "images"
            )
            if os.path.isdir(image_default_sub_dp):
                image_dp = image_default_sub_dp
            else:
                image_dp = image_default_same_dp
        return image_dp

    def execute(self, context):
        """Abstract method that must be overriden by a subclass."""
        # Pythons ABC class and Blender's operators do not work well
        # together in the context of multiple inheritance.
        raise NotImplementedError("Subclasses must override this function!")
