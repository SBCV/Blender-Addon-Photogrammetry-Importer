import sys
import subprocess
import os
import numpy as np
import bpy
from tempfile import NamedTemporaryFile


from photogrammetry_importer.blender_utility.retrieval_utility import (
    get_selected_camera,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report
from photogrammetry_importer.importers.camera_utility import (
    load_background_image,
    get_computer_vision_camera,
)
from photogrammetry_importer.file_handlers.instant_ngp_file_handler import (
    InstantNGPFileHandler,
)
from photogrammetry_importer.process_communication.subprocess_command import (
    create_subprocess_command,
)
from photogrammetry_importer.process_communication.file_communication import (
    read_np_array_from_file,
)


class RunViewSynthesisOperator(bpy.types.Operator):  # ImportHelper
    """An Operator to save a rendering of the point cloud as Blender image."""

    bl_idname = "photogrammetry_importer.run_view_synthesis"
    bl_label = "Run View Synthesis for Current Camera"
    bl_description = "Export camera properties to Instant-NGP json."

    @classmethod
    def poll(cls, context):
        """Return the availability status of the operator."""
        cam = get_selected_camera()
        return cam is not None

    def execute(self, context):
        """Compute a view synthesis for the current camera."""

        log_report(
            "INFO", "Compute view synthesis for current camera: ...", self
        )
        scene = context.scene

        if sys.platform == "linux":
            temp_json_file = NamedTemporaryFile()
            temp_array_file = NamedTemporaryFile()
        elif sys.platform == "win32":
            temp_json_file = NamedTemporaryFile(delete=False)
            temp_array_file = NamedTemporaryFile(delete=False)
            # Required for windows (https://docs.python.org/3.9/library/tempfile.html)
            #  Whether the name can be used to open the file a second time, while the named temporary file is still open,
            #  varies across platforms (it can be so used on Unix; it cannot on Windows)
            temp_json_file.close()
            temp_array_file.close()
        else:
            assert False

        camera_obj = get_selected_camera()
        camera = get_computer_vision_camera(camera_obj, camera_obj.name)

        # Call before executing the child process
        InstantNGPFileHandler.write_instant_ngp_file(
            temp_json_file.name, [camera]
        )

        if (
            scene.view_synthesis_panel_settings.execution_environment
            == "CONDA"
        ):
            conda_exe_fp = scene.view_synthesis_panel_settings.conda_exe_fp
            conda_env_name = scene.view_synthesis_panel_settings.conda_env_name
            python_exe_fp = None
        elif (
            scene.view_synthesis_panel_settings.execution_environment
            == "DEFAULT PYTHON"
        ):
            python_exe_fp = scene.view_synthesis_panel_settings.python_exe_fp
            conda_exe_fp = None
            conda_env_name = None

        view_synthesis_exe_or_script_fp = (
            scene.view_synthesis_panel_settings.view_synthesis_executable_fp
        )
        view_synthesis_snapshot_fp = (
            scene.view_synthesis_panel_settings.view_synthesis_snapshot_fp
        )
        additional_system_dps = (
            scene.view_synthesis_panel_settings.additional_system_dps
        )
        samples_per_pixel = (
            scene.view_synthesis_panel_settings.samples_per_pixel
        )

        parameter_list = ["--load_snapshot", view_synthesis_snapshot_fp]
        parameter_list += ["--temp_json_ifp", temp_json_file.name]
        parameter_list += ["--temp_array_ofp", temp_array_file.name]
        parameter_list += ["--samples_per_pixel", str(samples_per_pixel)]
        if additional_system_dps.strip() != "":
            parameter_list += [
                "--additional_system_dps",
                additional_system_dps,
            ]

        assert os.path.isfile(view_synthesis_exe_or_script_fp)
        assert os.path.isfile(temp_json_file.name)
        assert os.path.isfile(temp_array_file.name)

        command = create_subprocess_command(
            view_synthesis_exe_or_script_fp,
            parameter_list,
            python_exe_fp=python_exe_fp,
            conda_exe_fp=conda_exe_fp,
            conda_env_name=conda_env_name,
        )
        cmd_call = " ".join(command)
        log_report("INFO", cmd_call, self)

        child_process = subprocess.Popen(command)
        child_process.communicate()

        # Call after executing the child process
        img_np_array = read_np_array_from_file(
            temp_array_file.name, use_pickle=False
        )

        blender_image = bpy.data.images.new(
            "view_synthesis_result",
            width=img_np_array.shape[1],
            height=img_np_array.shape[0],
        )
        img_np_array_flipped = np.flipud(img_np_array)
        blender_image.pixels = img_np_array_flipped.ravel()
        load_background_image(blender_image, camera_obj.name)

        if sys.platform == "win32":
            # Required for windows (https://docs.python.org/3.9/library/tempfile.html)
            temp_json_file.close()
            temp_array_file.close()
            os.unlink(temp_json_file.name)
            os.unlink(temp_array_file.name)

        log_report(
            "INFO", "Compute view synthesis for current camera: Done", self
        )
        return {"FINISHED"}
