import bpy
import numpy as np
from bpy.props import StringProperty


class TransformationImportProperties:
    """ This class encapsulates Blender UI properties that allow to import transformations into Blender. """

    path_to_transformations: StringProperty(
        name="Transformation Directory",
        description="Path to transformations stored in .txt files",
        default="",
    )

    def draw_transformation_options(self, layout):
        transformation_box = layout.box()
        transformation_box.prop(self, "path_to_transformations")
