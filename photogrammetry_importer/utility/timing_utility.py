import time


class StopWatch(object):
    """Class to measure computation times."""

    def __init__(self):
        self.last_t = time.time()

    def reset_time(self):
        """Reset the stop watch to the current point in time."""
        self.last_t = time.time()

    def get_elapsed_time(self):
        """Return the elapsed time."""
        current_t = time.time()
        elapsed_t = current_t - self.last_t
        self.last_t = current_t
        return elapsed_t
