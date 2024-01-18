import bpy
from bpy.props import (
    StringProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
)
from photogrammetry_importer.panels.view_synthesis_operators import (
    RunViewSynthesisOperator,
)


class ViewSynthesisPanelSettings(bpy.types.PropertyGroup):
    """Class for the settings of the View Synthesis panel in the 3D view."""

    execution_environment_items = [
        ("CONDA", "Use Conda to run the view synthesis script", "", 1),
        (
            "DEFAULT PYTHON",
            "Use the standard Python environment to run the view synthesis script",
            "",
            2,
        ),
    ]
    execution_environment: EnumProperty(
        name="Execution Environment Type",
        description="Defines which environment is used to run the script",
        items=execution_environment_items,
    )
    conda_exe_fp: StringProperty(
        name="Conda Executable Name or File Path",
        description="",
        default="conda",
    )
    conda_env_name: StringProperty(
        name="Conda Environment Name",
        description="",
        default="base",
    )
    python_exe_fp: StringProperty(
        name="Python Executable Name or File Path",
        description="",
        default="python",
    )
    additional_system_dps: StringProperty(
        name="Additional System Paths to Run the Script",
        description="Additional system paths required to run the script. Two "
        "paths must be separated by a whitespace.",
        default="path/to/instant-ngp/build",
    )
    view_synthesis_executable_fp: StringProperty(
        name="View Synthesis Script File Name",
        description="",
        default="path/to/Blender-Addon-Photogrammetry-Importer/example_view_synthesis_scripts/instant_ngp.py",
    )
    view_synthesis_snapshot_fp: StringProperty(
        name="View Synthesis Output File Name",
        description="",
        default="path/to/instant-ngp/data/nerf/fox_colmap/snapshot.msgpack",
    )
    samples_per_pixel: IntProperty(
        name="Samples Per Pixel",
        description="",
        default=1,
    )


class ViewSynthesisPanel(bpy.types.Panel):
    """Class that defines the view synthesis panel in the 3D view."""

    bl_label = "View Synthesis Panel"
    bl_idname = "IMPORT_VIEW_SYNTHESIS_PT_manage_view_synthesis_visualization"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PhotogrammetryImporter"

    @classmethod
    def poll(cls, context):
        """Return the availability status of the panel."""
        return True

    @classmethod
    def register(cls):
        """Register properties and operators corresponding to this panel."""

        bpy.utils.register_class(ViewSynthesisPanelSettings)
        bpy.types.Scene.view_synthesis_panel_settings = PointerProperty(
            type=ViewSynthesisPanelSettings
        )
        bpy.utils.register_class(RunViewSynthesisOperator)

    @classmethod
    def unregister(cls):
        """Unregister properties and operators corresponding to this panel."""
        bpy.utils.unregister_class(ViewSynthesisPanelSettings)
        del bpy.types.Scene.view_synthesis_panel_settings
        bpy.utils.unregister_class(RunViewSynthesisOperator)

    def draw(self, context):
        """Draw the panel with corrresponding properties and operators."""
        settings = context.scene.view_synthesis_panel_settings
        layout = self.layout
        view_synthesis_box = layout.box()

        row = view_synthesis_box.row()
        row.operator(RunViewSynthesisOperator.bl_idname)
        row = view_synthesis_box.row()
        row.prop(settings, "execution_environment", text="Script Environment")
        if settings.execution_environment == "CONDA":
            row = view_synthesis_box.row()
            row.prop(
                settings, "conda_exe_fp", text="Conda Executable File Path"
            )
            row = view_synthesis_box.row()
            row.prop(settings, "conda_env_name", text="Conda Environment Name")
        elif settings.execution_environment == "DEFAULT PYTHON":
            row = view_synthesis_box.row()
            row.prop(
                settings,
                "python_exe_fp",
                text="Default Python Executable Name or File Path",
            )
        else:
            pass

        row = view_synthesis_box.row()
        row.prop(
            settings,
            "additional_system_dps",
            text="Additional System Paths",
        )
        row = view_synthesis_box.row()
        row.prop(
            settings,
            "view_synthesis_executable_fp",
            text="Script",
        )
        row = view_synthesis_box.row()
        row.prop(
            settings,
            "view_synthesis_snapshot_fp",
            text="Training Snapshot (Trained Model)",
        )
        row = view_synthesis_box.row()
        row.prop(settings, "samples_per_pixel", text="Samples Per Pixel")
