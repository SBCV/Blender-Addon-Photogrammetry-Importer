import os
import sys
import subprocess
from subprocess import PIPE
import copy
import json
import importlib
from collections import defaultdict
import bpy
from bpy.app.handlers import persistent
from photogrammetry_importer.blender_utility.logging_utility import log_report
from bpy.props import StringProperty


def _get_addon_name():
    return __name__.split(".")[0]


def _get_python_exe_path():
    # https://developer.blender.org/rB6527a14cd2ceaaf529beae522ca594bb250b56c9
    try:
        # For Blender 2.80, ..., etc
        python_exe_fp = bpy.app.binary_path_python
    except AttributeError:
        # For Blender 2.92, ..., etc
        python_exe_fp = sys.executable
    return python_exe_fp


def get_additional_command_line_sys_path():
    """Function that retrieves additional sys.path of the command line"""
    script_str = "import sys; import json; pickled_str = json.dumps(sys.path); print(pickled_str)"
    result = subprocess.run(
        [_get_python_exe_path(), "-c", script_str],
        stdout=PIPE,
        stderr=PIPE,
    )
    command_line_sys_paths = json.loads(result.stdout)
    blender_sys_paths = copy.deepcopy(sys.path)

    additional_system_paths = []
    for command_line_sys_path in command_line_sys_paths:
        if command_line_sys_path not in blender_sys_paths:
            if command_line_sys_path != "":
                log_report(
                    "INFO", f"Add missing sys.path: {command_line_sys_path}"
                )
                additional_system_paths.append(command_line_sys_path)
    return additional_system_paths


def add_command_line_sys_path():
    """Function that adds sys.path of the command line to Blender's sys.path"""
    additional_system_paths = get_additional_command_line_sys_path()
    for additional_sys_path in additional_system_paths:
        sys.path.append(additional_sys_path)

    if len(additional_system_paths) > 0:
        addon_name = _get_addon_name()
        prefs = bpy.context.preferences.addons[addon_name].preferences
        prefs.sys_path_list_str = json.dumps(additional_system_paths)


def remove_command_line_sys_path():
    """Function that removes additional paths in Blender's sys.path"""
    addon_name = _get_addon_name()
    prefs = bpy.context.preferences.addons[addon_name].preferences
    additional_system_paths = json.loads(prefs.sys_path_list_str)
    for additional_sys_path in additional_system_paths:
        if additional_sys_path in sys.path:
            sys.path.remove(additional_sys_path)
    prefs.sys_path_list_str = "[]"


@persistent
def add_command_line_sys_path_if_necessary(dummy):
    """Function that extends Blender's sys.path if necessary"""

    dependency_manager = OptionalDependencyManager.get_singleton()
    dependencies = dependency_manager.get_dependencies()
    installed = any(
        dependency.installation_status for dependency in dependencies
    )
    if installed:
        log_report(
            "INFO", "Found installed dependencies. Going to adjust sys.path."
        )
        add_command_line_sys_path()
    else:
        log_report(
            "INFO",
            "Found no installed dependencies. Not going to adjust sys.path.",
        )


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
        assert not self.installation_status
        module_spec = importlib.util.find_spec(self.import_name)
        self.installation_status = module_spec is not None

    def get_package_info(self):
        try:
            # This does NOT immediately work after installation from Blender's
            # python using a subprocess. A restart is required to import
            # "pkg_resources" properly.
            import pkg_resources

            # https://github.com/pypa/setuptools/blob/9f1822ee910df3df930a98ab99f66d18bb70659b/pkg_resources/__init__.py#L2574
            dist_info_distribution = pkg_resources.get_distribution(
                self.package_name
            )
            version_str = dist_info_distribution.version
            location_str = os.path.join(
                dist_info_distribution.location,
                dist_info_distribution.project_name,
            )
        except Exception as e:
            version_str = None
            location_str = None
        return version_str, location_str


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
            if lazy and self.pip_dependency_status.installation_status:
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

    def get_package_info(self):
        """Return the pip installation status."""
        return self.pip_dependency_status.get_package_info()


class OptionalDependency(DependencyStatus):
    """Class that describes an optional Python dependency of the addon."""

    def install(self, op=None):
        """Install this dependency."""
        pip_manager = PipManager.get_singleton()
        pip_manager.install_pip(lazy=True, op=op)
        add_command_line_sys_path()
        # https://pip.pypa.io/en/latest/cli/pip_install/#install-user
        # The "--user" option does not work with Blender's Python version.
        dependency_install_command = [
            _get_python_exe_path(),
            "-m",
            "pip",
            "install",
            # https://pip.pypa.io/en/latest/cli/pip/?highlight=no-cache-dir#cmdoption-isolated
            # "--isolated",
            # https://pip.pypa.io/en/latest/cli/pip/?highlight=no-cache-dir#cmdoption-no-cache-dir
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
        except ImportError as import_error:
            self.installation_status = False
            log_report(
                "ERROR", "===========================================", op
            )
            log_report(
                "ERROR",
                f"INSTALLATION of DEPENDENCY {self.import_name} FAILED!",
                op,
            )
            log_report("ERROR", f"Reason: {import_error}", op)
            log_report(
                "ERROR", "===========================================", op
            )

    def uninstall(self, remove_sys_path=True, op=None):
        """Uninstall this dependency."""
        pip_manager = PipManager.get_singleton()
        pip_manager.install_pip(lazy=True, op=op)
        dependency_uninstall_command = [
            _get_python_exe_path(),
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
        if remove_sys_path:
            remove_command_line_sys_path()
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
                gui_name="Setuptools",
                package_name="setuptools",
                import_name="setuptools",
            ),
            OptionalDependency(
                gui_name="Pillow", package_name="pillow", import_name="PIL"
            ),
            OptionalDependency(
                gui_name="Lazrs", package_name="lazrs", import_name="lazrs"
            ),
            OptionalDependency(
                gui_name="Laspy", package_name="laspy", import_name="laspy"
            ),
            OptionalDependency(
                gui_name="Pyntcloud",
                package_name="pyntcloud",
                import_name="pyntcloud",
            ),
        )

    def install_dependencies(self, dependency_package_name="", op=None):
        """Install all (optional) dependencies of this addon."""
        for dependency in self.get_dependencies():
            install = False
            if dependency_package_name == "":
                install = True
            elif dependency.package_name == dependency_package_name:
                install = True
            if install:
                dependency.install(op=op)

    def uninstall_dependencies(self, dependency_package_name="", op=None):
        """Uninstall all (optional) dependencies of this addon."""
        for dependency in self.get_dependencies():
            uninstall = False
            if dependency_package_name == "":
                uninstall = True
            elif dependency.package_name == dependency_package_name:
                uninstall = True
            if uninstall:
                dependency.uninstall(remove_sys_path=False, op=op)
        some_dependencies_installed = any(
            [
                dependency.installation_status
                for dependency in self.get_dependencies()
            ]
        )
        if not some_dependencies_installed:
            remove_command_line_sys_path()

    def get_dependencies(self):
        """Return all (optional) dependencies of this addon."""
        return self.dependencies


class InstallOptionalDependenciesOperator(bpy.types.Operator):
    """Operator to install all (optional) dependencies of this addon."""

    bl_idname = "photogrammetry_importer.install_dependencies"
    bl_label = "Download and Install ALL Optional Dependencies (be patient!)"
    bl_description = (
        "Download and install the optional dependencies (Python packages). "
        "Depending on the installation folder, Blender may have to be started "
        "with administrator privileges to install the packages. "
        "Start Blender from the console to see the progress."
    )
    bl_options = {"REGISTER"}
    dependency_package_name: StringProperty(
        name="Dependency Package Name",
        description="Target dependency package to be installed.",
        default="",
    )

    def execute(self, context):
        """Install all optional dependencies."""
        try:
            dependency_manager = OptionalDependencyManager.get_singleton()
            dependency_manager.install_dependencies(
                dependency_package_name=self.dependency_package_name, op=self
            )
        except (subprocess.CalledProcessError, ImportError) as err:
            log_report("ERROR", str(err))
            return {"CANCELLED"}
        return {"FINISHED"}


class UninstallOptionalDependenciesOperator(bpy.types.Operator):
    """Operator to uninstall all (optional) dependencies of this addon."""

    bl_idname = "photogrammetry_importer.uninstall_dependencies"
    bl_label = "Remove ALL Optional Dependencies"
    bl_description = (
        "Uninstall optional dependencies. Blender may have to be started with "
        "administrator privileges in order to remove the dependencies"
    )
    bl_options = {"REGISTER"}
    dependency_package_name: StringProperty(
        name="Dependency Package Name",
        description="Target dependency package to be removed.",
        default="",
    )

    def execute(self, context):
        """Uninstall all optional dependencies."""
        try:
            dependency_manager = OptionalDependencyManager.get_singleton()
            dependency_manager.uninstall_dependencies(
                dependency_package_name=self.dependency_package_name, op=self
            )
        except (subprocess.CalledProcessError, ImportError) as err:
            log_report("ERROR", str(err))
            return {"CANCELLED"}

        return {"FINISHED"}
