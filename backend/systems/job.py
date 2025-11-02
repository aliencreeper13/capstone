"""
Job system for managing creation, upgrade, and destruction of units/buildings.

A job represents a work item that takes time to complete (multiple ticks).
Jobs can create new units, upgrade existing units, or destroy units.
"""

from __future__ import annotations
from abc import ABC
from typing import Optional, TYPE_CHECKING

from .job_requirements import JobRequirements

if TYPE_CHECKING:
    from ..entities.unit import Unit


class Job(ABC):
    """
    Base class for all jobs (creation, upgrade, destruction).
    
    A job takes multiple ticks to complete and produces a result.
    During completion, it may instantiate a new unit or upgrade an existing one.
    
    Attributes:
        _num_ticks: Remaining ticks to complete job
        _result: The unit type (for creation) or unit instance (for upgrade/destruction)
        _is_upgrade: True if upgrading existing unit, False if creating new
        _is_destruction: True if destroying a unit
        _is_finished: True once job is completed
        _final_result: The completed unit instance (None until finished)
        _unit_args: Positional args for unit instantiation
        _unit_kwargs: Keyword args for unit instantiation
    """
    
    def __init__(self, num_ticks: int, result: "Unit | type[Unit]", *unit_args, **unit_kwargs):
        """
        Initialize a job.
        
        Args:
            num_ticks: Number of ticks until job completion (must be > 0)
            result: Unit type (for creation) or Unit instance (for upgrade/destruction)
            *unit_args: Positional arguments for unit instantiation
            **unit_kwargs: Keyword arguments for unit instantiation
            
        Raises:
            ValueError: If result is neither a type nor Unit instance
            AssertionError: If num_ticks <= 0
        """
        assert num_ticks > 0, f"Job duration must be > 0, got {num_ticks}"
        
        self._num_ticks = num_ticks
        self._result: "Unit | type[Unit]" = result
        self._unit_args = unit_args
        self._unit_kwargs = unit_kwargs
        
        # Determine if this is a creation or upgrade job based on result type
        self._is_upgrade = self._determine_is_upgrade(result)
        self._is_destruction: bool = False
        self._is_finished: bool = False
        self._final_result: Optional[Unit] = None
    
    @staticmethod
    def _determine_is_upgrade(result) -> bool:
        """
        Determine if a job is an upgrade job based on result type.
        
        Args:
            result: Either a Unit type (creation) or Unit instance (upgrade)
            
        Returns:
            False if result is a type (creation job)
            True if result is a Unit instance (upgrade job)
            
        Raises:
            ValueError: If result is neither a type nor Unit instance
        """
        # Import here to avoid circular dependency
        from ..entities.unit import Unit
        
        if isinstance(result, type):
            return False
        elif isinstance(result, Unit):
            return True
        else:
            raise ValueError(f"Job result must be a Unit type or instance, got {type(result)}")
    
    def progress(self, ticks_elapsed: float = 1) -> None:
        """
        Advance job by a certain number of ticks.

        Args:
            ticks_elapsed: Number of ticks to progress (default 1)
        
        When ticks reach zero, completes the job:
        - For creation jobs: instantiates the unit
        - For upgrade jobs: calls upgrade() on the unit
        - For destruction jobs: marks for removal
        """
        self._num_ticks -= ticks_elapsed
        
        # Complete job when ticks reach zero
        if self._num_ticks <= 0 and not self._is_finished:
            self._complete_job()
            self._num_ticks = 0
    
    def _complete_job(self) -> None:
        """
        Complete the job and set the result.
        
        Called when job ticks reach zero. Handles creation, upgrade, and destruction.
        """
        # Import here to avoid circular dependency
        from ..entities.unit import Unit
        
        if self._is_upgrade:
            # Upgrade existing unit
            assert isinstance(self._result, Unit), f"Expected Unit instance, got {type(self._result)}"
            self._result.upgrade()
            self._final_result = self._result
        else:
            # Create new unit from type
            assert isinstance(self._result, type), f"Expected Unit type, got {type(self._result)}"
            self._final_result = self._result(*self._unit_args, **self._unit_kwargs)
        
        self._is_finished = True

    def is_finished(self) -> bool:
        """Return True if job has completed."""
        return self._num_ticks <= 0
    
    @property
    def result(self) -> Optional["Unit"]:
        """
        Get the completed unit (only valid after job is finished).
        
        Returns:
            None if job is not finished
            For creation: newly instantiated unit
            For upgrade: the upgraded unit instance
            For destruction: the unit marked for removal
        """
        return self._final_result
    
    @property
    def is_upgrade(self) -> bool:
        """Return True if this job upgrades an existing unit."""
        return self._is_upgrade

    @property
    def requirements(self) -> JobRequirements:
        """Get the job requirements from the unit."""
        return self._result.job_requirements

    @property
    def level_upon_completion(self) -> int:
        """
        Get the level the unit will be upon job completion.
        
        Returns:
            For finished jobs: the actual completed unit's level
            For upgrade jobs: current level + 1
            For creation jobs: 1 (new units start at level 1)
        """
        # Import here to avoid circular dependency
        from ..entities.unit import Unit
        
        if self._is_finished:
            assert isinstance(self._final_result, Unit), f"Expected Unit, got {type(self._final_result)}"
            return self._final_result.level
        elif self._is_upgrade:
            assert isinstance(self._result, Unit), f"Expected Unit instance, got {type(self._result)}"
            return self._result.level + 1
        else:
            # Creation jobs always start at level 1
            return 1


class CreationJob(Job):
    """
    Job for creating a new unit/building instance.
    
    Takes a unit type and instantiates it after the required ticks.
    """
    
    def __init__(self, num_ticks: int, result: type[Unit]):
        """
        Initialize a creation job.
        
        Args:
            num_ticks: Ticks until job completion
            result: Unit type to instantiate (must be type, not instance)
            
        Raises:
            ValueError: If result is not a type or not a Unit subclass
        """
        # Import here to avoid circular dependency
        from ..entities.unit import Unit
        
        if not isinstance(result, type):
            raise ValueError(f"CreationJob requires a Unit type, not an instance of {type(result)}")
        
        if not issubclass(result, Unit):
            raise ValueError(f"CreationJob type must be a subclass of Unit, got {result}")
        
        super().__init__(num_ticks, result)


class UpgradeJob(Job):
    """
    Job for upgrading an existing unit/building to the next level.
    
    Takes a unit instance and increases its level after the required ticks.
    """
    
    def __init__(self, num_ticks: int, result: Unit):
        """
        Initialize an upgrade job.
        
        Args:
            num_ticks: Ticks until job completion
            result: Unit instance to upgrade
            
        Raises:
            ValueError: If result is not a Unit instance
        """
        # Import here to avoid circular dependency
        from ..entities.unit import Unit
        
        if not isinstance(result, Unit):
            raise ValueError(f"UpgradeJob requires a Unit instance, not {type(result)}")
        super().__init__(num_ticks, result)


class DestructionJob(Job):
    """
    Job for destroying a unit/building and reclaiming some resources.
    
    Removes the unit from the city after the required ticks.
    """
    
    def __init__(self, num_ticks: int, result: Unit):
        """
        Initialize a destruction job.
        
        Args:
            num_ticks: Ticks until destruction completes
            result: Unit instance to destroy
            
        Raises:
            ValueError: If result is not a Unit instance
        """
        # Import here to avoid circular dependency
        from ..entities.unit import Unit
        
        if not isinstance(result, Unit):
            raise ValueError(f"DestructionJob requires a Unit instance, not {type(result)}")
        super().__init__(num_ticks=num_ticks, result=result)
        self._is_destruction = True