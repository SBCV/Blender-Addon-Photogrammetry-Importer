import time

class StopWatch(object):

    def __init__(self):
        self.last_t = time.time()

    def reset_time(self):
        self.last_t = time.time()

    def get_elapsed_time(self):
        current_t = time.time()
        elapsed_t = current_t - self.last_t
        self.last_t = current_t
        return elapsed_t