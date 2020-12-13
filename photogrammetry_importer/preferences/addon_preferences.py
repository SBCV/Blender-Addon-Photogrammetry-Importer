import os
import bpy
from bpy.props import BoolProperty, EnumProperty

from photogrammetry_importer.preferences.dependency_preferences import (
    InstallOptionalDependencies,
    UninstallOptionalDependencies,
    get_dependencies,
    get_module_status_description,
)
from photogrammetry_importer.utility.blender_logging_utility import log_report
from photogrammetry_importer.importers.camera_importer import CameraImporter
from photogrammetry_importer.importers.point_importer import PointImporter
from photogrammetry_importer.importers.mesh_importer import MeshImporter

from photogrammetry_importer.registration.registration import (
    register_importers,
    unregister_importers,
    register_exporters,
    unregister_exporters,
)


def _get_addon_name():
    return __name__.split(".")[0]


class PhotogrammetryImporterPreferences(
    bpy.types.AddonPreferences,
    CameraImporter,
    PointImporter,
    MeshImporter,
):
    # __name__ == photogrammetry_importer.preferences.addon_preferences
    bl_idname = _get_addon_name()

    # Importer
    colmap_importer_bool: BoolProperty(name="Colmap Importer", default=True)
    meshroom_importer_bool: BoolProperty(
        name="Meshroom Importer", default=True
    )
    mve_importer_bool: BoolProperty(name="MVE Importer", default=True)
    open3d_importer_bool: BoolProperty(name="Open3D Importer", default=True)
    opensfm_importer_bool: BoolProperty(name="OpenSfM Importer", default=True)
    openmvg_importer_bool: BoolProperty(name="OpenMVG Importer", default=True)
    ply_importer_bool: BoolProperty(name="PLY Importer", default=True)
    visualsfm_importer_bool: BoolProperty(
        name="VisualSfM Importer", default=True
    )
    # Exporter
    colmap_exporter_bool: BoolProperty(name="Colmap Exporter", default=True)
    visualsfm_exporter_bool: BoolProperty(
        name="VisualSfM Exporter", default=True
    )

    @classmethod
    def register(cls):
        bpy.utils.register_class(InstallOptionalDependencies)
        bpy.utils.register_class(UninstallOptionalDependencies)
        bpy.utils.register_class(ResetPreferences)
        bpy.utils.register_class(UpdateImportersAndExporters)

    @classmethod
    def unregister(cls):
        bpy.utils.unregister_class(InstallOptionalDependencies)
        bpy.utils.unregister_class(UninstallOptionalDependencies)
        bpy.utils.unregister_class(ResetPreferences)
        bpy.utils.unregister_class(UpdateImportersAndExporters)

    def draw(self, context):
        layout = self.layout
        install_dependency_box = layout.box()
        install_dependency_box.operator(
            InstallOptionalDependencies.bl_idname, icon="CONSOLE"
        )
        install_dependency_box.operator(
            UninstallOptionalDependencies.bl_idname, icon="CONSOLE"
        )
        dependencies = get_dependencies()
        for dependency in dependencies:
            status = get_module_status_description(dependency)
            install_dependency_box.label(
                text=f"{dependency.gui_name}: {status}"
            )
        install_dependency_box.label(
            text="After uninstalling the dependencies one may restart Blender "
            + " to clear the references to the module within Blender."
        )

        reset_box = layout.box()
        reset_box.operator(ResetPreferences.bl_idname)

        importer_exporter_box = layout.box()
        importer_exporter_box.label(text="Active Importers / Exporters:")
        split = importer_exporter_box.split()
        column = split.column()
        importer_box = column.box()
        importer_box.prop(self, "colmap_importer_bool")
        importer_box.prop(self, "meshroom_importer_bool")
        importer_box.prop(self, "mve_importer_bool")
        importer_box.prop(self, "open3d_importer_bool")
        importer_box.prop(self, "opensfm_importer_bool")
        importer_box.prop(self, "openmvg_importer_bool")
        importer_box.prop(self, "ply_importer_bool")
        importer_box.prop(self, "visualsfm_importer_bool")

        column = split.column()
        exporter_box = column.box()
        exporter_box.prop(self, "colmap_exporter_bool")
        exporter_box.prop(self, "visualsfm_exporter_bool")

        importer_exporter_box.operator(UpdateImportersAndExporters.bl_idname)

        import_options_box = layout.box()
        import_options_box.label(text="Default Import Options:")

        self.draw_camera_options(import_options_box, draw_everything=True)
        self.draw_point_options(import_options_box, draw_everything=True)
        self.draw_mesh_options(import_options_box)

    def copy_values_from_annotations(self, source):
        for annotation_key in source.__annotations__:
            source_annotation = source.__annotations__[annotation_key]
            if source_annotation[0] == EnumProperty:
                source_default_value = source_annotation[1]["items"][0][0]
            else:
                source_default_value = source_annotation[1]["default"]
            setattr(self, annotation_key, source_default_value)

    def reset(self):
        camera_importer_original = CameraImporter()
        point_importer_original = PointImporter()
        mesh_importer_original = MeshImporter()

        self.copy_values_from_annotations(camera_importer_original)
        self.copy_values_from_annotations(point_importer_original)
        self.copy_values_from_annotations(mesh_importer_original)


class ResetPreferences(bpy.types.Operator):
    bl_idname = "photogrammetry_importer.reset_preferences"
    bl_label = "Reset Preferences to Factory Settings"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        log_report("INFO", "Reset preferences: ...", self)
        addon_name = _get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[
            addon_name
        ].preferences
        import_export_prefs.reset()

        unregister_importers()
        register_importers(import_export_prefs)

        unregister_exporters()
        register_exporters(import_export_prefs)

        log_report("INFO", "Reset preferences: Done", self)
        return {"FINISHED"}


class UpdateImportersAndExporters(bpy.types.Operator):
    bl_idname = "photogrammetry_importer.update_importers_and_exporters"
    bl_label = "Update (Enable / Disable) Importers and Exporters"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        log_report("INFO", "Update importers and exporters: ...", self)
        addon_name = _get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[
            addon_name
        ].preferences

        unregister_importers()
        register_importers(import_export_prefs)

        unregister_exporters()
        register_exporters(import_export_prefs)

        log_report("INFO", "Update importers and exporters: Done", self)
        return {"FINISHED"}
