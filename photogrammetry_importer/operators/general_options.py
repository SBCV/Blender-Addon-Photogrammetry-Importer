import os
import sys
import bpy
from bpy.props import BoolProperty
from photogrammetry_importer.blender_utility.logging_utility import log_report


class GeneralOptions:
    """Class to define and apply general options."""

    adjust_clipping_distance: BoolProperty(
        name="Adjust Clipping Distance",
        description="Adjust clipping distance of 3D view.",
        default=False,
    )

    def draw_general_options(self, layout):
        """Draw general options."""
        mesh_box = layout.box()
        mesh_box.prop(self, "adjust_clipping_distance")

    def apply_general_options(self):
        """Apply the options defined by this class."""
        if self.adjust_clipping_distance:
            log_report(
                "INFO", "Adjust clipping distance of 3D view: ...", self
            )
            active_space = None
            for area in bpy.context.screen.areas:
                if area.type == "VIEW_3D":
                    active_space = area.spaces.active
                    break
            # Setting "active_space.clip_end" to values close to "sys.maxsize"
            # causes strange graphical artifacts in the 3D view.
            if sys.maxsize == 2 ** 63 - 1:
                # 2**(63-8) = 2**55 works without artifacts
                active_space.clip_end = 2 ** 55 - 1
            else:
                active_space.clip_end = 2 ** 23 - 1
            log_report(
                "INFO", "Adjust clipping distance of 3D view: Done", self
            )
