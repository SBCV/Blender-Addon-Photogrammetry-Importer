import os
import sys
import bpy
from bpy.props import BoolProperty

class GeneralImportProperties():
    """ This class encapsulates general Blender UI properties. """
    adjust_clipping_distance: BoolProperty(
        name="Adjust Clipping Distance",
        description =   "Adjust clipping distance of 3D view.",
        default=False)

    def draw_general_options(self, layout):
        mesh_box = layout.box()
        mesh_box.prop(self, "adjust_clipping_distance")
                    
    def apply_general_options(self):
        if self.adjust_clipping_distance:
            self.report({'INFO'}, 'Adjust clipping distance of 3D view: ...')
            active_space = None
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    active_space = area.spaces.active
                    break
            # Setting "active_space.clip_end" to values close to "sys.maxsize" 
            # causes strange graphical artifacts in the 3D view.
            if sys.maxsize == 2**63-1:
                # 2**(63-8) = 2**55 works without artifacts
                active_space.clip_end = 2**55-1
            else:
                active_space.clip_end = 2**23-1
            self.report({'INFO'}, 'Adjust clipping distance of 3D view: Done')
