"""MVP entry point: a TurtleBot3 dances through Policy -> Action -> Skill -> Driver."""

import os
import signal
import sys
import threading
import time

import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.executors import ExternalShutdownException, SingleThreadedExecutor
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from ros_gz_interfaces.srv import SetEntityPose
from std_srvs.srv import Empty

from clair_agent.core import Agent, ExecutionStatus
from clair_agent.drivers.turtlebot3_driver import TurtleBot3Driver
from clair_agent.policies import ScriptedDancePolicy
from clair_agent.sensors.ros_sensors import OdometrySensor, RGBCamera
from clair_agent.skills import BaseMotionSkill

from .ros_clock import RosClock


class DanceNode(Node):

    def __init__(self):
        super().__init__('dance_agent')
        default_dance = os.path.join(
            get_package_share_directory('clair_agent'), 'config', 'dance.yaml')
        model = self.declare_parameter(
            'model', os.environ.get('TURTLEBOT3_MODEL', 'burger')).value
        dance_file = self.declare_parameter('dance_file', '').value or default_dance
        cmd_vel_topic = self.declare_parameter('cmd_vel_topic', 'cmd_vel').value
        odom_topic = self.declare_parameter('odom_topic', 'odom').value
        stamped = self.declare_parameter('stamped_cmd_vel', False).value
        rate_hz = self.declare_parameter('command_rate_hz', 20.0).value
        use_camera = self.declare_parameter('use_camera', False).value
        camera_topic = self.declare_parameter('camera_topic', 'camera/image_raw').value
        self.runs = self.declare_parameter('runs', 1).value
        self.startup_timeout = self.declare_parameter('startup_timeout', 60.0).value
        # Service called between runs to put the robot back at its start pose.
        # '' disables it. Type is 'empty' (Gazebo Classic /reset_world) or
        # 'set_entity_pose' (ros_gz bridge of /world/<name>/set_pose, which moves
        # `reset_entity` to the origin; Fortress ignores a full world reset).
        self.reset_service = self.declare_parameter('reset_service', '').value
        self.reset_service_type = self.declare_parameter(
            'reset_service_type', 'empty').value
        self.reset_entity = self.declare_parameter(
            'reset_entity', 'turtlebot3_burger').value
        if self.reset_service_type not in ('empty', 'set_entity_pose'):
            raise ValueError(
                f'unknown reset_service_type {self.reset_service_type!r}')

        self.clock = RosClock(self)
        self.driver = TurtleBot3Driver(self, model, cmd_vel_topic, stamped)
        self.odom = OdometrySensor(self, odom_topic)
        sensors = [self.odom]
        if use_camera:
            sensors.append(RGBCamera(self, camera_topic))
        policy = ScriptedDancePolicy.from_yaml(dance_file)
        self.agent = Agent(
            policy=policy,
            skills=[BaseMotionSkill(self.driver, self.clock, rate_hz)],
            sensors=sensors, clock=self.clock, logger=self.get_logger())
        self.get_logger().info(
            f'TurtleBot3 {model}: {len(policy)} dance steps, '
            f'{policy.total_duration:.1f} s, from {dance_file}')

    def wait_until_ready(self, stop: threading.Event) -> bool:
        """Wait for the simulated robot: a cmd_vel listener, odometry, and a clock."""
        deadline = time.monotonic() + self.startup_timeout
        sim_time = self.get_parameter('use_sim_time').value
        while not stop.is_set() and time.monotonic() < deadline:
            missing = []
            if not self.driver.is_ready():
                missing.append('a subscriber on cmd_vel')
            if self.odom.read() is None:
                missing.append('odometry')
            if sim_time and self.clock.now() == 0.0:
                missing.append('/clock')
            if not missing:
                return True
            self.get_logger().info(
                'waiting for ' + ', '.join(missing), throttle_duration_sec=5.0)
            time.sleep(0.1)
        if not stop.is_set():
            self.get_logger().error(
                f'robot not ready after {self.startup_timeout:.0f} s; is the simulation running?')
        return False

    def reset_world(self) -> bool:
        if not self.reset_service:
            return True
        if self.reset_service_type == 'set_entity_pose':
            client = self.create_client(SetEntityPose, self.reset_service)
            request = SetEntityPose.Request()
            request.entity.name = self.reset_entity
            request.pose.orientation.w = 1.0
        else:
            client = self.create_client(Empty, self.reset_service)
            request = Empty.Request()
        try:
            if not client.wait_for_service(timeout_sec=5.0):
                self.get_logger().warn(
                    f'reset service {self.reset_service} unavailable; continuing without reset')
                return False
            future = client.call_async(request)
            deadline = time.monotonic() + 10.0
            while not future.done() and time.monotonic() < deadline:
                time.sleep(0.02)
            if not future.done():
                self.get_logger().warn(f'reset service {self.reset_service} timed out')
                return False
            if getattr(future.result(), 'success', True) is False:
                self.get_logger().warn(f'reset service {self.reset_service} refused')
                return False
            time.sleep(0.5)  # let the robot settle at its start pose
            self.get_logger().info(f'world reset via {self.reset_service}')
            return True
        finally:
            self.destroy_client(client)

    def log_pose(self, prefix: str) -> None:
        pose = self.odom.read()
        if pose is not None:
            self.get_logger().info(
                f'{prefix} pose: x={pose.x:+.3f} m, y={pose.y:+.3f} m, yaw={pose.yaw:+.3f} rad')

    def dance(self) -> ExecutionStatus:
        status = ExecutionStatus.SUCCEEDED
        for run in range(1, self.runs + 1):
            if run > 1:
                self.reset_world()
            self.agent.reset()
            self.get_logger().info(f'=== dance run {run}/{self.runs} ===')
            self.log_pose('start')
            report = self.agent.run()
            self.log_pose('end')
            self.get_logger().info(
                f'run {run}: {report.status.value} - {report.message}')
            status = report.status
            if not report.ok:
                break
        return status


def main(args=None):
    # We handle signals ourselves so the robot is stopped before ROS shuts down.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = DanceNode()
    stop = threading.Event()

    def on_signal(signum, frame):
        node.get_logger().info('cancel requested; stopping the robot')
        stop.set()
        node.agent.cancel()

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    executor = SingleThreadedExecutor()
    executor.add_node(node)

    def spin():
        try:
            executor.spin()
        except ExternalShutdownException:
            pass

    spinner = threading.Thread(target=spin, daemon=True)
    spinner.start()

    status = ExecutionStatus.FAILED
    try:
        if node.wait_until_ready(stop):
            status = node.dance()
        elif stop.is_set():
            status = ExecutionStatus.CANCELLED
    finally:
        # Repeat the stop so it lands even if one message is dropped.
        for _ in range(5):
            node.driver.stop()
            time.sleep(0.05)
        executor.shutdown()
        spinner.join(timeout=2.0)  # the spin thread must be gone before teardown
        node.destroy_node()
        rclpy.shutdown()
    return 0 if status is ExecutionStatus.SUCCEEDED else 1


if __name__ == '__main__':
    sys.exit(main())
