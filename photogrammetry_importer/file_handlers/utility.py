import numpy as np
from photogrammetry_importer.blender_utility.logging_utility import log_report


def check_radial_distortion(radial_distortion, camera_name, op=None):
    """Check if the radial distortion is compatible with Blender."""

    # TODO: Integrate lens distortion nodes
    # https://docs.blender.org/manual/en/latest/compositing/types/distort/lens_distortion.html
    # to properly support radial distortion represented with a single parameter

    if radial_distortion is None:
        return
    if np.array_equal(
        np.asarray(radial_distortion), np.zeros_like(radial_distortion)
    ):
        return

    output = "Blender does not support radial distortion of cameras in the"
    output += f" 3D View. Distortion of camera {camera_name}:"
    output += " {radial_distortion}. If possible, re-compute the "
    output += "reconstruction using a camera model without radial distortion"
    output += ' parameters.  Use "Suppress Distortion Warnings" in the'
    output += " import settings to suppress this message."
    log_report("WARNING", output, op)
