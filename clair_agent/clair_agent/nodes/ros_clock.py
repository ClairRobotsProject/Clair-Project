"""Clock backed by a ROS node, so durations follow simulation time."""

import time

import rclpy
from rclpy.node import Node

from clair_agent.core import Clock


class RosClock(Clock):

    def __init__(self, node: Node):
        self._clock = node.get_clock()

    def now(self) -> float:
        return self._clock.now().nanoseconds * 1e-9

    def sleep(self, seconds: float) -> None:
        """Wait for ``seconds`` of ROS time.

        May return early if ROS time is paused or running slowly, so callers
        stay responsive to cancellation; they must re-check ``now()``.
        """
        target = self.now() + seconds
        wall_deadline = time.monotonic() + max(2.0 * seconds, 0.1)
        while rclpy.ok() and self.now() < target and time.monotonic() < wall_deadline:
            time.sleep(0.002)
