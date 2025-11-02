"""
Engine utilities for flexible type checking and game-wide utilities.
Provides tools for dealing with dynamically loaded classes and flexible type comparisons.
"""


def soft_isinstance(obj, cls):
    """
    Flexible isinstance check that handles classes loaded from different modules.
    
    Useful when classes might be reloaded or imported from different paths,
    comparing by class name and MRO instead of strict identity.
    
    Args:
        obj: Object to check
        cls: Class to check against
        
    Returns:
        True if obj is an instance of cls (by name or MRO), False otherwise
    """
    def class_signature(c):
        return c.__name__, c.__qualname__

    obj_mro = [class_signature(c) for c in type(obj).__mro__]
    target_sig = class_signature(cls)

    if target_sig in obj_mro:
        return True

    # handle same class name from another module
    obj_class_names = [c.__name__ for c in type(obj).__mro__]
    return cls.__name__ in obj_class_names