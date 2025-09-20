
class Job:
    def __init__(self, num_ticks: int, result): # todo: what type should `result` be?
        assert num_ticks > 0
        self._num_ticks = num_ticks
        self._result = result 
    
    def progress(self):
        self._num_ticks -= 1
        if self._num_ticks <= 0:
            self._num_ticks = 0

    def is_finished(self) -> bool:
        return self._num_ticks <= 0