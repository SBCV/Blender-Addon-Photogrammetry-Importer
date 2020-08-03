import bpy

from photogrammetry_importer.operators.photogrammetry_import_op import ImportColmap
from photogrammetry_importer.operators.photogrammetry_import_op import ImportMeshroom
from photogrammetry_importer.operators.photogrammetry_import_op import ImportMVE
from photogrammetry_importer.operators.photogrammetry_import_op import ImportNVM
from photogrammetry_importer.operators.photogrammetry_import_op import ImportOpenMVG
from photogrammetry_importer.operators.photogrammetry_import_op import ImportOpenSfM
from photogrammetry_importer.operators.photogrammetry_import_op import ImportOpen3D
from photogrammetry_importer.operators.photogrammetry_import_op import ImportPLY

from photogrammetry_importer.operators.photogrammetry_export_op import ExportNVM
from photogrammetry_importer.operators.photogrammetry_export_op import ExportColmap


# Import Functions
def colmap_import_operator_function(self, context):
    self.layout.operator(ImportColmap.bl_idname, text="Colmap Import (model/workspace)")

def meshroom_import_operator_function(self, context):
    self.layout.operator(ImportMeshroom.bl_idname, text="Meshroom Import (.sfm/.json/.mg)")

def mve_import_operator_function(self, context):
    self.layout.operator(ImportMVE.bl_idname, text="MVE Import (workspace)")

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
    register_importer(import_prefs.mve_importer_bool, ImportMVE, mve_import_operator_function)
    register_importer(import_prefs.open3d_importer_bool, ImportOpen3D, open3d_import_operator_function)
    register_importer(import_prefs.opensfm_importer_bool, ImportOpenSfM, opensfm_import_operator_function)
    register_importer(import_prefs.openmvg_importer_bool, ImportOpenMVG, openmvg_import_operator_function)
    register_importer(import_prefs.ply_importer_bool, ImportPLY, ply_import_operator_function)
    register_importer(import_prefs.visualsfm_importer_bool, ImportNVM, visualsfm_import_operator_function)


def unregister_importers():
    unregister_importer(ImportColmap, colmap_import_operator_function)
    unregister_importer(ImportMeshroom, meshroom_import_operator_function)
    unregister_importer(ImportMVE, mve_import_operator_function)
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

