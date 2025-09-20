class Unit:
    def __init__(self,  name: str, size: int = 1):
        self.name = name
        self._size = size
        self.level = 1

    @property
    def size(self) -> int:
        return self._size