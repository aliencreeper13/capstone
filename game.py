from Empire import Empire

class Game:
    def __init__(self, empires: list[Empire]):
        self._current_tick: int = 0
        self._empires: list[Empire] = empires
        for empire in self._empires:
            assert not empire.assigned_to_game()
            empire.assign_to_game(self)
            

    def next_tick(self):
        self._current_tick += 1
        for empire in self._empires:
            empire.update(self._current_tick)

    @property
    def current_tick(self) -> int:
        return self._current_tick

class EmptyGame(Game):
    """
    A newly instantiated empire is assigned to an empty game until it is assigned to a real game
    """
    # this makes this a singleton class
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(EmptyGame, cls).__new__(cls)
        return cls.instance