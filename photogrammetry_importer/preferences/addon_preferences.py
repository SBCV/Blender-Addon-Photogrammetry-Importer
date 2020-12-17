import os
import bpy
from bpy.props import BoolProperty, EnumProperty

from photogrammetry_importer.preferences.dependency import (
    InstallOptionalDependenciesOperator,
    UninstallOptionalDependenciesOperator,
    OptionalDependencyManager,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report
from photogrammetry_importer.importers.camera_importer import CameraImporter
from photogrammetry_importer.importers.point_importer import PointImporter
from photogrammetry_importer.importers.mesh_importer import MeshImporter

from photogrammetry_importer.registration.registration import Registration


def _get_addon_name():
    return __name__.split(".")[0]


class AddonPreferences(
    bpy.types.AddonPreferences,
    CameraImporter,
    PointImporter,
    MeshImporter,
):
    """Class to manage persistent addon preferences."""

    # __name__ == photogrammetry_importer.preferences.addon_preferences
    bl_idname = _get_addon_name()

    visible_preferences: EnumProperty(
        name="Use original frames",
        items=(
            ("DEPENDENCIES", "Dependencies", ""),
            ("IMPORTEREXPORTER", "Importer / Exporter", ""),
            ("IMPORTOPTIONS", "Import Options", ""),
        ),
    )

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
        """Register corresponding operators."""
        bpy.utils.register_class(InstallOptionalDependenciesOperator)
        bpy.utils.register_class(UninstallOptionalDependenciesOperator)
        bpy.utils.register_class(ResetImportOptionsOperator)
        bpy.utils.register_class(UpdateImporterExporterOperator)

    @classmethod
    def unregister(cls):
        """Unregister corresponding operators."""
        bpy.utils.unregister_class(InstallOptionalDependenciesOperator)
        bpy.utils.unregister_class(UninstallOptionalDependenciesOperator)
        bpy.utils.unregister_class(ResetImportOptionsOperator)
        bpy.utils.unregister_class(UpdateImporterExporterOperator)

    def _draw_dependencies(self, install_dependency_box):
        install_dependency_box.label(text="Dependencies:")
        install_dependency_box.operator(
            InstallOptionalDependenciesOperator.bl_idname, icon="CONSOLE"
        )
        install_dependency_box.operator(
            UninstallOptionalDependenciesOperator.bl_idname, icon="CONSOLE"
        )
        dependency_manager = OptionalDependencyManager.get_singleton()
        dependencies = dependency_manager.get_dependencies()
        for dependency in dependencies:
            status = dependency.get_installation_status()
            install_dependency_box.label(
                text=f"{dependency.gui_name}: {status}"
            )
        install_dependency_box.label(
            text="After uninstalling the dependencies one must restart Blender"
            " to clear the references to the module within Blender."
        )

    def _draw_importer_exporter(self, importer_exporter_box):
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

        importer_exporter_box.operator(
            UpdateImporterExporterOperator.bl_idname
        )

    def draw(self, context):
        """Draw available preference options."""
        layout = self.layout
        layout.row()
        layout.row().label(
            text='Select "Dependencies", "Importer / Exporter" or'
            ' "Import Options" to view the corresponding preferences.'
        )
        layout.row().prop(self, "visible_preferences", expand=True)
        layout.row()
        if self.visible_preferences == "DEPENDENCIES":
            install_dependency_box = layout.box()
            self._draw_dependencies(install_dependency_box)

        if self.visible_preferences == "IMPORTEREXPORTER":
            importer_exporter_box = layout.box()
            self._draw_importer_exporter(importer_exporter_box)

        if self.visible_preferences == "IMPORTOPTIONS":
            import_options_box = layout.box()
            import_options_box.label(text="Default Import Options:")
            import_options_box.operator(ResetImportOptionsOperator.bl_idname)

            self.draw_camera_options(import_options_box, draw_everything=True)
            self.draw_point_options(import_options_box, draw_everything=True)
            self.draw_mesh_options(import_options_box)

    def _copy_values_from_annotations(self, source):
        for annotation_key in source.__annotations__:
            source_annotation = source.__annotations__[annotation_key]
            if source_annotation[0] == EnumProperty:
                source_default_value = source_annotation[1]["items"][0][0]
            else:
                source_default_value = source_annotation[1]["default"]
            setattr(self, annotation_key, source_default_value)

    def reset_import_options(self):
        """Reset the import options to factor settings."""
        camera_importer_original = CameraImporter()
        point_importer_original = PointImporter()
        mesh_importer_original = MeshImporter()

        self._copy_values_from_annotations(camera_importer_original)
        self._copy_values_from_annotations(point_importer_original)
        self._copy_values_from_annotations(mesh_importer_original)


class UpdateImporterExporterOperator(bpy.types.Operator):
    """Operator to activate and deactivate importers and exporters."""

    bl_idname = "photogrammetry_importer.update_importer_exporter"
    bl_label = "Update (Enable / Disable) Importers and Exporters"

    def execute(self, context):
        """Activate and deactivate importers and exporters.

        Uses the selected options of :class:`.AddonPreferences` to determine
        active and inactive importers and exporters.
        """
        log_report("INFO", "Update importers and exporters: ...", self)
        addon_name = _get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[
            addon_name
        ].preferences

        Registration.unregister_importers()
        Registration.register_importers(import_export_prefs)

        Registration.unregister_exporters()
        Registration.register_exporters(import_export_prefs)

        log_report("INFO", "Update importers and exporters: Done", self)
        return {"FINISHED"}


class ResetImportOptionsOperator(bpy.types.Operator):
    """Operator to reset import options."""

    bl_idname = "photogrammetry_importer.reset_import_options"
    bl_label = "Reset Import Options to Factory Settings"

    def execute(self, context):
        """Reset import options to factory settings."""
        log_report("INFO", "Reset preferences: ...", self)
        addon_name = _get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[
            addon_name
        ].preferences
        import_export_prefs.reset_import_options()

        log_report("INFO", "Reset preferences: Done", self)
        return {"FINISHED"}
