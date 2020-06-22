'''
Copyright (C) 2018 Sebastian Bullinger


Created by Sebastian Bullinger

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
    "name": "Photogrammetry Import Export Addon",
    "description": "Allows to import and export photogrammetry results (cameras, points and meshes).",
    "author": "Sebastian Bullinger",
    "version": (2, 0, 0),
    "blender": (2, 80, 0),
    "location": "File / Import and File/Export",
    "warning": "",
    "wiki_url": "https://blender-addon-photogrammetry-importer.readthedocs.io/en/latest/installation.html",
    "tracker_url": "https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer/issues",
    "category": "Import-Export" }

import bpy

# load and reload submodules
##################################

import importlib
from .utils import developer_utils
importlib.reload(developer_utils)
modules = developer_utils.setup_addon_modules(__path__, __name__, "bpy" in locals())

# The root dir is blenders addon folder, 
# therefore we need the "photogrammetry_importer" specifier for this addon
from photogrammetry_importer.blender_logging import log_report
from photogrammetry_importer.photogrammetry_import_op import ImportMeshroom
from photogrammetry_importer.photogrammetry_import_op import ImportOpenMVG
from photogrammetry_importer.photogrammetry_import_op import ImportOpenSfM
from photogrammetry_importer.photogrammetry_import_op import ImportColmap
from photogrammetry_importer.photogrammetry_import_op import ImportNVM
from photogrammetry_importer.photogrammetry_import_op import ImportOpen3D
from photogrammetry_importer.photogrammetry_import_op import ImportPLY

from photogrammetry_importer.photogrammetry_export_op import ExportNVM
from photogrammetry_importer.photogrammetry_export_op import ExportColmap

from photogrammetry_importer.panel.opengl_panel import OpenGLPanel
from photogrammetry_importer.opengl.visualization_utils import redraw_points
bpy.app.handlers.load_post.append(redraw_points)

# =========================================================================
# === Uncomment for fast debugging ===
# from bpy.app.handlers import persistent
# @persistent
# def load_handler(dummy):
#     from photogrammetry_importer.file_handler.ply_file_handler import PLYFileHandler
#     from photogrammetry_importer.utils.visualization_utils import draw_points
#     points = PLYFileHandler.parse_ply_file('path/to/file.ply')

#     class LogOp():
#         def report(sef, arg1, arg2):
#             print(arg1, arg2)

#     log_op = LogOp()
#     draw_points(log_op, points)
# =========================================================================
# 

class PhotogrammetryImporterPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
 
    # Importer
    colmap_importer_bool: bpy.props.BoolProperty(
        name="Colmap Importer",
        default=True)

    meshroom_importer_bool: bpy.props.BoolProperty(
        name="Meshroom Importer",
        default=True)

    open3d_importer_bool: bpy.props.BoolProperty(
        name="Open3D Importer",
        default=True)
 
    opensfm_importer_bool: bpy.props.BoolProperty(
        name="OpenSfM Importer",
        default=True)
    
    openmvg_importer_bool: bpy.props.BoolProperty(
        name="OpenMVG Importer",
        default=True)

    ply_importer_bool: bpy.props.BoolProperty(
        name="PLY Importer",
        default=True)

    visualsfm_importer_bool: bpy.props.BoolProperty(
        name="VisualSfM Importer",
        default=True)

    # Exporter
    colmap_exporter_bool: bpy.props.BoolProperty(
        name="Colmap Exporter",
        default=True)
    
    visualsfm_exporter_bool: bpy.props.BoolProperty(
        name="VisualSfM Exporter",
        default=True)

    def draw(self, context):
        layout = self.layout
        split = layout.split()
        column = split.column()
        import_box = column.box()
        import_box.prop(self, "colmap_importer_bool")
        import_box.prop(self, "meshroom_importer_bool")
        import_box.prop(self, "open3d_importer_bool")
        import_box.prop(self, "opensfm_importer_bool")
        import_box.prop(self, "openmvg_importer_bool")
        import_box.prop(self, "ply_importer_bool")
        import_box.prop(self, "visualsfm_importer_bool")

        column = split.column()
        export_box = column.box()
        export_box.prop(self, "colmap_exporter_bool")
        export_box.prop(self, "visualsfm_exporter_bool")

        layout.operator("photogrammetry_importer.update_importers_and_exporters")

class UpdateImportersAndExporters(bpy.types.Operator):
    bl_idname = "photogrammetry_importer.update_importers_and_exporters"
    bl_label = "Update (Enable / Disable) Importers and Exporters"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        log_report('INFO', 'Update importers and exporters: ...', self)
        import_export_prefs = bpy.context.preferences.addons[__name__].preferences

        unregister_importers()
        register_importers(import_export_prefs)

        unregister_exporters()
        register_exporters(import_export_prefs)

        log_report('INFO', 'Update importers and exporters: Done', self)
        return {'FINISHED'}

# Import Functions
def colmap_import_operator_function(self, context):
    self.layout.operator(ImportColmap.bl_idname, text="Colmap Import (model/workspace)")

def meshroom_import_operator_function(self, context):
    self.layout.operator(ImportMeshroom.bl_idname, text="Meshroom Import (.sfm/.json/.mg)")

def open3d_import_operator_function(self, context):
    self.layout.operator(ImportOpen3D.bl_idname, text="Open3D Import (.log/.json)")

def opensfm_import_operator_function(self, context):
    self.layout.operator(ImportOpenSfM.bl_idname, text="OpenSfM Import (.json)")

def openmvg_import_operator_function(self, context):
    self.layout.operator(ImportOpenMVG.bl_idname, text="OpenMVG / Regard3D Import (.json)")

def ply_import_operator_function(self, context):
    self.layout.operator(ImportPLY.bl_idname, text="Point Cloud PLY Import (.ply)")

def visualsfm_import_operator_function(self, context):
    self.layout.operator(ImportNVM.bl_idname, text="VisualSfM Import (.nvm)")

# Export Functions
def colmap_export_operator_function(self, context):
    self.layout.operator(ExportColmap.bl_idname, text="Colmap Export (folder)")

def visualsfm_export_operator_function(self, context):
    self.layout.operator(ExportNVM.bl_idname, text="VisualSfM Export (.nvm)") 

# Define register/unregister Functions
def bl_idname_to_bpy_types_name(bl_idname, bpy_types_prefix):
    assert bpy_types_prefix in ['IMPORT', 'EXPORT']
    bl_idname_suffix = bl_idname.split('.')[1]
    return bpy_types_prefix + '_SCENE_OT_' + bl_idname_suffix

def is_registered(import_or_export_operator, operator_type):
    assert operator_type in ['IMPORT', 'EXPORT'] 
    return hasattr(
        bpy.types, 
        bl_idname_to_bpy_types_name(import_or_export_operator.bl_idname, operator_type))

def register_importer(condition, importer, append_function):
    # https://blenderartists.org/t/find-out-if-a-class-is-registered/602335
    if condition:
        if not is_registered(importer, operator_type='IMPORT'):
            bpy.utils.register_class(importer)
            bpy.types.TOPBAR_MT_file_import.append(append_function)

def unregister_importer(importer, append_function):
    if is_registered(importer, operator_type='IMPORT'):
        bpy.utils.unregister_class(importer)
        bpy.types.TOPBAR_MT_file_import.remove(append_function)

def register_exporter(condition, exporter, append_function):
    # https://blenderartists.org/t/find-out-if-a-class-is-registered/602335
    if condition:
        if not is_registered(exporter, operator_type='EXPORT'):
            bpy.utils.register_class(exporter)
            bpy.types.TOPBAR_MT_file_export.append(append_function)

def unregister_exporter(exporter, append_function):
    if is_registered(exporter, operator_type='EXPORT'):
        bpy.utils.unregister_class(exporter)
        bpy.types.TOPBAR_MT_file_export.remove(append_function)

def register_importers(import_prefs):
    register_importer(import_prefs.colmap_importer_bool, ImportColmap, colmap_import_operator_function)
    register_importer(import_prefs.meshroom_importer_bool, ImportMeshroom, meshroom_import_operator_function)  
    register_importer(import_prefs.open3d_importer_bool, ImportOpen3D, open3d_import_operator_function)  
    register_importer(import_prefs.opensfm_importer_bool, ImportOpenSfM, opensfm_import_operator_function)  
    register_importer(import_prefs.openmvg_importer_bool, ImportOpenMVG, openmvg_import_operator_function)  
    register_importer(import_prefs.ply_importer_bool, ImportPLY, ply_import_operator_function)  
    register_importer(import_prefs.visualsfm_importer_bool, ImportNVM, visualsfm_import_operator_function)

def unregister_importers():
    unregister_importer(ImportColmap, colmap_import_operator_function)
    unregister_importer(ImportMeshroom, meshroom_import_operator_function)  
    unregister_importer(ImportOpen3D, open3d_import_operator_function)  
    unregister_importer(ImportOpenSfM, opensfm_import_operator_function)  
    unregister_importer(ImportOpenMVG, openmvg_import_operator_function)  
    unregister_importer(ImportPLY, ply_import_operator_function)  
    unregister_importer(ImportNVM, visualsfm_import_operator_function)

def register_exporters(export_prefs):
    register_exporter(export_prefs.colmap_exporter_bool, ExportColmap, colmap_export_operator_function)
    register_exporter(export_prefs.visualsfm_exporter_bool, ExportNVM, visualsfm_export_operator_function)

def unregister_exporters():
    unregister_exporter(ExportColmap, colmap_export_operator_function)
    unregister_exporter(ExportNVM, visualsfm_export_operator_function)

def register():
    bpy.utils.register_class(UpdateImportersAndExporters)
    bpy.utils.register_class(PhotogrammetryImporterPreferences)

    import_export_prefs = bpy.context.preferences.addons[__name__].preferences
    register_importers(import_export_prefs)
    register_exporters(import_export_prefs)

    bpy.utils.register_class(OpenGLPanel)

    # === Uncomment for fast debugging ===
    # bpy.app.handlers.load_post.append(load_handler)

    print("Registered {} with {} modules".format(bl_info["name"], len(modules)))

def unregister():
    bpy.utils.unregister_class(UpdateImportersAndExporters)
    bpy.utils.unregister_class(PhotogrammetryImporterPreferences)

    unregister_importers()
    unregister_exporters()

    bpy.utils.unregister_class(OpenGLPanel)

    print("Unregistered {}".format(bl_info["name"]))


if __name__ == '__main__':
    print('main called')
    
