from photogrammetry_importer.process_communication.serialization import (
    serialize_json_dict,
    deserialize_json_dict,
    serialize_numpy_array,
    deserialize_numpy_array,
)


def write_json_to_file(json_dict, temp_json_ofp):
    json_dict_serialized = serialize_json_dict(json_dict)
    with open(temp_json_ofp, "wb") as opened_temp_json_file:
        opened_temp_json_file.write(json_dict_serialized)


def read_json_from_file(temp_ifp):
    with open(temp_ifp, "rb") as opened_temp_json_file:
        json_dict_serialized = opened_temp_json_file.read()
    json_dict = deserialize_json_dict(json_dict_serialized)
    return json_dict


def write_np_array_to_file(np_array, temp_ofp, use_pickle):
    serialized_np_array = serialize_numpy_array(
        np_array, use_pickle=use_pickle
    )
    with open(temp_ofp, "wb") as f:
        f.write(serialized_np_array)


def read_np_array_from_file(temp_array_ifp, use_pickle):
    with open(temp_array_ifp, "rb") as opened_temp_array_file:
        serialized_np_array = opened_temp_array_file.read()
    np_array = deserialize_numpy_array(
        serialized_np_array, use_pickle=use_pickle
    )
    return np_array
