"""TurtleBot3 adapter: the only place that knows about ``cmd_vel``."""

from geometry_msgs.msg import Twist, TwistStamped
from rclpy.node import Node

from .differential_drive import DifferentialDriveDriver

# Velocity limits from the TurtleBot3 specifications (m/s, rad/s).
TURTLEBOT3_LIMITS = {
    'burger': (0.22, 2.84),
    'waffle': (0.26, 1.82),
    'waffle_pi': (0.26, 1.82),
}


class TurtleBot3Driver(DifferentialDriveDriver):
    """Publishes velocity commands to a real or simulated TurtleBot3.

    ``stamped=True`` publishes ``TwistStamped`` instead of ``Twist`` for
    bringups that expect it; the Humble Gazebo simulation uses ``Twist``.
    """

    def __init__(self, node: Node, model: str = 'burger',
                 topic: str = 'cmd_vel', stamped: bool = False):
        if model not in TURTLEBOT3_LIMITS:
            raise ValueError(
                f'unknown TurtleBot3 model {model!r}; '
                f'expected one of {sorted(TURTLEBOT3_LIMITS)}')
        self.model = model
        self.max_linear, self.max_angular = TURTLEBOT3_LIMITS[model]
        self._node = node
        self._stamped = stamped
        self._pub = node.create_publisher(
            TwistStamped if stamped else Twist, topic, 10)

    def set_velocity(self, linear: float, angular: float) -> None:
        linear, angular = self.clamp(linear, angular)
        twist = Twist()
        twist.linear.x = float(linear)
        twist.angular.z = float(angular)
        if self._stamped:
            msg = TwistStamped()
            msg.header.stamp = self._node.get_clock().now().to_msg()
            msg.header.frame_id = 'base_link'
            msg.twist = twist
            self._pub.publish(msg)
        else:
            self._pub.publish(twist)

    def is_ready(self) -> bool:
        return self._pub.get_subscription_count() > 0
