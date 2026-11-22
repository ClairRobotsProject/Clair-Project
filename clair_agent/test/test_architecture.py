"""Unit tests for the ROS-free core: Policy -> Action -> Skill -> Driver."""

import os
import threading

import pytest

from clair_agent.actions import (
    ArcAction, DriveAction, RotateAction, StopAction)
from clair_agent.core import Action, Agent, Clock, ExecutionStatus, Policy
from clair_agent.drivers import DifferentialDriveDriver
from clair_agent.policies import ScriptedDancePolicy, parse_choreography
from clair_agent.skills import BaseMotionSkill

DANCE_YAML = os.path.join(os.path.dirname(__file__), '..', 'config', 'dance.yaml')


class FakeClock(Clock):

    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t

    def sleep(self, seconds):
        self.t += seconds


class FakeDriver(DifferentialDriveDriver):
    max_linear = 0.22
    max_angular = 2.84

    def __init__(self):
        self.commands = []

    def set_velocity(self, linear, angular):
        self.commands.append(self.clamp(linear, angular))


def make_agent(steps, clock=None):
    clock = clock or FakeClock()
    driver = FakeDriver()
    agent = Agent(ScriptedDancePolicy(steps),
                  [BaseMotionSkill(driver, clock, rate_hz=10.0)], clock=clock)
    return agent, driver, clock


def test_dance_runs_every_step_through_the_driver_and_stops():
    steps = [DriveAction(linear=0.1, duration=1.0),
             RotateAction(angular=1.0, duration=0.5),
             StopAction(duration=0.2)]
    agent, driver, clock = make_agent(steps)

    report = agent.run()

    assert report.ok
    assert [a for a, _ in report.steps] == steps
    assert all(r.status is ExecutionStatus.SUCCEEDED for _, r in report.steps)
    assert clock.t == pytest.approx(1.7)
    assert (0.1, 0.0) in driver.commands and (0.0, 1.0) in driver.commands
    assert driver.commands[-1] == (0.0, 0.0)


def test_skill_holds_velocity_for_the_duration_then_stops():
    clock, driver = FakeClock(), FakeDriver()
    skill = BaseMotionSkill(driver, clock, rate_hz=4.0)  # 0.25 s: exact in binary

    result = skill.execute(DriveAction(linear=0.1, duration=1.0), threading.Event())

    assert result.ok
    assert clock.t == pytest.approx(1.0)
    assert driver.commands[:-1] == [(0.1, 0.0)] * 4
    assert driver.commands[-1] == (0.0, 0.0)


def test_driver_clamps_to_robot_limits():
    agent, driver, _ = make_agent([ArcAction(linear=5.0, angular=-9.0, duration=0.1)])
    agent.run()
    assert driver.commands[0] == (0.22, -2.84)


def test_cancel_stops_the_robot_and_skips_remaining_steps():
    steps = [DriveAction(linear=0.1, duration=10.0),
             RotateAction(angular=1.0, duration=10.0)]
    agent, driver, clock = make_agent(steps)
    original_sleep = clock.sleep

    def sleep_then_cancel(seconds):
        original_sleep(seconds)
        if clock.t >= 1.0:
            agent.cancel()

    clock.sleep = sleep_then_cancel
    report = agent.run()

    assert report.status is ExecutionStatus.CANCELLED
    assert len(report.steps) == 1
    assert clock.t < 2.0
    assert driver.commands[-1] == (0.0, 0.0)
    assert (0.0, 1.0) not in driver.commands


def test_agent_can_run_again_after_reset():
    agent, driver, _ = make_agent([DriveAction(linear=0.1, duration=0.3)])
    first = agent.run()
    agent.reset()
    second = agent.run()
    assert first.ok and second.ok
    assert len(first.steps) == len(second.steps) == 1


def test_action_without_a_skill_fails_and_stops():
    class Wave(Action):
        pass

    class WavePolicy(Policy):
        def get_action(self, observation):
            return Wave()

    driver = FakeDriver()
    agent = Agent(WavePolicy(), [BaseMotionSkill(driver, FakeClock())])
    report = agent.run()

    assert report.status is ExecutionStatus.FAILED
    assert 'no skill' in report.message
    assert driver.commands == [(0.0, 0.0)]


def test_driver_error_is_reported_as_failure():
    class BrokenDriver(FakeDriver):
        def set_velocity(self, linear, angular):
            if linear:
                raise RuntimeError('link down')
            super().set_velocity(linear, angular)

    clock = FakeClock()
    agent = Agent(ScriptedDancePolicy([DriveAction(linear=0.1, duration=1.0)]),
                  [BaseMotionSkill(BrokenDriver(), clock)], clock=clock)
    report = agent.run()
    assert report.status is ExecutionStatus.FAILED
    assert 'link down' in report.message


def test_choreography_parsing_picks_action_types_and_repeats():
    actions = parse_choreography({'dance': [
        {'name': 'fwd', 'linear': 0.1, 'duration': 1},
        {'angular': 1.0, 'duration': 1, 'repeat': 2},
        {'linear': 0.1, 'angular': 1.0, 'duration': 1},
        {'duration': 0.5},
    ]})
    assert [type(a) for a in actions] == [
        DriveAction, RotateAction, RotateAction, ArcAction, StopAction]
    assert actions[0].label == 'fwd'


@pytest.mark.parametrize('bad', [
    {}, {'dance': 'spin'}, {'dance': [{'linear': 0.1}]},
    {'dance': [{'duration': 1, 'speed': 3}]}, {'dance': [{'duration': -1}]},
])
def test_choreography_parsing_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        parse_choreography(bad)


def test_default_dance_file_is_valid_and_within_burger_limits():
    policy = ScriptedDancePolicy.from_yaml(DANCE_YAML)
    assert len(policy) > 0
    while (action := policy.get_action(None)) is not None:
        assert abs(action.linear) <= 0.22
        assert abs(action.angular) <= 2.84


def test_policy_and_core_do_not_import_ros():
    import clair_agent.core
    import clair_agent.policies.dance_policy as dance_policy
    import pathlib
    sources = [pathlib.Path(dance_policy.__file__)]
    sources += pathlib.Path(clair_agent.core.__file__).parent.glob('*.py')
    for path in sources:
        text = path.read_text()
        for banned in ('rclpy', 'geometry_msgs', 'cmd_vel', 'gazebo'):
            assert banned not in text, f'{path.name} mentions {banned}'
