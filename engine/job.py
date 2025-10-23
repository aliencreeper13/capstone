
from job_requirements import HasJobRequirementsMixin
from unit import Unit


class Job:
    def __init__(self, num_ticks: int, result: Unit):
        assert num_ticks > 0
        self._num_ticks = num_ticks
        self._result: Unit = result 
        self._is_upgrade = False
        
        self._is_destruction: bool = False
    
    def progress(self):
        self._num_ticks -= 1
        if self._num_ticks <= 0:
            self._num_ticks = 0

    def is_finished(self) -> bool:
        return self._num_ticks <= 0
    
    @property
    def result(self) -> Unit:
        return self._result
    
    @property
    def is_upgrade(self) -> bool:
        return self._is_upgrade
    
class UpgradeJob(Job):
    def __init__(self, num_ticks, result):
        super().__init__(num_ticks, result)
    

class DestructionJob(Job):
    def __init__(self, num_ticks, result):
        super().__init__(num_ticks=num_ticks, result=result, is_upgrade=False)
        self._is_destruction = True
    
