"""TurtleBot3 dance in Gazebo, using the official TurtleBot3 simulation.

Equivalent to the ROBOTIS e-Manual command

    export TURTLEBOT3_MODEL=burger
    ros2 launch turtlebot3_gazebo empty_world.launch.py

followed by the dance Agent. Needs the turtlebot3_gazebo package.
"""

import os

from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from clair_agent.launch_common import dance_actions, dance_arguments
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    try:
        tb3_gazebo = get_package_share_directory('turtlebot3_gazebo')
    except PackageNotFoundError as exc:
        raise RuntimeError(
            'turtlebot3_gazebo is not installed. Run scripts/install_dependencies.sh, '
            'or use tb3_dance_fortress.launch.py, which needs only Gazebo Fortress.'
        ) from exc

    return LaunchDescription(dance_arguments() + [
        DeclareLaunchArgument('x_pose', default_value='0.0'),
        DeclareLaunchArgument('y_pose', default_value='0.0'),
        # turtlebot3_gazebo reads the model from the environment.
        SetEnvironmentVariable('TURTLEBOT3_MODEL', LaunchConfiguration('model')),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(tb3_gazebo, 'launch', 'empty_world.launch.py')),
            launch_arguments={
                'x_pose': LaunchConfiguration('x_pose'),
                'y_pose': LaunchConfiguration('y_pose'),
            }.items()),
    ] + dance_actions(reset_service='/reset_world', reset_service_type='empty'))
