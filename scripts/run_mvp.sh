#!/usr/bin/env bash
# Build the workspace and run the TurtleBot3 dance MVP.
#
#   scripts/run_mvp.sh                 official TurtleBot3 simulation if installed,
#                                      otherwise the Gazebo Fortress stand-in
#   scripts/run_mvp.sh fortress        force the Gazebo Fortress stand-in
#   scripts/run_mvp.sh classic runs:=3 extra arguments go to ros2 launch
#
# The repository can live anywhere. Set COLCON_WS to use a particular
# colcon workspace; otherwise an enclosing <workspace>/src tree is detected
# (your home directory is never used as a workspace), or a private workspace
# is created under ~/.cache/clair_agent_ws.
set -eo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"

build_paths=()
if [[ -n "${COLCON_WS:-}" ]]; then
    mkdir -p "$COLCON_WS"
    ws="$(cd "$COLCON_WS" && pwd -P)"

    # Include the selected workspace's other source packages, if present.
    if [[ -d "$ws/src" ]]; then
        build_paths+=("$ws/src")
    fi
    # Also include this repository when it is not already under workspace/src.
    case "$repo/" in
        "$ws/src/"*) ;;
        *) build_paths+=("$repo") ;;
    esac
else
    # Walk upward and use the nearest enclosing colcon-style workspace whose
    # src directory contains this repository.
    candidate="$repo"
    ws=""
    while :; do
        if [[ -d "$candidate/src" && "$candidate" != "$HOME" && "$repo/" == "$candidate/src/"* ]]; then
            ws="$candidate"
            break
        fi
        [[ "$candidate" == "/" ]] && break
        candidate="$(dirname "$candidate")"
    done

    if [[ -z "$ws" ]]; then
        # No enclosing workspace: keep build/install/log outside the repository.
        ws="${XDG_CACHE_HOME:-$HOME/.cache}/clair_agent_ws"
        mkdir -p "$ws"
        build_paths+=("$repo")
    fi
fi

source /opt/ros/humble/setup.bash
[[ -f /usr/share/gazebo/setup.sh ]] && source /usr/share/gazebo/setup.sh
[[ -f "$HOME/turtlebot3_ws/install/setup.bash" ]] && source "$HOME/turtlebot3_ws/install/setup.bash"

echo "Using colcon workspace: $ws"
cd "$ws"
if ((${#build_paths[@]})); then
    colcon build --symlink-install --base-paths "${build_paths[@]}" --packages-select clair_agent
else
    colcon build --symlink-install --packages-select clair_agent
fi
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
