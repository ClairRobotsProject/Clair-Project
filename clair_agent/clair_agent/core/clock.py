"""Clock abstraction so skills run on simulation time and tests run instantly."""

import time
from abc import ABC, abstractmethod


class Clock(ABC):

    @abstractmethod
    def now(self) -> float:
        """Current time in seconds."""

    @abstractmethod
    def sleep(self, seconds: float) -> None:
        """Block for ``seconds`` of this clock's time."""


class WallClock(Clock):

    def now(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)
