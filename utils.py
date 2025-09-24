from math import floor, exp

def new_production_rate_given_morale(baseline_rate: int, morale: int, k: float = 0.01):
    assert 0 <= morale <= 100
    # if morale = 50, then the return value will just be the baseline rate
    return floor(baseline_rate*(2 / (1 + exp(-k*(morale - 50)))))