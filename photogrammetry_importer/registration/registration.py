import importlib
import bpy

from photogrammetry_importer.operators.colmap_import_op import (
    ImportColmapOperator,
)
from photogrammetry_importer.operators.meshroom_import_op import (
    ImportMeshroomOperator,
)
from photogrammetry_importer.operators.mve_import_op import ImportMVEOperator
from photogrammetry_importer.operators.visualsfm_import_op import (
    ImportVisualSfMOperator,
)
from photogrammetry_importer.operators.openmvg_import_op import (
    ImportOpenMVGOperator,
)
from photogrammetry_importer.operators.opensfm_import_op import (
    ImportOpenSfMOperator,
)
from photogrammetry_importer.operators.open3d_import_op import (
    ImportOpen3DOperator,
)
from photogrammetry_importer.operators.point_data_import_op import (
    ImportPointDataOperator,
)

from photogrammetry_importer.operators.visualsfm_export_op import (
    ExportVisualSfMOperator,
)
from photogrammetry_importer.operators.colmap_export_op import (
    ExportColmapOperator,
)

# Definining the following import and export functions within the
# "Registration" class causes different errors when hovering over entries in
# "file/import" of the following form:
# "rna_uiItemO: operator missing srna 'import_scene.colmap_model'""

# Import Functions
def _colmap_import_operator_function(topbar_file_import, context):
    topbar_file_import.layout.operator(
        ImportColmapOperator.bl_idname, text="Colmap (model/workspace)"
    )


def _meshroom_import_operator_function(topbar_file_import, context):
    topbar_file_import.layout.operator(
        ImportMeshroomOperator.bl_idname,
        text="Meshroom (.sfm/.json/.mg)",
    )


def _mve_import_operator_function(topbar_file_import, context):
    topbar_file_import.layout.operator(
        ImportMVEOperator.bl_idname, text="MVE (workspace)"
    )


def _open3d_import_operator_function(topbar_file_import, context):
    topbar_file_import.layout.operator(
        ImportOpen3DOperator.bl_idname, text="Open3D (.log/.json)"
    )


def _opensfm_import_operator_function(topbar_file_import, context):
    topbar_file_import.layout.operator(
        ImportOpenSfMOperator.bl_idname, text="OpenSfM (.json)"
    )


def _openmvg_import_operator_function(topbar_file_import, context):
    topbar_file_import.layout.operator(
        ImportOpenMVGOperator.bl_idname,
        text="OpenMVG / Regard3D (.json)",
    )


def _point_data_import_operator_function(topbar_file_import, context):
    module_spec = importlib.util.find_spec("pyntcloud")
    if module_spec is not None:
        suffix = "(.ply/.pcd/.las/.asc/.pts/.csv)"
    else:
        suffix = "[Pyntcloud is NOT installed]"
    topbar_file_import.layout.operator(
        ImportPointDataOperator.bl_idname,
        text="Point Data " + suffix,
    )


def _visualsfm_import_operator_function(topbar_file_import, context):
    topbar_file_import.layout.operator(
        ImportVisualSfMOperator.bl_idname, text="VisualSfM (.nvm)"
    )


# Export Functions
def _colmap_export_operator_function(topbar_file_export, context):
    topbar_file_export.layout.operator(
        ExportColmapOperator.bl_idname, text="Colmap (folder)"
    )


def _visualsfm_export_operator_function(topbar_file_export, context):
    topbar_file_export.layout.operator(
        ExportVisualSfMOperator.bl_idname, text="VisualSfM (.nvm)"
    )


class Registration:
    """Class to register import and export operators."""

    # Define register/unregister Functions
    @staticmethod
    def _bl_idname_to_bpy_types_name(bl_idname, bpy_types_prefix):
        assert bpy_types_prefix in ["IMPORT", "EXPORT"]
        bl_idname_suffix = bl_idname.split(".")[1]
        return bpy_types_prefix + "_SCENE_OT_" + bl_idname_suffix

    @classmethod
    def _is_registered(cls, import_or_export_operator, operator_type):
        """Determine if an importer/exporter is already registered."""
        assert operator_type in ["IMPORT", "EXPORT"]
        return hasattr(
            bpy.types,
            cls._bl_idname_to_bpy_types_name(
                import_or_export_operator.bl_idname, operator_type
            ),
        )

    @classmethod
    def _register_importer(cls, condition, importer, append_function):
        """Register a single importer."""
        # https://blenderartists.org/t/find-out-if-a-class-is-registered/602335
        if condition:
            if not cls._is_registered(importer, operator_type="IMPORT"):
                bpy.utils.register_class(importer)
                bpy.types.TOPBAR_MT_file_import.append(append_function)

    @classmethod
    def _unregister_importer(cls, importer, append_function):
        """Unregister a single importer."""
        if cls._is_registered(importer, operator_type="IMPORT"):
            bpy.utils.unregister_class(importer)
            bpy.types.TOPBAR_MT_file_import.remove(append_function)

    @classmethod
    def _register_exporter(cls, condition, exporter, append_function):
        """Register a single exporter."""
        # https://blenderartists.org/t/find-out-if-a-class-is-registered/602335
        if condition:
            if not cls._is_registered(exporter, operator_type="EXPORT"):
                bpy.utils.register_class(exporter)
                bpy.types.TOPBAR_MT_file_export.append(append_function)

    @classmethod
    def _unregister_exporter(cls, exporter, append_function):
        """Unregister a single exporter."""
        if cls._is_registered(exporter, operator_type="EXPORT"):
            bpy.utils.unregister_class(exporter)
            bpy.types.TOPBAR_MT_file_export.remove(append_function)

    @classmethod
    def register_importers(cls, import_prefs):
        """Register importers according to the import preferences."""
        cls._register_importer(
            import_prefs.colmap_importer_bool,
            ImportColmapOperator,
            _colmap_import_operator_function,
        )
        cls._register_importer(
            import_prefs.meshroom_importer_bool,
            ImportMeshroomOperator,
            _meshroom_import_operator_function,
        )
        cls._register_importer(
            import_prefs.mve_importer_bool,
            ImportMVEOperator,
            _mve_import_operator_function,
        )
        cls._register_importer(
            import_prefs.open3d_importer_bool,
            ImportOpen3DOperator,
            _open3d_import_operator_function,
        )
        cls._register_importer(
            import_prefs.opensfm_importer_bool,
            ImportOpenSfMOperator,
            _opensfm_import_operator_function,
        )
        cls._register_importer(
            import_prefs.openmvg_importer_bool,
            ImportOpenMVGOperator,
            _openmvg_import_operator_function,
        )
        cls._register_importer(
            import_prefs.point_data_importer_bool,
            ImportPointDataOperator,
            _point_data_import_operator_function,
        )
        cls._register_importer(
            import_prefs.visualsfm_importer_bool,
            ImportVisualSfMOperator,
            _visualsfm_import_operator_function,
        )

    @classmethod
    def unregister_importers(cls):
        """Unregister all registered importers."""
        cls._unregister_importer(
            ImportColmapOperator, _colmap_import_operator_function
        )
        cls._unregister_importer(
            ImportMeshroomOperator, _meshroom_import_operator_function
        )
        cls._unregister_importer(
            ImportMVEOperator, _mve_import_operator_function
        )
        cls._unregister_importer(
            ImportOpen3DOperator, _open3d_import_operator_function
        )
        cls._unregister_importer(
            ImportOpenSfMOperator, _opensfm_import_operator_function
        )
        cls._unregister_importer(
            ImportOpenMVGOperator, _openmvg_import_operator_function
        )
        cls._unregister_importer(
            ImportPointDataOperator, _point_data_import_operator_function
        )
        cls._unregister_importer(
            ImportVisualSfMOperator, _visualsfm_import_operator_function
        )

    @classmethod
    def register_exporters(cls, export_prefs):
        """Register exporters according to the export preferences."""
        cls._register_exporter(
            export_prefs.colmap_exporter_bool,
            ExportColmapOperator,
            _colmap_export_operator_function,
        )
        cls._register_exporter(
            export_prefs.visualsfm_exporter_bool,
            ExportVisualSfMOperator,
            _visualsfm_export_operator_function,
        )

    @classmethod
    def unregister_exporters(cls):
        """Unregister all registered exporters."""
        cls._unregister_exporter(
            ExportColmapOperator, _colmap_export_operator_function
        )
        cls._unregister_exporter(
            ExportVisualSfMOperator, _visualsfm_export_operator_function
        )
