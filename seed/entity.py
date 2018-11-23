"""Represents any uniquely identiable object. Intended as a base class."""
from typing import Tuple

class UidFactory:
    """a source of unique identifiers"""
    def __init__(self):
        self._current_uid = 0

    def get_uid(self):
        """Returns a unique identifier"""
        uid = self._current_uid
        self._current_uid += 1
        return uid

UID_SOURCE = UidFactory()

class Entity:
    """A uniquely identifiable object"""
    default_location_deltas = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
    def __init__(self, deltas: Tuple = default_location_deltas):
        self.uid = UID_SOURCE.get_uid()
        self.deltas = deltas
