
from job_requirements import HasJobRequirementsMixin


class Job:
    def __init__(self, num_ticks: int, result: HasJobRequirementsMixin, is_upgrade: bool):
        assert num_ticks > 0
        self._num_ticks = num_ticks
        self._result: HasJobRequirementsMixin = result 
        self._is_upgrade = is_upgrade
        
        self._is_destruction: bool = False
    
    def progress(self):
        self._num_ticks -= 1
        if self._num_ticks <= 0:
            self._num_ticks = 0

    def is_finished(self) -> bool:
        return self._num_ticks <= 0
    
    @property
    def result(self) -> HasJobRequirementsMixin:
        return self._result
    
    @property
    def is_upgrade(self) -> bool:
        return self._is_upgrade
    

class DestructionJob(Job):
    def __init__(self, num_ticks, result):
        super().__init__(num_ticks=num_ticks, result=result, is_upgrade=False)
        self._is_destruction = True
    
