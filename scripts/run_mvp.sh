#!/usr/bin/env bash
# Build the workspace and run the TurtleBot3 dance MVP.
#
#   scripts/run_mvp.sh                 official TurtleBot3 simulation if installed,
#                                      otherwise the Gazebo Fortress stand-in
#   scripts/run_mvp.sh fortress        force the Gazebo Fortress stand-in
#   scripts/run_mvp.sh classic runs:=3 extra arguments go to ros2 launch
#
# Expects this repository inside the src/ folder of a colcon workspace.
set -eo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ws="$(cd "$repo/../.." && pwd)"
if [[ "$(basename "$(dirname "$repo")")" != "src" ]]; then
    echo "Clone this repository into <workspace>/src first (see README)." >&2
    exit 1
fi

source /opt/ros/humble/setup.bash
[[ -f /usr/share/gazebo/setup.sh ]] && source /usr/share/gazebo/setup.sh
[[ -f ~/turtlebot3_ws/install/setup.bash ]] && source ~/turtlebot3_ws/install/setup.bash

cd "$ws"
colcon build --symlink-install --packages-select clair_agent
source install/setup.bash

export TURTLEBOT3_MODEL="${TURTLEBOT3_MODEL:-burger}"

sim="${1:-auto}"
[[ $# -gt 0 ]] && shift
if [[ "$sim" == "auto" ]]; then
    if ros2 pkg prefix turtlebot3_gazebo >/dev/null 2>&1; then sim=classic; else sim=fortress; fi
fi
case "$sim" in
    classic)  exec ros2 launch clair_agent tb3_dance.launch.py "$@" ;;
    fortress) exec ros2 launch clair_agent tb3_dance_fortress.launch.py "$@" ;;
    *) echo "unknown simulator '$sim' (use classic or fortress)" >&2; exit 1 ;;
esac
