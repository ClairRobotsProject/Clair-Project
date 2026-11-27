#!/usr/bin/env bash
# Install what the TurtleBot3 dance MVP needs on ROS 2 Humble.
#
#   scripts/install_dependencies.sh                   Gazebo Fortress (default)
#   scripts/install_dependencies.sh classic           also the official TurtleBot3
#                                                     simulation (Gazebo Classic 11)
#   scripts/install_dependencies.sh classic --source  build the TurtleBot3 packages in
#                                                     ~/turtlebot3_ws, as the ROBOTIS
#                                                     e-Manual does
#
# Fortress packages that are already installed are skipped, so on a machine
# that already has them the default run needs no sudo.
set -eo pipefail   # no -u: the ROS setup scripts read unset variables

source /opt/ros/humble/setup.bash

classic=false
from_source=false
for arg in "$@"; do
    case "$arg" in
        classic)  classic=true ;;
        --source) classic=true; from_source=true ;;
        *) echo "unknown argument '$arg' (use: classic, --source)" >&2; exit 1 ;;
    esac
done

# --- Gazebo Fortress (default) ---------------------------------------------
missing=()
for pkg in ros_gz_bridge ros_gz_interfaces; do
    if ! ros2 pkg prefix "$pkg" >/dev/null 2>&1; then
        missing=(ros-humble-ros-gz)
    fi
done
command -v colcon >/dev/null 2>&1 || missing+=(python3-colcon-common-extensions)

if ((${#missing[@]})); then
    sudo apt update
    sudo apt install -y "${missing[@]}"
else
    echo "Gazebo Fortress dependencies are already installed."
fi

if ! command -v ign >/dev/null 2>&1; then
    echo "Warning: the 'ign' command (Gazebo Fortress) was not found." >&2
    echo "Install Gazebo Fortress: https://gazebosim.org/docs/fortress/install_ubuntu" >&2
fi

# --- Optional: Gazebo Classic and the official TurtleBot3 simulation --------
if $classic; then
    sudo apt update
    sudo apt install -y 'ros-humble-gazebo-*'
    if $from_source; then
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
fi

echo "Done. Next: scripts/run_mvp.sh"