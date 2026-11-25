#!/usr/bin/env bash
# Install the TurtleBot3 Gazebo simulation for ROS 2 Humble.
#
# Follows the ROBOTIS e-Manual (Quick Start > PC Setup, and Simulation):
#   https://emanual.robotis.com/docs/en/platform/turtlebot3/quick-start/
#   https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/
#
#   ./install_dependencies.sh            apt binaries of the TurtleBot3 packages
#   ./install_dependencies.sh --source   build them in ~/turtlebot3_ws, as the manual does
set -euo pipefail

source /opt/ros/humble/setup.bash

# Gazebo (Classic 11) and its ROS 2 integration.
sudo apt update
sudo apt install -y 'ros-humble-gazebo-*' python3-colcon-common-extensions

if [[ "${1:-}" == "--source" ]]; then
    mkdir -p ~/turtlebot3_ws/src
    cd ~/turtlebot3_ws/src
    for repo in DynamixelSDK turtlebot3_msgs turtlebot3 turtlebot3_simulations; do
        [[ -d $repo ]] || git clone -b humble "https://github.com/ROBOTIS-GIT/$repo.git"
    done
    cd ~/turtlebot3_ws
    colcon build --symlink-install
    echo "Built. Add to your shell:  source ~/turtlebot3_ws/install/setup.bash"
else
    sudo apt install -y ros-humble-turtlebot3 ros-humble-turtlebot3-msgs \
        ros-humble-turtlebot3-gazebo
fi

echo "Done. Next: scripts/run_mvp.sh"
