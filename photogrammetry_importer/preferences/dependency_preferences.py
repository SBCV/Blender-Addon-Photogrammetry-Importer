import subprocess
import importlib
import pkg_resources
from collections import defaultdict
import bpy
from photogrammetry_importer.utility.blender_logging_utility import log_report


class Dependency:
    def __init__(self, gui_name, package_name, import_name):
        # Name shown in GUI
        self.gui_name = gui_name
        # Package name such as "pillow" in "pip install pillow"
        self.package_name = package_name
        # Import name such as "PIL" in "import PIL"
        self.import_name = import_name


dependencies = (
    Dependency(gui_name="Pillow", package_name="pillow", import_name="PIL"),
    Dependency(
        gui_name="Pyntcloud", package_name="pyntcloud", import_name="pyntcloud"
    ),
)

dependency_status_initialized = False
dependency_status = defaultdict(bool)


def install_pip():
    try:
        subprocess.run(
            [bpy.app.binary_path_python, "-m", "pip", "--version"], check=True
        )
    except subprocess.CalledProcessError:
        import os
        import ensurepip

        # https://github.com/robertguetzkow/blender-python-examples/blob/master/add-ons/install-dependencies/install-dependencies.py
        # Note that ensurepip.bootstrap() calls pip, which adds the
        # environment variable PIP_REQ_TRACKER. After ensurepip.bootstrap()
        # finishes execution, the directory is deleted.
        # However, any subprocesses calling pip will use the environment
        # variable PIP_REQ_TRACKER (which points to an invalid path).
        # Thus, we need to remove the invalid environment variable.
        ensurepip.bootstrap()
        os.environ.pop("PIP_REQ_TRACKER", None)


def install_package(package_name):
    # TODO "--user"
    install_command = [
        bpy.app.binary_path_python,
        "-m",
        "pip",
        "install",
        package_name,
    ]
    subprocess.run(install_command, check=True)


def uninstall_package(package_name):
    uninstall_command = [
        bpy.app.binary_path_python,
        "-m",
        "pip",
        "uninstall",
        "-y",
        package_name,
    ]
    subprocess.run(uninstall_command, check=True)


def add_module(import_name):
    global dependency_status
    try:
        importlib.import_module(import_name)
        dependency_status[import_name] = True
    except:
        pass


def delete_module(import_name):
    global dependency_status
    del dependency_status[import_name]


def get_dependencies():
    initialize_dependency_status()
    return dependencies


def initialize_dependency_status():
    global dependency_status
    global dependency_status_initialized
    if not dependency_status_initialized:
        for dependency in dependencies:
            import_name = dependency.import_name
            module_spec = importlib.util.find_spec(import_name)
            if module_spec is not None:
                dependency_status[import_name] = True
        dependency_status_initialized = True


def get_module_status_description(dependency):
    global dependency_status
    if dependency_status[dependency.import_name]:
        version_str = get_version_string(dependency.package_name)
        status = f"Installed (Version {version_str})"
    else:
        status = "Not installed"
    return status


def get_version_string(package_name):
    return pkg_resources.get_distribution(package_name).version


class InstallOptionalDependencies(bpy.types.Operator):
    bl_idname = "photogrammetry_importer.install_dependencies"
    bl_label = "Install Optional Dependencies"
    bl_description = (
        "Download and install the optional dependencies (python packages) of "
        "this addon. Depending on the installation location Blender may have "
        "to be started with administrator privileges to install the packages"
    )
    bl_options = {"REGISTER"}

    @classmethod
    def poll(self, context):
        return True

    def execute(self, context):
        try:
            install_pip()
            for dependency in dependencies:
                install_package(dependency.package_name)
                add_module(dependency.import_name)
        except (subprocess.CalledProcessError, ImportError) as err:
            log_report("ERROR", str(err))
            return {"CANCELLED"}
        return {"FINISHED"}


class UninstallOptionalDependencies(bpy.types.Operator):
    bl_idname = "photogrammetry_importer.uninstall_dependencies"
    bl_label = "Uninstall Optional Dependencies"
    bl_description = (
        "Uninstall optional dependencies. Blender may have to be started with "
        "administrator privileges in order to remove the dependencies"
    )
    bl_options = {"REGISTER"}

    @classmethod
    def poll(self, context):
        return True

    def execute(self, context):
        try:
            install_pip()
            for dependency in dependencies:
                uninstall_package(dependency.package_name)
                delete_module(dependency.import_name)
        except (subprocess.CalledProcessError, ImportError) as err:
            log_report("ERROR", str(err))
            return {"CANCELLED"}

        return {"FINISHED"}
