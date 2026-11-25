"""Launch pieces shared by the package's launch files."""

from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import EnvironmentVariable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def dance_arguments():
    return [
        DeclareLaunchArgument(
            'model',
            default_value=EnvironmentVariable('TURTLEBOT3_MODEL', default_value='burger'),
            description='TurtleBot3 model: burger, waffle or waffle_pi'),
        DeclareLaunchArgument(
            'dance_file', default_value='',
            description='Choreography YAML; empty uses config/dance.yaml'),
        DeclareLaunchArgument(
            'runs', default_value='1', description='How many times to perform the dance'),
        DeclareLaunchArgument(
            'use_camera', default_value='false',
            description='Attach the RGB camera Sensor (waffle_pi only)'),
        DeclareLaunchArgument(
            'shutdown_when_done', default_value='false',
            description='Shut the whole launch down when the dance ends'),
    ]


def dance_actions(reset_service='', reset_service_type='empty'):
    """The dance Agent node, plus an optional shutdown when it exits."""
    node = Node(
        package='clair_agent', executable='dance_agent', name='dance_agent',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'model': LaunchConfiguration('model'),
            'dance_file': LaunchConfiguration('dance_file'),
            'runs': ParameterValue(LaunchConfiguration('runs'), value_type=int),
            'use_camera': ParameterValue(
                LaunchConfiguration('use_camera'), value_type=bool),
            'reset_service': reset_service,
            'reset_service_type': reset_service_type,
        }])
    shutdown = RegisterEventHandler(
        OnProcessExit(
            target_action=node,
            on_exit=[EmitEvent(event=Shutdown(reason='dance finished'))]),
        condition=IfCondition(LaunchConfiguration('shutdown_when_done')))
    return [node, shutdown]
