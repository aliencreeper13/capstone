"""
Exception classes for the game engine.
Defines custom exceptions for game-specific errors.
"""

class GameException(Exception):
    pass

class RequirementsException(GameException):
    pass

class CapitalExclusiveException(GameException):
    pass

class BadEffect(GameException):
    pass

class BadAllegianceException(GameException):
    pass

class IllegalMoveException(GameException):
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

class UnauthorizedAccess(GameException):
    pass