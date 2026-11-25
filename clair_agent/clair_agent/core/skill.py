"""Skill: knows *how* to execute an Action through one or more Drivers."""

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .action import Action
from .driver import Driver


class ExecutionStatus(Enum):
    SUCCEEDED = 'succeeded'
    CANCELLED = 'cancelled'
    FAILED = 'failed'


@dataclass(frozen=True)
class ExecutionResult:
    status: ExecutionStatus
    message: str = ''

    @property
    def ok(self) -> bool:
        return self.status is ExecutionStatus.SUCCEEDED


class Skill(ABC):
    """Executes the Actions it supports using its Drivers.

    ``execute`` blocks until the action finishes, fails, or ``cancel`` is set.
    """

    def __init__(self, name: str, drivers: Sequence[Driver]):
        if not drivers:
            raise ValueError(f'Skill {name!r} needs at least one Driver')
        self.name = name
        self.drivers = list(drivers)

    @abstractmethod
    def can_execute(self, action: Action) -> bool:
        ...

    @abstractmethod
    def execute(self, action: Action, cancel: threading.Event) -> ExecutionResult:
        ...

    def stop(self) -> None:
        for driver in self.drivers:
            driver.stop()
