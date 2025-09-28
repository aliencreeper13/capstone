from math import floor, exp

from constants import MAX_MORALE, HALF_MORALE

def new_production_rate_given_morale(baseline_rate: int, morale: int, k: float = 0.01) -> float:
    assert 0 <= morale <= MAX_MORALE
    # if morale = 50, then the return value will just be the baseline rate
    return (baseline_rate*(2 / (1 + exp(-k*(morale - HALF_MORALE)))))