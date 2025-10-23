from abc import ABC
from typing import Optional

from job_requirements import HasJobRequirementsMixin, JobRequirements
from unit import Unit


class Job(ABC):
    def __init__(self, num_ticks: int, result: Unit | type[Unit], *unit_args, **unit_kwargs):
        assert num_ticks > 0
        self._num_ticks = num_ticks
        self._result: Unit | type[Unit] = result

        self._unit_args = unit_args
        self._unit_kwargs = unit_kwargs  # if a creation job,
        # this indicates the arguments passed into the instantiation of the unit, if any
        if isinstance(result, type):  # a type indicates that it's a creation job
            self._is_upgrade = False
        elif isinstance(result, Unit): # an instance indicates that it's an upgrade
            self._is_upgrade = True
        else:
            raise ValueError("Bad result given")
        
        self._is_destruction: bool = False
        self._is_finished: bool = False

        self._final_result: Optional[Unit] = None
    
    def progress(self):
        """Move forward with the progress of the job"""
        self._num_ticks -= 1
        if self._num_ticks <= 0:
            if not self._is_finished:
                # if an upgrade, then upgrade the unit!!!
                if self._is_upgrade:
                    assert isinstance(self._result, Unit)
                    self._result.upgrade()
                    self._final_result = self._result
                # instantiate a new unit if a creation job
                else:
                    self._final_result = self._result(*self._unit_args, **self._unit_kwargs)
                self._is_finished = True
            self._num_ticks = 0



    def is_finished(self) -> bool:
        return self._num_ticks <= 0
    
    @property
    def result(self) -> Optional[Unit]:
        """
        :return: None if not finished, the resultant Unit if finished.
        If an upgrade, the unit will be a level higher than it was before
        If not an upgrade, a brand-new unit will be instantiated
        """
        return self._final_result
    
    @property
    def is_upgrade(self) -> bool:
        return self._is_upgrade

    @property
    def requirements(self) -> JobRequirements:
        return self._result.job_requirements

    @property
    def level_upon_completion(self) -> int:
        if self._is_finished:
            assert isinstance(self._final_result, Unit)
            return self._final_result.level
        else:
            if self._is_upgrade:
                assert isinstance(self._result, Unit)
                return self._result.level + 1
            else:
                return 1  # a new unit will start at level 1


class CreationJob(Job):
    def __init__(self, num_ticks: int, result: type[Unit]):
        if not isinstance(result, type):
            raise ValueError(f"A Creation Job requires a `type`, not an instance")
        if not issubclass(result, Unit):
            raise ValueError(f"A Creation Job `type` instance must be a subclass of `{Unit.__name__}`")
        super().__init__(num_ticks, result)

class UpgradeJob(Job):
    def __init__(self, num_ticks: int, result: Unit):
        if not isinstance(result, Unit):
            raise ValueError(f"An Upgrade Job requires a `{Unit.__name__} instance (not type)`")
        super().__init__(num_ticks, result)
    

class DestructionJob(Job):
    def __init__(self, num_ticks: int, result: Unit):
        super().__init__(num_ticks=num_ticks, result=result, is_upgrade=False)
        self._is_destruction = True
    
