"""Sensor: acquires data and exposes it as an Observation."""

from abc import ABC, abstractmethod
from typing import Optional

from .observation import Observation


class Sensor(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def read(self) -> Optional[Observation]:
        """Return the latest Observation, or ``None`` if nothing has arrived."""
