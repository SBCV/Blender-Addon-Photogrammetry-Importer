import os

def get_file_paths_in_dir(idp,
                          ext=None,
                          target_str_or_list=None,
                          ignore_str_or_list=None,
                          base_name_only=False,
                          relative_path_only=False,
                          without_ext=False,
                          sort_result=True,
                          natural_sorting=False,
                          recursive=False):

    """ ext can be a list of extensions or a single extension
        (e.g. ['.jpg', '.png'] or '.jpg')
    """

    if recursive:
        ifp_s = []
        for root, dirs, files in os.walk(idp):
            ifp_s += [os.path.join(root, ele) for ele in files]
    else:
        ifp_s = [os.path.join(idp, ele) for ele in os.listdir(idp)
                 if os.path.isfile(os.path.join(idp, ele))]

    if ext is not None:
        if isinstance(ext, list):
            ifp_s = [ifp for ifp in ifp_s if os.path.splitext(ifp)[1].lower() in ext]
        else:
            ifp_s = [ifp for ifp in ifp_s if os.path.splitext(ifp)[1].lower() == ext]

    if target_str_or_list is not None:
        if type(target_str_or_list) == str:
            target_str_or_list = [target_str_or_list]
        for target_str in target_str_or_list:
            ifp_s = [ifp for ifp in ifp_s if target_str in os.path.basename(ifp)]

    if ignore_str_or_list is not None:
        if type(ignore_str_or_list) == str:
            ignore_str_or_list = [ignore_str_or_list]
        for ignore_str in ignore_str_or_list:
            ifp_s = [ifp for ifp in ifp_s if ignore_str not in os.path.basename(ifp)]

    assert not (base_name_only and relative_path_only)
    if base_name_only:
        ifp_s = [os.path.basename(ifp) for ifp in ifp_s]

    if relative_path_only:
        ifp_s = [os.path.relpath(ifp, idp) for ifp in ifp_s]

    if without_ext:
        ifp_s = [os.path.splitext(ifp)[0] for ifp in ifp_s]

    if sort_result:
        if natural_sorting:
            ifp_s = sorted(ifp_s, key=natural_key)
        else:
            ifp_s = sorted(ifp_s)

    return ifp_s


def get_image_file_paths_in_dir(idp,
                                base_name_only=False,
                                relative_path_only=False,
                                without_ext=False,
                                sort_result=True,
                                recursive=True,
                                target_str_or_list=None):
    return get_file_paths_in_dir(
        idp,
        ext=['.rgb', '.gif', '.pbm', '.pgm', '.ppm', '.pnm', '.tiff', '.tif', 
                    '.rast', '.xbm', '.jpg', '.jpeg', '.png', '.bmp', '.png',
                    '.webp', '.exr', '.hdr', '.svg'],
        target_str_or_list=target_str_or_list,
        base_name_only=base_name_only,
        relative_path_only=relative_path_only,
        without_ext=without_ext,
        sort_result=sort_result,
        recursive=recursive)