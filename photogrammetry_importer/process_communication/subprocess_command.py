import os
from sys import platform


def create_subprocess_command(
    script_fp,
    parameter_list=None,
    python_exe_fp=None,
    conda_exe_fp=None,
    conda_env_name=None,
):
    """Create a command to execute a script with a Python subprocess."""
    assert os.path.isfile(script_fp)
    if parameter_list is None:
        parameter_list = []

    if python_exe_fp is None and conda_exe_fp is None:
        if platform == "linux":
            # python_exe_fp = "/usr/bin/python3"
            python_exe_fp = None
            conda_exe_fp = "conda"
        elif platform == "win32":
            # python_exe_fp = "python.exe"
            # python_exe_fp = r"C:\Users\<user>\miniconda3\python.exe"
            # conda_exe_fp = r"C:\Users\<user>\miniconda3\condabin\conda.bat"
            python_exe_fp = None
            conda_exe_fp = "conda.bat"

    assert python_exe_fp is None or conda_exe_fp is None

    if python_exe_fp is not None:
        command = [python_exe_fp]
    if conda_exe_fp is not None:
        if conda_env_name is None:
            conda_env_name = "base"
        command = [
            conda_exe_fp,
            "run",
            # https://github.com/conda/conda/issues/9412
            "--no-capture-output",
            "-n",
            conda_env_name,
            "python",
        ]

    command += [script_fp]
    command += parameter_list
    return command
