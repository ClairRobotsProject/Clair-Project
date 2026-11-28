"""TurtleBot3-sized robot dancing in Gazebo Fortress (Ignition Gazebo 6).

Uses the stand-in model in worlds/dance_floor.sdf, so it runs without the
turtlebot3_gazebo package. The Agent, Policy, Skill and Driver are the same
ones tb3_dance.launch.py uses.
"""

import os

from ament_index_python.packages import get_package_share_directory
from clair_agent.launch_common import dance_actions, dance_arguments
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

WORLD = 'dance_floor'


def generate_launch_description():
    world = os.path.join(
        get_package_share_directory('clair_agent'), 'worlds', f'{WORLD}.sdf')
    set_pose = f'/world/{WORLD}/set_pose'
    headless = LaunchConfiguration('headless')
    gui_config = os.path.join(
        get_package_share_directory('clair_agent'), 'config', 'gui.config')

    return LaunchDescription(dance_arguments() + [
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='Run the simulation server without the Gazebo window'),
        ExecuteProcess(
            cmd=['ign', 'gazebo', '-r', '--gui-config', gui_config, world],
            output='screen',
            condition=UnlessCondition(headless)),
        ExecuteProcess(
            cmd=['ign', 'gazebo', '-r', '-s', world], output='screen',
            condition=IfCondition(headless)),
        Node(
            package='ros_gz_bridge', executable='parameter_bridge', output='screen',
            arguments=[
                '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
                '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
                '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
                f'{set_pose}@ros_gz_interfaces/srv/SetEntityPose',
            ]),
    ] + dance_actions(reset_service=set_pose, reset_service_type='set_entity_pose'))
