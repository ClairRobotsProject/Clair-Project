"""Agent: coordinates sensing, policy evaluation, and skill execution."""

import logging
import threading
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from .action import Action
from .clock import Clock, WallClock
from .observation import CompositeObservation
from .policy import Policy
from .sensor import Sensor
from .skill import ExecutionResult, ExecutionStatus, Skill


@dataclass
class RunReport:
    status: ExecutionStatus
    message: str = ''
    steps: List[tuple] = field(default_factory=list)  # (Action, ExecutionResult)

    @property
    def ok(self) -> bool:
        return self.status is ExecutionStatus.SUCCEEDED


class Agent:
    """Runs the control cycle: observe -> Policy.get_action -> Skill.execute.

    The Agent holds one active Policy, any number of Skills and Sensors. It
    always stops every Skill when a run ends, however it ends.
    """

    def __init__(self, policy: Policy, skills: Sequence[Skill],
                 sensors: Sequence[Sensor] = (), clock: Optional[Clock] = None,
                 logger=None):
        self.policy = policy
        self.skills = list(skills)
        self.sensors = list(sensors)
        self.clock = clock or WallClock()
        self.log = logger or logging.getLogger('clair_agent')
        self._cancel = threading.Event()

    def observe(self) -> CompositeObservation:
        return CompositeObservation(
            stamp=self.clock.now(),
            observations={s.name: s.read() for s in self.sensors})

    def skill_for(self, action: Action) -> Optional[Skill]:
        for skill in self.skills:
            if skill.can_execute(action):
                return skill
        return None

    def cancel(self) -> None:
        """Ask the running behavior to stop. Safe to call from another thread."""
        self._cancel.set()

    def reset(self) -> None:
        self._cancel.clear()
        self.policy.reset()

    def run(self) -> RunReport:
        report = RunReport(ExecutionStatus.SUCCEEDED)
        step = 0
        try:
            while not self._cancel.is_set():
                action = self.policy.get_action(self.observe())
                if action is None:
                    report.message = f'policy finished after {step} actions'
                    break
                step += 1
                skill = self.skill_for(action)
                if skill is None:
                    result = ExecutionResult(
                        ExecutionStatus.FAILED, f'no skill can execute {action.name}')
                else:
                    self.log.info(f'[{step}] policy -> {action} -> skill {skill.name!r}')
                    result = skill.execute(action, self._cancel)
                report.steps.append((action, result))
                self.log.info(
                    f'[{step}] {action.name}: {result.status.value}'
                    + (f' ({result.message})' if result.message else ''))
                if not result.ok:
                    report.status = result.status
                    report.message = (
                        result.message or f'{action.name} {result.status.value}')
                    break
            if self._cancel.is_set() and report.status is not ExecutionStatus.FAILED:
                report.status = ExecutionStatus.CANCELLED
                report.message = f'cancelled after {step} actions'
        finally:
            self.stop()
        return report

    def stop(self) -> None:
        for skill in self.skills:
            try:
                skill.stop()
            except Exception as exc:  # stopping must reach every skill
                self.log.error(f'failed to stop skill {skill.name!r}: {exc}')
