
from effects import Effects
from dataclasses import dataclass


class Ideology:
    def __init__(self, effects_list: list[Effects]):
        self._effects: list[Effects] = effects_list

class NeutralIdeology(Ideology):
    pass    


