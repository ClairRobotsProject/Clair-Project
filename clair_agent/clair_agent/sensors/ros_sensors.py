"""ROS 2-backed Sensors."""

import math
import threading
from typing import Optional

import numpy as np
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

from clair_agent.core import Observation, Sensor

from .observations import OdometryObservation, RGBObservation


def _seconds(stamp) -> float:
    return stamp.sec + stamp.nanosec * 1e-9


class _TopicSensor(Sensor):
    """Keeps the latest converted message from one topic."""

    def __init__(self, node: Node, name: str, msg_type, topic: str, qos):
        super().__init__(name)
        self._lock = threading.Lock()
        self._latest: Optional[Observation] = None
        self._sub = node.create_subscription(msg_type, topic, self._on_msg, qos)

    def _convert(self, msg) -> Optional[Observation]:
        raise NotImplementedError

    def _on_msg(self, msg) -> None:
        observation = self._convert(msg)
        if observation is not None:
            with self._lock:
                self._latest = observation

    def read(self) -> Optional[Observation]:
        with self._lock:
            return self._latest


class OdometrySensor(_TopicSensor):

    def __init__(self, node: Node, topic: str = 'odom', name: str = 'odom'):
        super().__init__(node, name, Odometry, topic, 10)

    def _convert(self, msg: Odometry) -> OdometryObservation:
        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                         1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        return OdometryObservation(
            stamp=_seconds(msg.header.stamp), x=p.x, y=p.y, yaw=yaw,
            linear=msg.twist.twist.linear.x, angular=msg.twist.twist.angular.z)


class RGBCamera(_TopicSensor):
    """RGB camera, e.g. the one on a TurtleBot3 Waffle Pi (640 x 480)."""

    def __init__(self, node: Node, topic: str = 'camera/image_raw',
                 name: str = 'rgb_camera'):
        super().__init__(node, name, Image, topic, qos_profile_sensor_data)
        self._node = node

    def _convert(self, msg: Image) -> Optional[RGBObservation]:
        if msg.encoding not in ('rgb8', 'bgr8'):
            self._node.get_logger().warn(
                f'{self.name}: unsupported encoding {msg.encoding!r}',
                throttle_duration_sec=5.0)
            return None
        rows = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.step)
        image = rows[:, :msg.width * 3].reshape(msg.height, msg.width, 3)
        if msg.encoding == 'bgr8':
            image = image[:, :, ::-1]
        return RGBObservation(stamp=_seconds(msg.header.stamp), image=image,
                              width=msg.width, height=msg.height)
