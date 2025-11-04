from .mobile_unit import MobileUnit
class PassiveUnit(MobileUnit):
    def __init__(self):
        """Initialize passive unit which cannot inflict damage."""
        super().__init__()
        if self._base_attributes.damage_per_tick > 0:
            raise ValueError("PassiveUnit damage_per_tick must be 0")