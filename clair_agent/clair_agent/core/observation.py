"""Observation: the input a Policy decides from."""

from abc import ABC
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class Observation(ABC):
    """Base class for sensor output. ``stamp`` is seconds on the Agent's clock."""

    stamp: float = 0.0


@dataclass(frozen=True)
class CompositeObservation(Observation):
    """The latest Observation from each of the Agent's Sensors, keyed by sensor name.

    A sensor that has produced nothing yet maps to ``None``.
    """

    observations: Dict[str, Optional[Observation]] = field(default_factory=dict)

    def get(self, sensor_name: str) -> Optional[Observation]:
        return self.observations.get(sensor_name)
