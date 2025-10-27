from __future__ import annotations

from army import ArmyAttributes, ArmyUnit
from building import Building
from engine.ideology import Ideology
from engine.location import WorldMap
from job_requirements import JobRequirements
from city import City
from data import ExpendableCityResources, ExpendableEmpireResources
from effects import Effect
from game import Game
from empire import Empire
from job import Job, CreationJob


# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

if __name__ == "__main__":

    worldmap = WorldMap(size=(1000, 1000))
    game = Game(worldmap)

    americanism = Ideology(effects_list=[])

    mequon = City((0, 0), 50)
    mequon._resources.wealth = 100

    US = Empire(50, capital_city=mequon, ideology=americanism)
    game.add_empire(US)

    class CUW(Building):
        name="CUW"
        size = 5
        effect = Effect(duration_in_ticks=0,
                                            expendable_city_resources_per_tick=ExpendableCityResources(
                                                wealth=2
                                            ))
        job_requirements = JobRequirements(
                                                city_resources_level1=ExpendableCityResources(
                                                    wealth=10
                                                ))
        description = "Concordia University Wisconsin"
    # print(isinstance(CUW))
    print("Mequon allegiance before US", mequon.allegiance)
    US.add_city(mequon)
    print("Mequon Allegiance after US", mequon.allegiance)
    print(mequon.knowledge)
    cuw_job = CreationJob(num_ticks=5, result=CUW)
    mequon.add_job(cuw_job)
    print(mequon.allegiance.game)

    class Menuge(ArmyUnit):
        name = "Professor Menuge"
        size = 1
        effect = Effect(
            expendable_empire_resources_per_tick=ExpendableEmpireResources(
                knowledge=1000000000000
            ))
        job_requirements = JobRequirements()
        description = "Profound Monty Python enjoyer."


    game.begin_game()