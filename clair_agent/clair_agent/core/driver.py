"""Driver: translates execution requests into robot-specific commands."""

from abc import ABC, abstractmethod


class Driver(ABC):
    """Base interface for robot adapters. Families (differential drive, arm,
    cartesian, ...) extend it with their own command methods."""

    @abstractmethod
    def stop(self) -> None:
        """Bring the hardware this driver controls to a safe halt."""

    def is_ready(self) -> bool:
        """Whether the robot side is connected and will receive commands."""
        return True
