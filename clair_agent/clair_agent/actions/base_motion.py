"""Base-motion actions for a mobile robot. Units: metres, radians, seconds."""

from dataclasses import dataclass

from clair_agent.core import Action


@dataclass(frozen=True)
class BaseMotionAction(Action):
    """Hold a body velocity for a fixed duration, then stop.

    ``linear`` is forward speed in m/s (negative = backwards) and ``angular``
    is yaw rate in rad/s (positive = counter-clockwise).
    """

    linear: float = 0.0
    angular: float = 0.0
    duration: float = 0.0
    label: str = ''

    def __post_init__(self):
        if self.duration < 0:
            raise ValueError('duration must be >= 0')

    def __str__(self) -> str:
        tag = f'{self.label}: ' if self.label else ''
        return (f'{self.name}({tag}linear={self.linear:+.2f} m/s, '
                f'angular={self.angular:+.2f} rad/s, {self.duration:.2f} s)')


@dataclass(frozen=True)
class DriveAction(BaseMotionAction):
    """Translate straight forward or backward."""


@dataclass(frozen=True)
class RotateAction(BaseMotionAction):
    """Turn in place."""


@dataclass(frozen=True)
class ArcAction(BaseMotionAction):
    """Translate and turn at the same time."""


@dataclass(frozen=True)
class StopAction(BaseMotionAction):
    """Stand still for ``duration`` seconds."""

    def __post_init__(self):
        super().__post_init__()
        if self.linear or self.angular:
            raise ValueError('StopAction cannot carry a velocity')
