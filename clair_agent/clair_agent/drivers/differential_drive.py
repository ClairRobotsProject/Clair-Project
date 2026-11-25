"""Driver family for differential-drive bases."""

from abc import abstractmethod

from clair_agent.core import Driver


class DifferentialDriveDriver(Driver):
    """Commands a base by body velocity. Implementations clamp to their limits."""

    max_linear: float = float('inf')   # m/s
    max_angular: float = float('inf')  # rad/s

    @abstractmethod
    def set_velocity(self, linear: float, angular: float) -> None:
        """Command forward speed (m/s) and yaw rate (rad/s)."""

    def stop(self) -> None:
        self.set_velocity(0.0, 0.0)

    def clamp(self, linear: float, angular: float):
        return (max(-self.max_linear, min(self.max_linear, linear)),
                max(-self.max_angular, min(self.max_angular, angular)))
