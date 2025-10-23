
from data import ExpendableCityResources, ExpendableEmpireResources
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
        return [Effect(expendable_city_resources_per_tick=ExpendableCityResources(
            wealth=1
        ))]

class NeutralIdeology(Ideology):
    pass    


class Monarchy(Ideology):
    def __init__(self):
        super().__init__([
            Effect(
                duration_in_ticks=0,
                morale_per_tick=1,
                expendable_empire_resources_pct_increase=ExpendableEmpireResources(
                    knowledge=-2
                )
            )
        ])


