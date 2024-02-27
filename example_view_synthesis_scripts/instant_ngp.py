import sys
import argparse
import os
import commentjson as json
import numpy as np
import io
import pickle


def create_args_parser():
    parser = argparse.ArgumentParser(
        description="Run instant neural graphics primitives with additional configuration & output options"
    )

    parser.add_argument(
        "--load_snapshot",
        "--snapshot",
        default="",
        help="Load this snapshot before training. recommended extension: .ingp/.msgpack",
    )

    parser.add_argument(
        "--nerf_compatibility",
        action="store_true",
        help="Matches parameters with original NeRF. Can cause slowness and worse results on some scenes, but helps with high PSNR on synthetic scenes.",
    )
    parser.add_argument(
        "--exposure",
        default=0.0,
        type=float,
        help="Controls the brightness of the image. Positive numbers increase brightness, negative numbers decrease it.",
    )

    parser.add_argument(
        "--samples_per_pixel",
        type=int,
        default=16,
        help="Number of samples per pixel in screenshots.",
    )

    # For "import pyngp as ngp"
    parser.add_argument(
        "--additional_system_dps",
        nargs="+",
        default="",
        help="Path to the temporary json file.",
    )

    # For communication with parent process
    parser.add_argument(
        "--temp_json_ifp", default="", help="Path to the temporary json file."
    )
    parser.add_argument(
        "--temp_array_ofp",
        default="",
        help="Path to the temporary array file.",
    )

    return parser


def write_np_array_to_file(np_array, temp_ofp, use_pickle):
    """Copy of photogrammetry_importer.file_communication.write_np_array_to_file"""
    serialized_np_array = serialize_numpy_array(
        np_array, use_pickle=use_pickle
    )
    with open(temp_ofp, "wb") as f:
        f.write(serialized_np_array)


def serialize_numpy_array(np_array, use_pickle=False):
    """Copy of photogrammetry_importer.serialization.serialize_numpy_array"""
    if use_pickle:
        serialized_np_array = pickle.dumps(np_array)
    else:
        memory_file = io.BytesIO()
        np.save(memory_file, np_array)
        serialized_np_array = memory_file.getvalue()
    return serialized_np_array


def configure_testbed(testbed, args):
    if testbed.mode == ngp.TestbedMode.Sdf:
        testbed.tonemap_curve = ngp.TonemapCurve.ACES

    testbed.exposure = args.exposure
    testbed.nerf.render_with_lens_distortion = True

    if args.nerf_compatibility:
        print(f"NeRF compatibility mode enabled")

        # Prior nerf papers accumulate/blend in the sRGB
        # color space. This messes not only with background
        # alpha, but also with DOF effects and the likes.
        # We support this behavior, but we only enable it
        # for the case of synthetic nerf data where we need
        # to compare PSNR numbers to results of prior work.
        testbed.color_space = ngp.ColorSpace.SRGB

        # No exponential cone tracing. Slightly increases
        # quality at the cost of speed. This is done by
        # default on scenes with AABB 1 (like the synthetic
        # ones), but not on larger scenes. So force the
        # setting here.
        testbed.nerf.cone_angle_constant = 0

        # Match nerf paper behaviour and train on a fixed bg.
        testbed.nerf.training.random_bg_color = False


def linear_to_srgb(img):
    """Copy of linear_to_srgb(img) in instant-ngp/scripts/common.py"""
    limit = 0.0031308
    return np.where(
        img > limit, 1.055 * (img ** (1.0 / 2.4)) - 0.055, 12.92 * img
    )


def post_process_image(img):
    """See instant-ngp/scripts/common.py
    write_image(file, img, quality=95)
    write_image_imageio(img_file, img, quality)
    """

    # See: write_image(file, img, quality=95)
    if img.shape[2] == 4:
        img = np.copy(img)
        # Unmultiply alpha
        img[..., 0:3] = np.divide(
            img[..., 0:3],
            img[..., 3:4],
            out=np.zeros_like(img[..., 0:3]),
            where=img[..., 3:4] != 0,
        )
        img[..., 0:3] = linear_to_srgb(img[..., 0:3])
    else:
        img = linear_to_srgb(img)

    # # See: write_image_imageio(img_file, img, quality)
    # img = (np.clip(img, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)

    return img


def create_single_screenshot(testbed, args):
    with open(args.temp_json_ifp) as f:
        ref_transforms = json.load(f)

    print("ref_transforms")
    print(ref_transforms)

    testbed.fov_axis = 0
    testbed.fov = ref_transforms["camera_angle_x"] * 180 / np.pi

    assert len(ref_transforms["frames"]) == 1, len(ref_transforms["frames"])

    f = ref_transforms["frames"][0]
    if "transform_matrix" in f:
        cam_matrix = f["transform_matrix"]
    elif "transform_matrix_start" in f:
        cam_matrix = f["transform_matrix_start"]
    else:
        raise KeyError()
    testbed.set_nerf_camera_matrix(np.matrix(cam_matrix)[:-1, :])

    image = testbed.render(
        int(ref_transforms["w"]),
        int(ref_transforms["h"]),
        args.samples_per_pixel,
        True,
    )
    image = post_process_image(image)
    return image


if __name__ == "__main__":
    parser = create_args_parser()
    args = parser.parse_args()

    for system_dp in args.additional_system_dps:
        assert os.path.isdir(system_dp)
        sys.path.append(system_dp)

    # The following import (i.e. "import pyngp as ngp") requires the python
    #  build directory of instant_ngp (i.e. "path/to/instant_ngp/build") in the
    #  system path.
    import pyngp as ngp

    testbed = ngp.Testbed()

    testbed.load_snapshot(args.load_snapshot)
    configure_testbed(testbed, args)
    img_np_array = create_single_screenshot(testbed, args)
    write_np_array_to_file(img_np_array, args.temp_array_ofp, use_pickle=False)
