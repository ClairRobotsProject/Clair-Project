#!/usr/bin/env bash
# Build the workspace and run the TurtleBot3 dance MVP.
#
#   scripts/run_mvp.sh                 Gazebo Fortress stand-in (default)
#   scripts/run_mvp.sh classic         official TurtleBot3 simulation (Gazebo Classic)
#   scripts/run_mvp.sh runs:=3         extra arguments go to ros2 launch
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

# Gazebo Fortress is the default; pass "classic" for the official TurtleBot3 simulation.
sim=fortress
case "${1:-}" in
    classic|fortress) sim="$1"; shift ;;
esac
case "$sim" in
    classic)  launch_file=tb3_dance.launch.py ;;
    fortress) launch_file=tb3_dance_fortress.launch.py ;;
esac

# The simulation's output goes to a log file, not the terminal.
# CLAIR_LOG_TO_SCREEN=1 scripts/run_mvp.sh shows it in the terminal instead.
if [[ "${CLAIR_LOG_TO_SCREEN:-0}" == 1 ]]; then
    exec ros2 launch clair_agent "$launch_file" "$@"
fi

log_dir="$repo/logs"
mkdir -p "$log_dir"
log="$log_dir/${sim}_$(date +%Y-%m-%d_%H-%M-%S).log"
ln -sfn "$(basename "$log")" "$log_dir/latest.log"

echo "Running the dance in Gazebo ${sim^}."
echo "Log file: $log"
echo "Follow it live in another terminal:  tail -f $log_dir/latest.log"
echo "Press Ctrl+C to stop."

# Ctrl+C still reaches ros2 launch (so it stops the robot and Gazebo); this
# handler only keeps the script alive long enough to print the summary.
trap ':' INT
status=0
ros2 launch clair_agent "$launch_file" "$@" >"$log" 2>&1 || status=$?

echo
echo "Simulation stopped (exit code $status). Summary:"
grep -E "dance run|run [0-9]+: |not ready|\[ERROR\]" "$log" \
    || echo "  no summary lines found; see $log"
exit "$status"
