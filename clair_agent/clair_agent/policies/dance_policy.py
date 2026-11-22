"""Scripted dance: a fixed sequence of base-motion Actions."""

from typing import Iterable, List, Optional

import yaml

from clair_agent.actions import (
    ArcAction, BaseMotionAction, DriveAction, RotateAction, StopAction)
from clair_agent.core import Action, Observation, Policy


class ScriptedDancePolicy(Policy):
    """Plays back a choreography one Action per call, then returns ``None``.

    The Observation is ignored: the dance is open loop. The interface stays
    compatible with policies that do use sensor feedback.
    """

    def __init__(self, choreography: Iterable[BaseMotionAction]):
        self._steps: List[BaseMotionAction] = list(choreography)
        if not self._steps:
            raise ValueError('choreography is empty')
        self._index = 0

    def get_action(self, observation: Observation) -> Optional[Action]:
        if self._index >= len(self._steps):
            return None
        action = self._steps[self._index]
        self._index += 1
        return action

    def reset(self) -> None:
        self._index = 0

    def __len__(self) -> int:
        return len(self._steps)

    @property
    def total_duration(self) -> float:
        return sum(step.duration for step in self._steps)

    @classmethod
    def from_yaml(cls, path: str) -> 'ScriptedDancePolicy':
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(parse_choreography(data))


def parse_choreography(data) -> List[BaseMotionAction]:
    """Build actions from ``{'dance': [{name, linear, angular, duration, repeat}]}``."""
    if not isinstance(data, dict) or not isinstance(data.get('dance'), list):
        raise ValueError("choreography file needs a top-level 'dance' list")
    actions: List[BaseMotionAction] = []
    for i, step in enumerate(data['dance']):
        if not isinstance(step, dict) or 'duration' not in step:
            raise ValueError(f"dance step {i} needs at least a 'duration'")
        unknown = set(step) - {'name', 'linear', 'angular', 'duration', 'repeat'}
        if unknown:
            raise ValueError(f'dance step {i} has unknown keys: {sorted(unknown)}')
        linear = float(step.get('linear', 0.0))
        angular = float(step.get('angular', 0.0))
        if linear and angular:
            kind = ArcAction
        elif linear:
            kind = DriveAction
        elif angular:
            kind = RotateAction
        else:
            kind = StopAction
        action = kind(linear=linear, angular=angular,
                      duration=float(step['duration']),
                      label=str(step.get('name', '')))
        actions.extend([action] * int(step.get('repeat', 1)))
    return actions
