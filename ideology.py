
from effects import Effect
from dataclasses import dataclass

from gameobject import GameObject


class Ideology(GameObject):
    def __init__(self, effects_list: list[Effect]):
        self._neutral_effects = Ideology.neutral_effects()
        self._ideological_specific_effects = effects_list
        # self._effects: list[Effect] = self._neutral_effects + self._ideological_specific_effects

    @property
    def effects(self) -> list[Effect]:
        return self._neutral_effects + self._ideological_specific_effects
    
    # The effects that ALL ideologies possess
    @classmethod
    def neutral_effects(cls) -> list[Effect]:
        return [Effect(knowledge_per_tick=1)]

class NeutralIdeology(Ideology):
    pass    


