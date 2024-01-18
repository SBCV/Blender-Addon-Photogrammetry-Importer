from photogrammetry_importer.process_communication.serialization import (
    serialize_string,
    serialize_json_dict,
    deserialize_json_dict,
    serialize_numpy_array,
    deserialize_numpy_array,
)

BINARY_START_IDENTIFIER_STR = "_serialized_numpy_array_start_"
BINARY_END_IDENTIFIER_STR = "_serialized_numpy_array_end_"


def write_json_as_binary_string(json_dict):
    """Thin wrapper for serialize_json_dict()."""
    json_dict_serialized = serialize_json_dict(json_dict)
    return json_dict_serialized


def read_json_from_binary_string(json_dict_serialized):
    """Thin wrapper for deserialize_json_dict()."""
    json_dict = deserialize_json_dict(json_dict_serialized)
    return json_dict


def write_np_array_as_binary_string(np_array, use_pickle):
    """Write numpy array as binary string with start and end identifier."""
    serialized_np_array = serialize_numpy_array(
        np_array, use_pickle=use_pickle
    )
    serialized_string = serialize_string(BINARY_START_IDENTIFIER_STR) + b"\n"
    serialized_string += serialized_np_array + b"\n"
    serialized_string += serialize_string(BINARY_END_IDENTIFIER_STR) + b"\n"
    return serialized_string


def read_np_array_from_binary_string(process_output, use_pickle):
    """Read numpy array from binary string using start and end identifier."""
    lines = process_output.splitlines(keepends=True)
    binary_start_index, binary_end_index = _find_serialize_meta_information(
        lines
    )
    # IMPORTANT: The binary encoding of the numpy array potentially contains
    # new line characters (i.e. "\n"). Thus, while parsing the byte
    # representation multiple lines must be considered.
    serialized = b"".join(lines[binary_start_index + 1 : binary_end_index])
    np_array = deserialize_numpy_array(serialized, use_pickle=use_pickle)
    return np_array


def _find_serialize_meta_information(lines):
    binary_start_index = None
    binary_start_identifier = serialize_string(BINARY_START_IDENTIFIER_STR)
    for index, line in enumerate(lines):
        if line.startswith(binary_start_identifier):
            binary_start_index = index
            break
    assert binary_start_index is not None
    binary_end_index = None
    binary_end_identifier = serialize_string(BINARY_END_IDENTIFIER_STR)
    for relative_index, line in enumerate(lines[binary_start_index:]):
        index = binary_start_index + relative_index
        if line.startswith(binary_end_identifier):
            binary_end_index = index
            break
    return binary_start_index, binary_end_index
