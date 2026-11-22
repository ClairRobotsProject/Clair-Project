"""Concrete Observation types. Plain data, no ROS types."""

from dataclasses import dataclass
from typing import Any

from clair_agent.core import Observation


@dataclass(frozen=True)
class OdometryObservation(Observation):
    """Planar pose (m, rad) and body velocity (m/s, rad/s) in the odom frame."""

    x: float = 0.0
    y: float = 0.0
    yaw: float = 0.0
    linear: float = 0.0
    angular: float = 0.0


@dataclass(frozen=True)
class RGBObservation(Observation):
    """An RGB image as an ``(height, width, 3)`` uint8 array."""

    image: Any = None
    width: int = 0
    height: int = 0
