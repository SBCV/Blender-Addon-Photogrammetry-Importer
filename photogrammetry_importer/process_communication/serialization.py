import io
import pickle
import json
import numpy as np

RAW_UNICODE_ESCAPE = "raw_unicode_escape"


def serialize_string(plain_string):
    """Serialize string using raw unicode escapes."""
    serialized_string = plain_string.encode(RAW_UNICODE_ESCAPE)
    return serialized_string


def serialize_json_dict(json_dict):
    """Serialize json dict using raw unicode escapes."""
    json_dict_serialized = json.dumps(json_dict).encode(RAW_UNICODE_ESCAPE)
    return json_dict_serialized


def deserialize_json_dict(serialized_json_dict):
    """Deserialize json dict using raw unicode escapes."""
    json_dict_str = serialized_json_dict.decode(RAW_UNICODE_ESCAPE)
    json_dict = json.loads(json_dict_str)
    return json_dict


def serialize_numpy_array(np_array, use_pickle=False):
    """Serialize numpy array."""
    if use_pickle:
        serialized_np_array = pickle.dumps(np_array)
    else:
        # https://stackoverflow.com/questions/30698004/how-can-i-serialize-a-numpy-array-while-preserving-matrix-dimensions
        memory_file = io.BytesIO()
        np.save(memory_file, np_array)
        serialized_np_array = memory_file.getvalue()
    return serialized_np_array


def deserialize_numpy_array(serialized_np_array, use_pickle=False):
    """Deserialize numpy array."""
    if use_pickle:
        np_array = pickle.loads(serialized_np_array)
    else:
        # https://stackoverflow.com/questions/30698004/how-can-i-serialize-a-numpy-array-while-preserving-matrix-dimensions
        memory_file = io.BytesIO()
        memory_file.write(serialized_np_array)
        memory_file.seek(0)
        np_array = np.load(memory_file)
    return np_array
