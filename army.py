from unit import Unit


class ArmyUnit(Unit):
    def __init__(self, hitpoints: int, speed: int, damage_per_tick: int):
        self._hitpoints: int = hitpoints
        self._speed: int = speed
        self._damage_per_tick: int = damage_per_tick