class GameException(Exception):
    pass

class RequirementsExeption(GameException):
    pass

class CapitalExclusiveException(GameException):
    pass

class BadEffect(GameException):
    pass

class BadAllegianceException(GameException):
    pass

class AlreadyContainedException(GameException):
    pass

class NotEnoughWorkersException(GameException):
    pass

class BadGameNodeException(GameException):
    pass

class BadDirectionException(GameException):
    pass

class NotAssignedToGameException(GameException):
    pass