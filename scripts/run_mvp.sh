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
    classic)
        launch_file=tb3_dance.launch.py
        reset_cmd=(ros2 service call /reset_world std_srvs/srv/Empty) ;;
    fortress)
        launch_file=tb3_dance_fortress.launch.py
        reset_cmd=(ros2 service call /world/dance_floor/set_pose
                   ros_gz_interfaces/srv/SetEntityPose
                   "{entity: {name: turtlebot3_burger}, pose: {orientation: {w: 1.0}}}") ;;
esac

# Everything the simulation prints goes to a log file, not the terminal.
log_dir="$repo/logs"
mkdir -p "$log_dir"
log="$log_dir/${sim}_$(date +%Y-%m-%d_%H-%M-%S).log"
: >"$log"
ln -sfn "$(basename "$log")" "$log_dir/latest.log"

echo "Starting Gazebo ${sim^}. Log file: $log"
echo "Follow it live in another terminal:  tail -f $log_dir/latest.log"

# Start Gazebo and the bridge, without the Agent, in their own session and
# process group. Stopping that group later also stops every process Gazebo
# started, so no Gazebo server is left behind.
setsid ros2 launch clair_agent "$launch_file" start_agent:=false "$@" >>"$log" 2>&1 &
sim_pid=$!

stop_simulation() {
    if kill -0 -- -"$sim_pid" 2>/dev/null; then
        echo "Closing Gazebo..."
        kill -TERM -- -"$sim_pid" 2>/dev/null || true
        for _ in $(seq 20); do
            kill -0 -- -"$sim_pid" 2>/dev/null || break
            sleep 0.5
        done
        kill -KILL -- -"$sim_pid" 2>/dev/null || true
    fi
}
trap stop_simulation EXIT

# Ctrl+C reaches the running dance (the Agent stops the robot); this handler
# only records it, so the script can close Gazebo and exit cleanly.
interrupted=false
trap 'interrupted=true' INT

dance=0
while :; do
    dance=$((dance + 1))
    if ((dance > 1)); then
        "${reset_cmd[@]}" >>"$log" 2>&1 \
            || echo "  could not reset the robot's pose; dancing from where it stopped"
    fi
    echo
    echo "Dance $dance: running (Ctrl+C to stop)..."
    first_line=$(($(wc -l <"$log") + 1))
    ros2 launch clair_agent dance.launch.py shutdown_when_done:=true "$@" >>"$log" 2>&1 || true
    tail -n +"$first_line" "$log" \
        | grep -E "run [0-9]+: |not ready|\[ERROR\]" \
        | sed -E 's/.*\]: run [0-9]+: /  result: /; s/.*\]: /  /' \
        || echo "  no result found; see $log"
    $interrupted && break
    read -r -p "Dance again? [y/n] " answer || break
    $interrupted && break
    [[ "$answer" =~ ^[Yy] ]] || break
done
echo "Stopping. Log file: $log"
