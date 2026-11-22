"""Skill that executes base-motion Actions on a differential-drive Driver."""

import threading

from clair_agent.actions import BaseMotionAction
from clair_agent.core import (
    Action, Clock, ExecutionResult, ExecutionStatus, Skill, WallClock)
from clair_agent.drivers import DifferentialDriveDriver


class BaseMotionSkill(Skill):
    """Holds the requested velocity for the action's duration, then stops.

    The command is re-sent at ``rate_hz`` so the base keeps moving on drivers
    with a command timeout, and so cancellation takes effect within one period.
    """

    def __init__(self, driver: DifferentialDriveDriver, clock: Clock = None,
                 rate_hz: float = 20.0, name: str = 'base_motion'):
        super().__init__(name, [driver])
        if rate_hz <= 0:
            raise ValueError('rate_hz must be > 0')
        self.driver = driver
        self.clock = clock or WallClock()
        self.period = 1.0 / rate_hz

    def can_execute(self, action: Action) -> bool:
        return isinstance(action, BaseMotionAction)

    def execute(self, action: Action, cancel: threading.Event) -> ExecutionResult:
        if not self.can_execute(action):
            return ExecutionResult(
                ExecutionStatus.FAILED, f'{self.name} cannot execute {action.name}')
        try:
            end = self.clock.now() + action.duration
            while not cancel.is_set():
                remaining = end - self.clock.now()
                if remaining <= 0:
                    break
                self.driver.set_velocity(action.linear, action.angular)
                self.clock.sleep(min(self.period, remaining))
        except Exception as exc:
            return ExecutionResult(ExecutionStatus.FAILED, f'driver error: {exc}')
        finally:
            self.driver.stop()
        if cancel.is_set():
            return ExecutionResult(ExecutionStatus.CANCELLED)
        return ExecutionResult(ExecutionStatus.SUCCEEDED)
