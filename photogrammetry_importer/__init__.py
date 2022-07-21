"""
A Blender addon to import different photogrammetry formats.

Subpackage Summary
------------------

ext
    External dependencies.
file_handlers
    Classes to read and write different file formats.
operators
    Operators to import and export different file formats into Blender.
panels
    GUI elements to adjust and leverage the imported objects.
preferences
    Persistent addon preferences.
properties
    Properties used by the import and export operators.
registration
    Registration of the import and export operators.
types
    Types used by different subpackages.
utility
    General and Blender-specific utility functions.

"""

bl_info = {
    "name": "Photogrammetry Import Export Addon",
    # Do not break this line, otherwise the addon can not be activated!
    "description": "Allows to import and export photogrammetry results (cameras, points and meshes).",
    "author": "Sebastian Bullinger",
    "version": (3, 2, 1),
    "blender": (3, 2, 1),
    "location": "File/Import and File/Export",
    "warning": "",
    "wiki_url": "https://blender-addon-photogrammetry-importer.readthedocs.io/en/latest/",
    "tracker_url": "https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer/issues",
    "category": "Import-Export",
}

import bpy

# load and reload submodules
############################

import importlib
from .utility import developer_utility

importlib.reload(developer_utility)
modules = developer_utility.setup_addon_modules(
    __path__, __name__, "bpy" in locals()
)

# The root dir is Blenders addon folder.
# Therefore, we need the "photogrammetry_importer" specifier for this addon
from photogrammetry_importer.blender_utility.logging_utility import log_report

from photogrammetry_importer.preferences.addon_preferences import (
    AddonPreferences,
)

from photogrammetry_importer.registration.registration import Registration

from photogrammetry_importer.panels.view_3d_panel import OpenGLPanel
from photogrammetry_importer.opengl.utility import redraw_points
from photogrammetry_importer.preferences.dependency import (
    add_command_line_sys_path_if_necessary,
)

if bpy.app.version < bl_info["blender"]:
    log_report(
        "WARNING",
        f"Detected Blender version {bpy.app.version} is older than required"
        f" the required Blender version {bl_info['blender']}. This might lead"
        " to potential bugs!",
    )

bpy.app.handlers.load_post.append(redraw_points)
bpy.app.handlers.load_post.append(add_command_line_sys_path_if_necessary)


def register():
    """Register importers, exporters and panels."""
    bpy.utils.register_class(AddonPreferences)

    import_export_prefs = bpy.context.preferences.addons[__name__].preferences
    Registration.register_importers(import_export_prefs)
    Registration.register_exporters(import_export_prefs)

    bpy.utils.register_class(OpenGLPanel)

    log_report(
        "INFO",
        "Registered {} with {} modules".format(bl_info["name"], len(modules)),
    )


def unregister():
    """Unregister importers, exporters and panels."""
    bpy.utils.unregister_class(AddonPreferences)

    Registration.unregister_importers()
    Registration.unregister_exporters()

    bpy.utils.unregister_class(OpenGLPanel)

    log_report("INFO", "Unregistered {}".format(bl_info["name"]))


if __name__ == "__main__":
    log_report("INFO", "main called")
