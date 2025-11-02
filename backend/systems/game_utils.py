"""
Game balance and calculation utilities.

This module provides mathematical functions for game balance calculations,
particularly morale effects on unit performance and stat conversion between
raw (unbounded) and bounded display values.
"""

from math import floor, exp, tanh, atanh

from ..core.constants import MAX_MORALE, HALF_MORALE


def new_value_given_morale(baseline: float, morale: float, k: float = 0.01) -> float:
    """
    Calculate a modified value based on morale using a sigmoid curve.
    
    At HALF_MORALE (50), the returned value equals the baseline.
    As morale increases or decreases, the value scales accordingly using an
    exponential sigmoid function for smooth, realistic behavior.
    
    Args:
        baseline: The base value when morale is at HALF_MORALE
        morale: Current morale level (0-100)
        k: Scaling factor controlling how sharply morale affects the value
           (default: 0.01 for gradual effect)
    
    Returns:
        The adjusted value based on morale
        
    Raises:
        AssertionError: If morale is not in the range [0, MAX_MORALE]
    
    Example:
        >>> new_value_given_morale(100, 50)  # Normal morale -> baseline
        100.0
        >>> new_value_given_morale(100, 100)  # Max morale -> higher value
        >>> new_value_given_morale(100, 0)    # Min morale -> lower value
    """
    assert 0 <= morale <= MAX_MORALE, (
        f"Morale must be between 0 and {MAX_MORALE}, got {morale}"
    )
    # Sigmoid curve: when morale = HALF_MORALE, returns baseline
    # When morale is higher, returns higher value; when lower, returns lower value
    return baseline * (2 / (1 + exp(-k * (morale - HALF_MORALE))))


# ============================================================================
# Raw Value Conversion System
# ============================================================================
# These functions convert between unbounded raw values and bounded display values.
# Raw values (raw_morale, raw_efficiency) are stored internally and are unbounded.
# When raw_value = 0, it corresponds to the baseline (50 for morale/efficiency).
# Display values are computed on-the-fly from raw values using a hyperbolic tangent curve
# that approaches 0 and 100 asymptotically, preventing easy extremes.

def bounded_stat_from_raw(raw_value: float, steepness: float = 0.001) -> float:
    """
    Convert an unbounded raw stat value to a bounded 0-100 display value.
    
    The conversion uses a hyperbolic tangent curve that:
    - Returns 50 when raw_value = 0 (baseline)
    - Approaches 0 as raw_value → -∞ (asymptotic)
    - Approaches 100 as raw_value → +∞ (asymptotic)
    - Has diminishing returns (each +1 raw value adds less display value as extremes approach)
    
    Args:
        raw_value: Unbounded value where 0 = baseline (50 displayed)
        steepness: How quickly saturation occurs (default: 0.001 for gentle curve)
                   Lower values = more gradual approach to extremes
                   Higher values = faster saturation
    
    Returns:
        Displayed value in range [0, 100]
    
    Examples:
        >>> bounded_stat_from_raw(0)        # 50.0 (baseline)
        >>> bounded_stat_from_raw(100)      # ~86.0 (approaching 100)
        >>> bounded_stat_from_raw(-100)     # ~14.0 (approaching 0)
        >>> bounded_stat_from_raw(1000)     # ~99.9 (near maximum)
    """
    scale = 50.0
    return scale + scale * tanh(steepness * raw_value)


def raw_stat_from_bounded(display_value: float, steepness: float = 0.001) -> float:
    """
    Convert a bounded 0-100 display value back to an unbounded raw value.
    
    This is the inverse of bounded_stat_from_raw. Used when initializing
    raw values from existing bounded values.
    
    Args:
        display_value: Value in range [0, 100]
        steepness: Must match the steepness used in bounded_stat_from_raw
    
    Returns:
        Raw unbounded value where 0 = baseline (50 displayed)
        
    Raises:
        ValueError: If display_value is not in [0, 100]
        ValueError: If display_value is exactly 0 or 100 (mathematically undefined)
    """
    if not (0 < display_value < 100):
        if display_value == 0:
            raise ValueError("Cannot convert display_value=0 to raw (would be -∞)")
        elif display_value == 100:
            raise ValueError("Cannot convert display_value=100 to raw (would be +∞)")
        else:
            raise ValueError(f"display_value must be in range (0, 100), got {display_value}")
    
    scale = 50.0
    normalized = (display_value - scale) / scale
    return atanh(normalized) / steepness