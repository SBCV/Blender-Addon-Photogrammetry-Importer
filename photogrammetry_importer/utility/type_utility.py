def is_int(some_str):
    try:
        int(some_str)
        return True
    except ValueError:
        return False


def is_float(some_str):
    try:
        float(some_str)
        return True
    except ValueError:
        return False
