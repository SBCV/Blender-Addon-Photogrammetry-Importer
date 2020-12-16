import subprocess
import importlib
from collections import defaultdict
import bpy
from photogrammetry_importer.utility.blender_logging_utility import log_report


class OptionalDependency:
    """Class that describes an optional Python dependency of the addon."""

    def __init__(self, gui_name, package_name, import_name):
        # Name shown in the GUI.
        self.gui_name = gui_name
        # Package name such as "pillow" in "pip install pillow".
        self.package_name = package_name
        # Import name such as "PIL" in "import PIL".
        self.import_name = import_name

        self.installation_status = False
        self._determine_installation_status()

    def _determine_installation_status(self):
        """Determine wether this dependency is installed or not.

        Once a module is loaded into the current Python session, importlib can
        not longer be used to determine the installation status. Restart
        Blender to clear the current Python session.
        """
        if self.installation_status:
            assert False
        module_spec = importlib.util.find_spec(self.import_name)
        self.installation_status = module_spec is not None

    def _install_pip(self, lazy):
        """Install pip."""
        if lazy:
            module_spec = importlib.util.find_spec("pip")
            if module_spec is not None:
                return
        try:
            subprocess.run(
                [bpy.app.binary_path_python, "-m", "pip", "--version"],
                check=True,
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

    def install(self):
        """Install this dependency."""
        self._install_pip(lazy=True)

        # The "--user" option does not work with Blender's Python version.
        install_command = [
            bpy.app.binary_path_python,
            "-m",
            "pip",
            "install",
            self.package_name,
        ]
        subprocess.run(install_command, check=False)
        try:
            importlib.import_module(self.import_name)
            self.installation_status = True
        except:
            self.installation_status = False

    def uninstall(self):
        """Uninstall this dependency."""
        self._install_pip(lazy=True)

        uninstall_command = [
            bpy.app.binary_path_python,
            "-m",
            "pip",
            "uninstall",
            "-y",
            self.package_name,
        ]
        # Although "pip uninstall" may throw an error while uninstalling pillow
        # and lazrs it still removes the corresponding packages.
        subprocess.run(uninstall_command, check=False)
        self.installation_status = False

    def _get_version_string(self):
        module_spec = importlib.util.find_spec("pkg_resources")
        if module_spec is not None:
            import pkg_resources

            version_str = pkg_resources.get_distribution(
                self.package_name
            ).version
        else:
            version_str = "Unknown"
        return version_str

    def get_installation_status(self):
        """Return the installation status of this dependency."""
        if self.installation_status:
            version_str = self._get_version_string()
            status = f"Installed (Version {version_str})"
        else:
            status = "Not installed"
        return status


class OptionalDependencyManager:
    """Class that manages the (optional) dependencies of this addon."""

    @classmethod
    def get_singleton(cls):
        """Return a singleton of this class."""
        if hasattr(bpy.types.Object, "dependency_manager"):
            dependency_manager = bpy.types.Object.dependency_manager
        else:
            dependency_manager = cls()
            bpy.types.Object.dependency_manager = dependency_manager
        return dependency_manager

    def __init__(self):
        self.dependencies = (
            OptionalDependency(
                gui_name="Pillow", package_name="pillow", import_name="PIL"
            ),
            OptionalDependency(
                gui_name="Lazrs", package_name="lazrs", import_name="lazrs"
            ),
            OptionalDependency(
                gui_name="Pylas", package_name="pylas", import_name="pylas"
            ),
            OptionalDependency(
                gui_name="Pyntcloud",
                package_name="pyntcloud",
                import_name="pyntcloud",
            ),
        )

    def install_dependencies(self):
        """Install all (optional) dependencies of this addon."""
        for dependency in self.get_dependencies():
            dependency.install()

    def uninstall_dependencies(self):
        """Uninstall all (optional) dependencies of this addon."""
        for dependency in self.get_dependencies():
            dependency.uninstall()

    def get_dependencies(self):
        """Return all (optional) dependencies of this addon."""
        return self.dependencies


class InstallOptionalDependenciesOperator(bpy.types.Operator):
    """Operator to install all (optional) dependencies of this addon."""

    bl_idname = "photogrammetry_importer.install_dependencies"
    bl_label = "Download and Install Optional Dependencies (be patient!)"
    bl_description = (
        "Download and install the optional dependencies (Python packages). "
        "Depending on the installation folder, Blender may have to be started "
        "with administrator privileges to install the packages. "
        "Start Blender from the console to see the progress."
    )
    bl_options = {"REGISTER"}

    def execute(self, context):
        """Install all optional dependencies."""
        try:
            dependency_manager = OptionalDependencyManager.get_singleton()
            dependency_manager.install_dependencies()
        except (subprocess.CalledProcessError, ImportError) as err:
            log_report("ERROR", str(err))
            return {"CANCELLED"}
        return {"FINISHED"}


class UninstallOptionalDependenciesOperator(bpy.types.Operator):
    """Operator to uninstall all (optional) dependencies of this addon."""

    bl_idname = "photogrammetry_importer.uninstall_dependencies"
    bl_label = "Uninstall Optional Dependencies"
    bl_description = (
        "Uninstall optional dependencies. Blender may have to be started with "
        "administrator privileges in order to remove the dependencies"
    )
    bl_options = {"REGISTER"}

    def execute(self, context):
        """Uninstall all optional dependencies."""
        try:
            dependency_manager = OptionalDependencyManager.get_singleton()
            dependency_manager.uninstall_dependencies()
        except (subprocess.CalledProcessError, ImportError) as err:
            log_report("ERROR", str(err))
            return {"CANCELLED"}

        return {"FINISHED"}
