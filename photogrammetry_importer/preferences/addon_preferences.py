import os
import bpy
import json
from bpy.props import BoolProperty, EnumProperty, StringProperty

from photogrammetry_importer.preferences.dependency import (
    InstallOptionalDependenciesOperator,
    UninstallOptionalDependenciesOperator,
    PipManager,
    OptionalDependencyManager,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report
from photogrammetry_importer.utility.ui_utility import add_multi_line_label
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
    # Management of system paths
    sys_path_list_str: StringProperty(
        name="System Path List Decoded String", default="[]"
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

    def _draw_dependency(
        self,
        dependency,
        setuptools_missing_str,
        removed_in_current_sesssion_str,
        dependencies_status_box,
    ):
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

        dependency_status_box = dependencies_status_box.box()

        # https://blender.stackexchange.com/questions/51256/how-to-create-uilist-with-auto-aligned-three-columns
        #  This layout approach splits the remainder of the row (recursively).
        name_column = dependency_status_box.split(factor=0.1)
        name_column.label(text=f"{dependency.gui_name}")
        status_column = name_column.split(factor=0.1)
        status_column.label(text=f"{dependency_installation_status_str}")
        verson_location_column = status_column.split()
        version_location_str = f"{version_str}"
        if location_str != "":
            # Blender does not support tabs "\t"
            version_location_str += f"    ({location_str})"
        verson_location_column.label(text=version_location_str)

        # This layout approach adds more columns than required to enforce left
        #  alignment of buttons.
        column_flow_layout = dependency_status_box.column_flow(columns=5)
        package_name = dependency.package_name
        # Add operator to first column
        install_dependency_props = column_flow_layout.operator(
            InstallOptionalDependenciesOperator.bl_idname,
            text=f"Install {dependency.gui_name}",
            icon="CONSOLE",
        )
        install_dependency_props.dependency_package_name = package_name
        # Add operator to second column
        install_dependency_props = column_flow_layout.operator(
            UninstallOptionalDependenciesOperator.bl_idname,
            text=f"Remove {dependency.gui_name}",
            icon="CONSOLE",
        )
        install_dependency_props.dependency_package_name = package_name

    def _draw_dependencies(self, install_dependency_box):
        install_dependency_box.label(text="Dependencies:")
        install_dependency_button_box = install_dependency_box.column_flow(
            columns=2
        )
        install_dependency_props = install_dependency_button_box.operator(
            InstallOptionalDependenciesOperator.bl_idname, icon="CONSOLE"
        )
        install_dependency_props.dependency_package_name = ""

        remove_dependency_button_box = install_dependency_box.column_flow(
            columns=2
        )
        uninstall_dependency_props = remove_dependency_button_box.operator(
            UninstallOptionalDependenciesOperator.bl_idname, icon="CONSOLE"
        )
        uninstall_dependency_props.dependency_package_name = ""

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
        dependencies_status_box = install_dependency_box.box()

        dependency_manager = OptionalDependencyManager.get_singleton()
        dependencies = dependency_manager.get_dependencies()
        for dependency in dependencies:
            self._draw_dependency(
                dependency,
                setuptools_missing_str,
                removed_in_current_sesssion_str,
                dependencies_status_box,
            )

        dependency_status_description_box = dependencies_status_box.box()
        dependency_status_description_box.label(
            text="Note: After uninstalling the dependencies one must restart"
            " Blender to clear the references to the module within Blender."
        )

        row = install_dependency_box.row()
        row.label(text="Added system paths:")

        sys_paths_box = install_dependency_box.box()
        addon_name = _get_addon_name()
        prefs = bpy.context.preferences.addons[addon_name].preferences
        try:
            if prefs.sys_path_list_str != "[]":
                for entry in json.loads(prefs.sys_path_list_str):
                    sys_paths_box.label(text=f"{entry}")
            else:
                sys_paths_box.label(text="None")
        except json.decoder.JSONDecodeError as e:
            sys_paths_box.label(text="Error: Could not parse paths!")

        sys_paths_description_box = sys_paths_box.box()
        dependency_description = (
            "Note: When importing the installed dependencies, potentially not"
            " all required modules may be found - since Blender modifies the"
            " path available in sys.path. To prevent this, the addon will add"
            " the missing system paths (i.e. the paths that have been"
            " available during installation of the dependencies) to Blender's"
            " sys.path."
        )
        add_multi_line_label(sys_paths_description_box, dependency_description)

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
