import sys
import subprocess
import importlib
from collections import defaultdict
import bpy
from photogrammetry_importer.blender_utility.logging_utility import log_report


class DependencyStatus:
    """Class that describes the installation status of a Python dependency."""

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

    def _get_version_string(self, package_name):
        try:
            import pkg_resources

            version_str = pkg_resources.get_distribution(package_name).version
        except:
            version_str = "Unknown"
        return version_str

    def get_installation_status(self):
        """Return the installation status of this dependency."""
        if self.installation_status:
            version_str = self._get_version_string(self.package_name)
            status = f"Installed (Version {version_str})"
        else:
            status = "Not installed"
        return status


class PipManager:
    """Class that manages the pip installation."""

    def __init__(self):
        self.pip_dependency_status = DependencyStatus(
            gui_name="Pip", package_name="pip", import_name="pip"
        )

    @classmethod
    def get_singleton(cls):
        """Return a singleton of this class."""
        if hasattr(bpy.types.Object, "photogrammetry_pip_manager"):
            pip_manager = bpy.types.Object.photogrammetry_pip_manager
        else:
            pip_manager = cls()
            bpy.types.Object.photogrammetry_pip_manager = pip_manager
        return pip_manager

    def install_pip(self, lazy, op=None):
        """Install pip."""
        try:
            if lazy and self.pip_dependency_status.get_installation_status():
                import pip
                log_report(
                    "INFO",
                    "Pip already installed. Using existing pip installation"
                    + f" ({pip.__version__})",
                    op=op,
                )
                return
        except:
            pass

        log_report("INFO", "Installing pip!", op=op)

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
        self.pip_dependency_status.installation_status = True

    def get_installation_status(self):
        """Return the pip installation status."""
        return self.pip_dependency_status.get_installation_status()


class OptionalDependency(DependencyStatus):
    """Class that describes an optional Python dependency of the addon."""

    def _get_python_exe_path(self):
        # https://developer.blender.org/rB6527a14cd2ceaaf529beae522ca594bb250b56c9
        try:
            # For Blender 2.80, ..., etc
            python_exe_fp = bpy.app.binary_path_python
        except AttributeError:
            # For Blender 2.92, ..., etc
            python_exe_fp = sys.executable
        return python_exe_fp

    def install(self, op=None):
        """Install this dependency."""
        pip_manager = PipManager.get_singleton()
        pip_manager.install_pip(lazy=True, op=op)
        # The "--user" option does not work with Blender's Python version.
        dependency_install_command = [
            self._get_python_exe_path(),
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            self.package_name,
        ]
        log_report(
            "INFO",
            f"Installing dependency with {dependency_install_command}",
            op,
        )
        subprocess.run(dependency_install_command, check=False)
        try:
            importlib.import_module(self.import_name)
            self.installation_status = True
        except:
            self.installation_status = False

    def uninstall(self, op=None):
        """Uninstall this dependency."""
        pip_manager = PipManager.get_singleton()
        pip_manager.install_pip(lazy=True, op=op)
        dependency_uninstall_command = [
            self._get_python_exe_path(),
            "-m",
            "pip",
            "uninstall",
            "-y",
            self.package_name,
        ]
        log_report(
            "INFO",
            f"Uninstalling dependency with {dependency_uninstall_command}",
            op,
        )
        # Although "pip uninstall" may throw an error while uninstalling pillow
        # and lazrs it still removes the corresponding packages.
        subprocess.run(dependency_uninstall_command, check=False)
        self.installation_status = False


class OptionalDependencyManager:
    """Class that manages the (optional) dependencies of this addon."""

    @classmethod
    def get_singleton(cls):
        """Return a singleton of this class."""
        if hasattr(bpy.types.Object, "photogrammetry_dependency_manager"):
            dependency_manager = (
                bpy.types.Object.photogrammetry_dependency_manager
            )
        else:
            dependency_manager = cls()
            bpy.types.Object.photogrammetry_dependency_manager = (
                dependency_manager
            )
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

    def install_dependencies(self, op=None):
        """Install all (optional) dependencies of this addon."""
        for dependency in self.get_dependencies():
            dependency.install(op=op)

    def uninstall_dependencies(self, op=None):
        """Uninstall all (optional) dependencies of this addon."""
        for dependency in self.get_dependencies():
            dependency.uninstall(op=op)

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
            dependency_manager.install_dependencies(op=self)
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
            dependency_manager.uninstall_dependencies(op=self)
        except (subprocess.CalledProcessError, ImportError) as err:
            log_report("ERROR", str(err))
            return {"CANCELLED"}

        return {"FINISHED"}
