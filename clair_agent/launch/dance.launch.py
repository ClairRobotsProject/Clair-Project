"""Start only the dance Agent. The simulation must already be running."""

from clair_agent.launch_common import dance_actions, dance_arguments
from launch import LaunchDescription


def generate_launch_description():
    return LaunchDescription(dance_arguments() + dance_actions())
