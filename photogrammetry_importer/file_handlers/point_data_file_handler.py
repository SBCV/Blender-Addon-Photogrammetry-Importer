import os
from photogrammetry_importer.types.point import Point
from photogrammetry_importer.file_handlers.ply_file_handler import (
    PLYFileHandler,
)
from photogrammetry_importer.utility.blender_logging_utility import log_report
from photogrammetry_importer.utility.type_utility import is_float, is_int


class DataSemantics(object):
    def __init__(self):
        self.x_idx = None
        self.y_idx = None
        self.z_idx = None
        self.r_idx = None
        self.g_idx = None
        self.b_idx = None
        self.pseudo_color = None

    def is_color_initialized(self):
        return not None in [self.r_idx, self.g_idx, self.b_idx]


class PointDataFileHandler(object):
    @staticmethod
    def read_lines_as_tuples(ifc, delimiter):
        lines_as_tup = []
        for line in ifc.readlines():
            elements = line.split(delimiter)
            lines_as_tup.append(elements)
        return lines_as_tup

    @staticmethod
    def guess_data_semantics(data_tuple):
        log_report("INFO", "Guessing data semantics")
        data_semantics = DataSemantics()
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
            if not 0 <= int(data_tuple[idx]) <= 255:
                continue
            if not 0 <= int(data_tuple[idx]) <= 255:
                continue
            data_semantics.r_idx = idx
            data_semantics.g_idx = idx + 1
            data_semantics.b_idx = idx + 2
            data_semantics.pseudo_color = False
            break

        if data_semantics.is_color_initialized():
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

        return data_semantics

    @staticmethod
    def parse_header(line):
        data_semantics = DataSemantics()
        data_tuple = line.lstrip("//").rstrip().split(" ")

        for idx, val in enumerate(data_tuple):
            if val == "X":
                data_semantics.x_idx = idx
            elif val == "Y":
                data_semantics.y_idx = idx
            elif val == "Z":
                data_semantics.z_idx = idx
            elif val == "R":
                data_semantics.r_idx = idx
                data_semantics.pseudo_color = False
            elif val == "G":
                data_semantics.g_idx = idx
                data_semantics.pseudo_color = False
            elif val == "B":
                data_semantics.b_idx = idx
                data_semantics.pseudo_color = False
            elif val == "Rf":
                data_semantics.r_idx = idx
                data_semantics.pseudo_color = True
            elif val == "Gf":
                data_semantics.g_idx = idx
                data_semantics.pseudo_color = True
            elif val == "Bf":
                data_semantics.b_idx = idx
                data_semantics.pseudo_color = True

        return data_semantics

    @staticmethod
    def parse_asc_or_pts_or_csv(ifp, delimiter, only_data):

        points = []
        with open(ifp, "r") as ifc:

            data_semantics = None
            if not only_data:
                line = ifc.readline()
                if line.startswith("//"):
                    data_semantics = PointDataFileHandler.parse_header(line)
                    line = ifc.readline()
                    num_points = int(line.strip())
                else:
                    num_points = int(line.strip())

            lines_as_tuples = PointDataFileHandler.read_lines_as_tuples(
                ifc, delimiter=delimiter
            )

            if data_semantics is None:
                # Determine the semantics of the data
                data_tuple = lines_as_tuples[0]
                data_semantics = PointDataFileHandler.guess_data_semantics(
                    data_tuple
                )

            if data_semantics.pseudo_color:
                factor = 255
            else:
                factor = 1

            for idx, data_tuple in enumerate(lines_as_tuples):
                point = Point(
                    coord=[
                        float(data_tuple[data_semantics.x_idx]),
                        float(data_tuple[data_semantics.y_idx]),
                        float(data_tuple[data_semantics.z_idx]),
                    ],
                    color=[
                        int(factor * float(data_tuple[data_semantics.r_idx])),
                        int(factor * float(data_tuple[data_semantics.g_idx])),
                        int(factor * float(data_tuple[data_semantics.b_idx])),
                    ],
                    id=idx,
                    scalars=None,
                )
                points.append(point)

        return points

    @staticmethod
    def parse_point_data_file(ifp):
        log_report("INFO", "Parse Point Data File: ...")

        ext = os.path.splitext(ifp)[1].lower()
        if ext == ".ply":
            points = PLYFileHandler.parse_ply_file(ifp)
        elif ext == ".csv":
            points = PointDataFileHandler.parse_asc_or_pts_or_csv(
                ifp, delimiter=",", only_data=True
            )
        elif ext in [".asc", ".pts"]:
            # https://www.cloudcompare.org/doc/wiki/index.php?title=FILE_I/O
            points = PointDataFileHandler.parse_asc_or_pts_or_csv(
                ifp, delimiter=" ", only_data=False
            )
        else:
            log_report("ERROR", "Extension " + ext + " not supported.", self)
            assert False

        log_report("INFO", "Parse Point Data File: Done")
        return points
