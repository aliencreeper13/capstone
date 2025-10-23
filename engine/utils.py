from math import floor, exp

from constants import MAX_MORALE, HALF_MORALE

def new_value_given_morale(baseline: float, morale: float, k: float = 0.01) -> float:
    assert 0 <= morale <= MAX_MORALE
    # if morale = 50, then the return value will just be the baseline rate
    return (baseline*(2 / (1 + exp(-k*(morale - HALF_MORALE)))))