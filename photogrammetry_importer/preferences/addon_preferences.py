import os
import bpy
from bpy.props import BoolProperty

from photogrammetry_importer.blender_logging import log_report
from photogrammetry_importer.camera_import_properties import CameraImportProperties
from photogrammetry_importer.point_import_properties import PointImportProperties
from photogrammetry_importer.mesh_import_properties import MeshImportProperties

from photogrammetry_importer.registration import register_importers
from photogrammetry_importer.registration import unregister_importers
from photogrammetry_importer.registration import register_exporters
from photogrammetry_importer.registration import unregister_exporters

def get_addon_name():
    return __name__.split('.')[0]

class PhotogrammetryImporterPreferences(bpy.types.AddonPreferences,
                                        CameraImportProperties,
                                        PointImportProperties,
                                        MeshImportProperties):

    # __name__ == photogrammetry_importer.preferences.addon_preferences
    bl_idname = get_addon_name()

    # Importer
    colmap_importer_bool: BoolProperty(
        name="Colmap Importer",
        default=True)

    meshroom_importer_bool: BoolProperty(
        name="Meshroom Importer",
        default=True)

    open3d_importer_bool: BoolProperty(
        name="Open3D Importer",
        default=True)

    opensfm_importer_bool: BoolProperty(
        name="OpenSfM Importer",
        default=True)

    openmvg_importer_bool: BoolProperty(
        name="OpenMVG Importer",
        default=True)

    ply_importer_bool: BoolProperty(
        name="PLY Importer",
        default=True)

    visualsfm_importer_bool: BoolProperty(
        name="VisualSfM Importer",
        default=True)

    # Exporter
    colmap_exporter_bool: BoolProperty(
        name="Colmap Exporter",
        default=True)

    visualsfm_exporter_bool: BoolProperty(
        name="VisualSfM Exporter",
        default=True)

    def draw(self, context):
        layout = self.layout
        importer_exporter_box = layout.box()
        importer_exporter_box.label(
            text='Active Importers / Exporters:')
        split = importer_exporter_box.split()
        column = split.column()
        importer_box = column.box()
        importer_box.prop(self, "colmap_importer_bool")
        importer_box.prop(self, "meshroom_importer_bool")
        importer_box.prop(self, "open3d_importer_bool")
        importer_box.prop(self, "opensfm_importer_bool")
        importer_box.prop(self, "openmvg_importer_bool")
        importer_box.prop(self, "ply_importer_bool")
        importer_box.prop(self, "visualsfm_importer_bool")

        column = split.column()
        exporter_box = column.box()
        exporter_box.prop(self, "colmap_exporter_bool")
        exporter_box.prop(self, "visualsfm_exporter_bool")

        importer_exporter_box.operator("photogrammetry_importer.update_importers_and_exporters")

        import_options_box = layout.box()
        import_options_box.label(text='Default Import Options:')

        self.draw_camera_options(import_options_box, draw_everything=True)
        self.draw_point_options(import_options_box, draw_everything=True)
        self.draw_mesh_options(import_options_box)


class UpdateImportersAndExporters(bpy.types.Operator):
    bl_idname = "photogrammetry_importer.update_importers_and_exporters"
    bl_label = "Update (Enable / Disable) Importers and Exporters"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        log_report('INFO', 'Update importers and exporters: ...', self)
        addon_name = get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[addon_name].preferences

        unregister_importers()
        register_importers(import_export_prefs)

        unregister_exporters()
        register_exporters(import_export_prefs)

        log_report('INFO', 'Update importers and exporters: Done', self)
        return {'FINISHED'}
