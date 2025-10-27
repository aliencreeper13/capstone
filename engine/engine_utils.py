def soft_isinstance(obj, cls):
    def class_signature(c):
        return c.__name__, c.__qualname__

    obj_mro = [class_signature(c) for c in type(obj).__mro__]
    target_sig = class_signature(cls)

    if target_sig in obj_mro:
        return True

    # handle same class name from another module
    obj_class_names = [c.__name__ for c in type(obj).__mro__]
    return cls.__name__ in obj_class_names