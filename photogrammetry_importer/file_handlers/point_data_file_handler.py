import os
import numpy as np
import importlib

from photogrammetry_importer.types.point import Point
from photogrammetry_importer.blender_utility.logging_utility import log_report
from photogrammetry_importer.utility.type_utility import is_float, is_int


class _DataSemantics:
    def __init__(self):
        self.x_idx = None
        self.y_idx = None
        self.z_idx = None
        self.r_idx = None
        self.g_idx = None
        self.b_idx = None
        self.num_data_entries = None
        self.pseudo_color = None

    def is_initialized(self):
        return not None in [
            self.x_idx,
            self.y_idx,
            self.z_idx,
            self.r_idx,
            self.g_idx,
            self.b_idx,
            self.num_data_entries,
            self.pseudo_color,
        ]


class PointDataFileHandler:
    """Class to read and write common point data files."""

    @staticmethod
    def _read_lines_as_tuples(ifc, delimiter):
        lines_as_tup = []
        for line in ifc.readlines():
            elements = line.split(delimiter)
            lines_as_tup.append(elements)
        return lines_as_tup

    @staticmethod
    def _guess_data_semantics_from_tuple(data_tuple, op):
        data_semantics = _DataSemantics()
        data_semantics.num_data_entries = len(data_tuple)
        # Data must start with subsequent float values
        # representing the three-dimensional position
        for idx in [0, 1, 2]:
            assert is_float(data_tuple[idx])
        data_semantics.x_idx = 0
        data_semantics.y_idx = 1
        data_semantics.z_idx = 2

        num_data_entries = len(data_tuple)

        # Search for three subsequent int values between 0 and 255
        # (which indicate RGB color information)
        for idx in [3, num_data_entries - 3]:
            if not is_int(data_tuple[idx]):
                continue
            if not is_int(data_tuple[idx + 1]):
                continue
            if not is_int(data_tuple[idx + 2]):
                continue
            if not 0 <= int(data_tuple[idx]) <= 255:
                continue
            if not 0 <= int(data_tuple[idx + 1]) <= 255:
                continue
            if not 0 <= int(data_tuple[idx + 2]) <= 255:
                continue
            data_semantics.r_idx = idx
            data_semantics.g_idx = idx + 1
            data_semantics.b_idx = idx + 2
            data_semantics.pseudo_color = False
            break

        if data_semantics.is_initialized():
            return data_semantics

        # If not int values are found, we assume that the color information
        # is stored as pseudo colors, i.e. we are looking for 3 subsequent
        # floats between (0,1).
        for idx in [3, num_data_entries - 3]:
            assert is_float(data_tuple[idx])
            if not 0 <= float(data_tuple[idx]) <= 1:
                continue
            if not 0 <= float(data_tuple[idx + 1]) <= 1:
                continue
            if not 0 <= float(data_tuple[idx + 2]) <= 1:
                continue
            data_semantics.r_idx = idx
            data_semantics.g_idx = idx + 1
            data_semantics.b_idx = idx + 2
            data_semantics.pseudo_color = True
            break
        if not data_semantics.is_initialized():
            msg = "Could not guess data semantics from tuple."
            msg += " Consider to add a header to your input file to define position, colors, etc. \n"
            msg += "For example: \n"
            msg += "//X Y Z Rf Gf Bf Intensity\n"
            msg += "or: \n"
            msg += "//X Y Z R G B Intensity"
            log_report("ERROR", msg, op)
            assert False
        return data_semantics

    @staticmethod
    def _get_data_semantics_from_header(line):
        data_semantics = _DataSemantics()
        data_tuple = line.lstrip("//").rstrip().split(" ")
        data_semantics.num_data_entries = len(data_tuple)

        for idx, val in enumerate(data_tuple):
            val = val.lower()
            if val == "x":
                data_semantics.x_idx = idx
            elif val == "y":
                data_semantics.y_idx = idx
            elif val == "z":
                data_semantics.z_idx = idx
            elif val in ["r", "red"]:
                data_semantics.r_idx = idx
                data_semantics.pseudo_color = False
            elif val in ["g", "green"]:
                data_semantics.g_idx = idx
                data_semantics.pseudo_color = False
            elif val in ["b", "blue"]:
                data_semantics.b_idx = idx
                data_semantics.pseudo_color = False
            elif val == "rf":
                data_semantics.r_idx = idx
                data_semantics.pseudo_color = True
            elif val == "gf":
                data_semantics.g_idx = idx
                data_semantics.pseudo_color = True
            elif val == "bf":
                data_semantics.b_idx = idx
                data_semantics.pseudo_color = True
        assert data_semantics.is_initialized()
        return data_semantics

    @staticmethod
    def _get_data_semantics_from_ascii(ifp, delimiter, has_header, op=None):
        with open(ifp, "r") as ifc:
            data_semantics = None
            if has_header:
                line = ifc.readline()
                if line.startswith("//"):
                    log_report(
                        "INFO", "Reading data semantics from header", op
                    )
                    data_semantics = (
                        PointDataFileHandler._get_data_semantics_from_header(
                            line
                        )
                    )
                    line = ifc.readline()

            if data_semantics is None:
                log_report(
                    "INFO", "No header available, guessing data semantics", op
                )
                lines_as_tuples = PointDataFileHandler._read_lines_as_tuples(
                    ifc, delimiter=delimiter
                )
                data_semantics = (
                    PointDataFileHandler._guess_data_semantics_from_tuple(
                        lines_as_tuples[0], op
                    )
                )
            return data_semantics

    @staticmethod
    def _convert_data_semantics_to_list(data_semantics):

        named_list = [
            "s" + str(idx) for idx in range(data_semantics.num_data_entries)
        ]
        named_list[data_semantics.x_idx] = "x"
        named_list[data_semantics.y_idx] = "y"
        named_list[data_semantics.z_idx] = "z"
        named_list[data_semantics.r_idx] = "red"
        named_list[data_semantics.g_idx] = "green"
        named_list[data_semantics.b_idx] = "blue"
        return named_list

    @staticmethod
    def parse_point_data_file(ifp, op=None):
        """Parse a point data file.

        Supported file formats are: :code:`.ply`, :code:`.pcd`, :code:`.las`,
        :code:`.laz`, :code:`.asc`, :code:`.pts` and :code:`.csv`.

        Relies on the :code:`pyntcloud`, the :code:`laspy` and/or the
        :code:`lazrs` library to parse the different file formats.
        """

        log_report("INFO", "Parse Point Data File: ...", op)
        # https://pyntcloud.readthedocs.io/en/latest/io.html
        # https://www.cloudcompare.org/doc/wiki/index.php?title=FILE_I/O
        module_spec = importlib.util.find_spec("pyntcloud")
        if module_spec is None:
            log_report(
                "ERROR",
                "Importing this file type requires the pyntcloud library.",
                op,
            )
            assert False
        from pyntcloud import PyntCloud

        assert os.path.isfile(ifp)
        ext = os.path.splitext(ifp)[1].lower()
        if ext in [".asc", ".pts"]:
            sep = " "
            data_semantics = (
                PointDataFileHandler._get_data_semantics_from_ascii(
                    ifp, sep, has_header=True, op=op
                )
            )
            names = PointDataFileHandler._convert_data_semantics_to_list(
                data_semantics
            )
            point_cloud = PyntCloud.from_file(
                ifp, sep=sep, header=0, names=names
            )
            pseudo_color = data_semantics.pseudo_color
        elif ext == ".csv":
            sep = ","
            data_semantics = (
                PointDataFileHandler._get_data_semantics_from_ascii(
                    ifp, sep, has_header=False, op=op
                )
            )
            names = PointDataFileHandler._convert_data_semantics_to_list(
                data_semantics
            )
            point_cloud = PyntCloud.from_file(
                ifp, sep=sep, header=0, names=names
            )
            pseudo_color = data_semantics.pseudo_color
        else:
            pseudo_color = False
            point_cloud = PyntCloud.from_file(ifp)
        xyz_arr = point_cloud.points.loc[:, ["x", "y", "z"]].to_numpy()
        if set(["red", "green", "blue"]).issubset(point_cloud.points.columns):
            color_arr = point_cloud.points.loc[
                :, ["red", "green", "blue"]
            ].to_numpy()
            if pseudo_color:
                color_arr *= 255
        else:
            color_arr = np.ones_like(xyz_arr) * 255
        num_points = xyz_arr.shape[0]
        points = []
        for idx in range(num_points):
            point = Point(
                coord=xyz_arr[idx].astype("float64"),
                color=color_arr[idx].astype("int"),
                id=idx,
                scalars=dict(),
            )
            points.append(point)
        log_report("INFO", f"Number Points {len(points)}", op)
        log_report("INFO", "Parse Point Data File: Done", op)
        return points
