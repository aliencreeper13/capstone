from __future__ import annotations

from army import ArmyAttributes, ArmyUnit
from building import Building
from job_requirements import JobRequirements
from city import City
from data import ExpendableCityResources
from effects import Effect
from game import Game
from empire import Empire
from job import Job

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
    game = Game([])

    US = Empire(50)
    game.add_empire(US)

    mequon = City(10, 50.0)
    mequon._resources.wealth = 100
    cuw = Building("CUW", 2, effects=Effect(duration_in_ticks=0,
                                            expendable_city_resources_per_tick=ExpendableCityResources(
                                                wealth=2
                                            )),
                                            requirements=JobRequirements(
                                                city_resources_level1=ExpendableCityResources(
                                                    wealth=10
                                                )
                                            ))
    print("Mequon allegiance before US", mequon.allegiance)
    US.add_city(mequon)
    print("Mequon Allegiance after US", mequon.allegiance)
    print(mequon.knowledge)
    cuw_job = Job(num_ticks=5, result=cuw, is_upgrade=False)
    mequon.add_job(cuw_job)
    print(mequon.allegiance.game)


    professor_menuge = ArmyUnit(
        name="Professor Menuge",
        size=1,
        effects=Effect(knowledge_per_tick=1000000000),
        requirements=JobRequirements(
            contingent_on=[cuw]
        ),
        allegiance=US,
        base_attributes=ArmyAttributes(
            hitpoints=1000000,
            speed=100000,
            damage_per_tick=1000000000000000000000000000000000
        )
    )

    game.begin_game()