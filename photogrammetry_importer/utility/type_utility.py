def is_int(some_str):
    """ Return True, if the given string represents an integer value. """
    try:
        int(some_str)
        return True
    except ValueError:
        return False


def is_float(some_str):
    """ Return True, if the given string represents a float value. """
    try:
        float(some_str)
        return True
    except ValueError:
        return False
