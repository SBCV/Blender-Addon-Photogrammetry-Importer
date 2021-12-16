import os
import bpy
from bpy.props import BoolProperty, EnumProperty

from photogrammetry_importer.preferences.dependency import (
    InstallOptionalDependenciesOperator,
    UninstallOptionalDependenciesOperator,
    PipManager,
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
    point_data_importer_bool: BoolProperty(
        name="Point Data Importer", default=True
    )
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

    @staticmethod
    def _get_installation_status_str(installation_status):
        if installation_status:
            status = "Installed"
        else:
            status = "Not installed"
        return status

    @staticmethod
    def _get_package_info_str(
        info_str,
        installation_status,
        setuptools_missing_str="",
        removed_in_current_sesssion_str="",
    ):
        if installation_status:
            if info_str is None:
                # In this case the info_str could not been determined, since
                # the setuptools package is missing
                info_str = setuptools_missing_str
        else:
            if info_str is None:
                # In this case the module has not been removed in the
                # current Blender session
                info_str = ""
            else:
                # In this case the module was previously installed and has
                # been removed in the current Blender session
                info_str = removed_in_current_sesssion_str
        return info_str

    def _draw_dependencies(self, install_dependency_box):
        install_dependency_box.label(text="Dependencies:")
        install_dependency_box.operator(
            InstallOptionalDependenciesOperator.bl_idname, icon="CONSOLE"
        )
        install_dependency_box.operator(
            UninstallOptionalDependenciesOperator.bl_idname, icon="CONSOLE"
        )
        row = install_dependency_box.row()
        row.label(text="Pip Installation Status:")
        setuptools_missing_str = "Install setuptools (and restart Blender) to show version and location"
        removed_in_current_sesssion_str = (
            "(Restart Blender to clear imported module)"
        )

        pip_manager = PipManager.get_singleton()
        pip_status_box = install_dependency_box.box()
        pip_status_box_split = pip_status_box.split()
        pip_status_box_1 = pip_status_box_split.column()
        pip_status_box_2 = pip_status_box_split.column()
        pip_status_box_3 = pip_status_box_split.column()
        pip_status_box_4 = pip_status_box_split.column()

        pip_installation_status = (
            pip_manager.pip_dependency_status.installation_status
        )
        pip_installation_status_str = self._get_installation_status_str(
            pip_installation_status
        )
        version_str, location_str = pip_manager.get_package_info()
        version_str = self._get_package_info_str(
            version_str, pip_installation_status, setuptools_missing_str
        )
        location_str = self._get_package_info_str(
            location_str, pip_installation_status
        )

        pip_status_box_1.label(text="Pip")
        pip_status_box_2.label(text=f"{pip_installation_status_str}")
        pip_status_box_3.label(text=f"{version_str}")
        pip_status_box_4.label(text=f"{location_str}")

        row = install_dependency_box.row()
        row.label(text="Dependency Installation Status:")
        dependency_status_box = install_dependency_box.box()
        dependency_status_box_split = dependency_status_box.split()
        dependency_status_box_column_1 = dependency_status_box_split.column()
        dependency_status_box_column_2 = dependency_status_box_split.column()
        dependency_status_box_column_3 = dependency_status_box_split.column()
        dependency_status_box_column_4 = dependency_status_box_split.column()

        dependency_manager = OptionalDependencyManager.get_singleton()
        dependencies = dependency_manager.get_dependencies()
        for dependency in dependencies:
            dependency_installation_status = dependency.installation_status
            dependency_installation_status_str = self._get_installation_status_str(
                dependency_installation_status
            )
            version_str, location_str = dependency.get_package_info()
            version_str = self._get_package_info_str(
                version_str,
                dependency_installation_status,
                setuptools_missing_str,
                removed_in_current_sesssion_str,
            )
            location_str = self._get_package_info_str(
                location_str, dependency_installation_status
            )

            dependency_status_box_column_1.label(text=f"{dependency.gui_name}")
            dependency_status_box_column_2.label(
                text=f"{dependency_installation_status_str}"
            )
            dependency_status_box_column_3.label(text=f"{version_str}")
            dependency_status_box_column_4.label(text=f"{location_str}")

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
        importer_box.prop(self, "point_data_importer_bool")
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
