"""
Game Event System

This module defines the event system for tracking significant occurrences during gameplay.
Events are used to log battles, resource changes, building completions, unit creation,
city captures, and other important game state transitions.

Event Flow:
    1. Events are created by various game systems (army, city, empire)
    2. Events are timestamped and classified by type
    3. Events can be serialized to JSON for UI display or persistence
    4. Events contain rich metadata for debugging and gameplay feedback

Event Types:
    - battle_tick: Combat round occurred
    - battle_result: Battle concluded with winner/loser
    - city_captured: City ownership changed
    - building_completed: Construction finished
    - unit_created: New unit spawned
    - resource_change: Resource quantities modified
    - custom: Application-specific event
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Literal

from ..core.gameobject import DataclassGameObject

EventType = Literal[
    "battle_tick", "battle_result", "city_captured", 
    "building_completed", "unit_created", 
    "resource_change", "custom", "job_submission", "upgrade_completed"
    "city_founded", "new_city"
]
"""
Valid event type classifications.

Attributes:
    battle_tick: A single round of combat occurred
    battle_result: Combat concluded with final outcome
    city_captured: City changed ownership
    building_completed: Construction finished and building is operational
    unit_created: New military unit was spawned
    resource_change: City or empire resources were modified
    custom: Game-specific or user-defined event type
"""


@dataclass
class GameEvent(DataclassGameObject):
    """
    Represents a significant game event with timing and contextual data.
    
    This is the primary event class used throughout the game to track battles,
    resource changes, building completions, and other important state transitions.
    Events can be logged, serialized for UI display, or used for debugging.
    
    Attributes:
        type (EventType): Classification of the event (e.g., "battle_result", "resource_change")
        timestamp (int): When the event occurred (in game time)
        source (str): Which game system created the event (e.g., "Army", "City", "Empire")
        description (str): Human-readable summary of what happened
        data (dict[str, Any]): Additional event metadata:
            - For "battle_result": keys like "victor", "loser", "casualties", "damage"
            - For "city_captured": keys like "city_id", "attacker", "defender"
            - For "resource_change": keys like "resource_type", "old_value", "new_value"
            - For "building_completed": keys like "building_type", "city_id"
            - For "unit_created": keys like "unit_type", "city_id", "count"
    
    Example:
        >>> from datetime import datetime
        >>> event = GameEvent(
        ...     type="resource_change",
        ...     unix_timestamp=int(datetime.now().timestamp()),
        ...     source="City",
        ...     description="Market produced 10 wealth",
        ...     data={"resource_type": "wealth", "amount": 10}
        ... )
        >>> print(event.short_summary())
        [resource_change] Market produced 10 wealth
    """
    
    type: EventType
    """Event classification identifying what kind of occurrence this is."""
    
    unix_timestamp: int
    """When the event occurred in unix time."""
    
    source: str
    """Which game system created this event (e.g., 'Army', 'City', 'Empire')."""
    
    description: str
    """Human-readable description of what happened."""
    
    data: dict[str, Any] = field(default_factory=dict)
    """
    Additional event metadata specific to the event type.
    
    Contents depend on the event type and source system. Used for detailed
    game logic, debugging, and UI rendering.
    """

    triggered_by_ai: bool = False
    """Whether this event was triggered by AI actions (True) or human player (False)."""

    @property
    def timestamp(self) -> datetime:
        """Get the event timestamp as a datetime object."""
        return datetime.fromtimestamp(self.unix_timestamp)

    def short_summary(self) -> str:
        """
        Generate a brief one-line event summary.
        
        Returns:
            str: Formatted string like "[battle_result] Army defeated defenders"
        
        Example:
            >>> event = GameEvent(
            ...     type="building_completed",
            ...     unix_timestamp=int(datetime.now().timestamp()),
            ...     source="City",
            ...     description="Market construction completed",
            ... )
            >>> print(event.short_summary())
            [building_completed] Market construction completed
        """
        return f"[{self.type}] {self.description}"

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the event to a dictionary for JSON export or API responses.
        
        Converts the datetime object to ISO format string for JSON compatibility.
        Used primarily for transmitting event data to the frontend UI or
        persistence layers.
        
        Returns:
            dict[str, Any]: Serialized event with keys:
                - type: str - the event classification
                - timestamp: str - ISO format datetime string
                - source: str - which system created the event
                - description: str - human-readable summary
                - data: dict - additional metadata
        
        Example:
            >>> from datetime import datetime
            >>> event = GameEvent(
            ...     type="unit_created",
            ...     timestamp=datetime(2024, 1, 15, 10, 30),
            ...     source="Army",
            ...     description="Infantry unit spawned",
            ...     data={"unit_type": "Infantry", "count": 5}
            ... )
            >>> event_dict = event.to_dict()
            >>> event_dict["timestamp"]
            '2024-01-15T10:30:00'
        """
        return {
            "type": self.type,
            "unix_timestamp": self.unix_timestamp,
            "source": self.source,
            "description": self.description,
            "data": self.data,
            "triggered_by_ai": self.triggered_by_ai,
        }