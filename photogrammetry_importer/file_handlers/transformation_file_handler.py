import os
import numpy as np
from photogrammetry_importer.blender_utility.logging_utility import log_report


class TransformationFileHandler:
    """Class to read directories with files storing transformations."""

    @staticmethod
    def parse_transformation_folder(t_idp, op=None):
        """Parse a directory with files storing transformations."""

        if not os.path.isdir(t_idp):
            return []

        t_fps = sorted(
            [
                os.path.join(t_idp, fn)
                for fn in os.listdir(t_idp)
                if os.path.isfile(os.path.join(t_idp, fn))
                and os.path.splitext(fn)[1] == ".txt"
            ]
        )

        transformations_sorted = []
        for t_fp in t_fps:
            log_report("INFO", "transformation file path: " + t_fp, op)
            trans_mat = np.loadtxt(t_fp, dtype="f", delimiter=" ")
            # log_report('INFO', 'transformation mat: ' + str(trans_mat), op)
            transformations_sorted.append(trans_mat)

        return transformations_sorted
