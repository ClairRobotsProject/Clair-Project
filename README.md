# Clair-Project

A modular robot-control architecture that separates decision-making (**Policy**),
executable behavior (**Skill**), robot adapters (**Driver**) and sensing (**Sensor**),
coordinated by an **Agent**. The design is in
[docs/robot-agent-architecture.md](docs/robot-agent-architecture.md).

This repository currently holds the **MVP: a TurtleBot3 performs a dance in Gazebo**
through the architecture, on ROS 2 Humble.

## Quick start

```bash
# 1. Clone the repository anywhere
git clone https://github.com/ClairRobotsProject/Clair-Project.git
cd Clair-Project


# 2. Install the dependencies (once; Gazebo Fortress by default, add "classic"
#    for the official TurtleBot3 simulation)
scripts/install_dependencies.sh

# 3. Build and run the dance
scripts/run_mvp.sh
```
The simulation's output is written to logs/<simulator>_<date>.log (and logs/latest.log), not the terminal. Set CLAIR_LOG_TO_SCREEN=1 to see it in the terminal.

run_mvp.sh runs the Gazebo Fortress stand-in by default. Pass classic to use the official TurtleBot3 simulation instead (needs turtlebot3_gazebo) (see [Simulators](#simulators)).
After each dance, run_mvp.sh asks whether to dance again. Yes puts the robot back at its start pose and repeats; no closes Gazebo

It builds with colcon in the first of these that applies, and prints which one it used:

1. the workspace named by the `COLCON_WS` environment variable;
2. the workspace whose `src/` folder contains the repository, if there is one
   (your home directory never counts);
3. a private workspace in `~/.cache/clair_agent_ws`.

### The same thing by hand

These are the commands from the ROBOTIS e-Manual
([PC setup](https://emanual.robotis.com/docs/en/platform/turtlebot3/quick-start/),
[simulation](https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/)),
plus the dance Agent.

```bash
# Terminal 1: TurtleBot3 in an empty Gazebo world
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo empty_world.launch.py

# Terminal 2: the Agent (run from the repository root; build/, install/ and log/
# are created there and are git-ignored)
cd Clair-Project && colcon build --symlink-install && source install/setup.bash
ros2 launch clair_agent dance.launch.py
```

Or both in one command:

```bash
ros2 launch clair_agent tb3_dance_fortress.launch.py
```

Press Ctrl-C at any time; the Agent stops the robot before it exits.

### Launch arguments

| Argument | Default | Meaning |
| --- | --- | --- |
| `model` | `$TURTLEBOT3_MODEL` or `burger` | `burger`, `waffle` or `waffle_pi`; sets the velocity limits |
| `dance_file` | `config/dance.yaml` | Choreography to perform |
| `runs` | `1` | Perform the dance this many times, resetting the robot's pose in between |
| `use_camera` | `false` | Attach the RGB camera Sensor (`waffle_pi`) |
| `shutdown_when_done` | `false` | Close the simulation when the dance ends |
| `headless` | `false` | Fortress launch only: no Gazebo window |

## Simulators

| Launch file | Simulator | Robot model | Needs |
| --- | --- | --- | --- |
| `tb3_dance.launch.py` | Gazebo Classic 11 | Official ROBOTIS TurtleBot3 | `turtlebot3_gazebo` |
| `tb3_dance_fortress.launch.py` | Gazebo Fortress | Stand-in with Burger wheel geometry | `ros_gz_sim`, `ros_gz_bridge` |

Both expose `cmd_vel`, `odom` and `/clock`, so the Agent code is identical. The
Fortress stand-in ([worlds/dance_floor.sdf](clair_agent/worlds/dance_floor.sdf)) is
a box on two wheels with the Burger's wheel radius and separation; it is not the
ROBOTIS model.

In Fortress the between-runs reset moves the robot back to the origin but does not
zero its wheel odometry, so logged poses keep accumulating across runs.

## How the dance maps onto the architecture

```
ScriptedDancePolicy --Action--> Agent --execute--> BaseMotionSkill --set_velocity--> TurtleBot3Driver --cmd_vel--> Gazebo
        ^                         |
        +------Observation--------+<------ OdometrySensor / RGBCamera <---- odom, camera/image_raw
```

| Architecture element | Class | File |
| --- | --- | --- |
| Agent | `Agent` | `clair_agent/core/agent.py` |
| Policy | `Policy` → `ScriptedDancePolicy` | `core/policy.py`, `policies/dance_policy.py` |
| Action | `Action` → `BaseMotionAction` → `DriveAction`, `RotateAction`, `ArcAction`, `StopAction` | `core/action.py`, `actions/base_motion.py` |
| Skill | `Skill` → `BaseMotionSkill` | `core/skill.py`, `skills/base_motion_skill.py` |
| Driver | `Driver` → `DifferentialDriveDriver` → `TurtleBot3Driver` | `core/driver.py`, `drivers/` |
| Sensor | `Sensor` → `OdometrySensor`, `RGBCamera` | `core/sensor.py`, `sensors/ros_sensors.py` |
| Observation | `Observation` → `OdometryObservation`, `RGBObservation` | `core/observation.py`, `sensors/observations.py` |

`clair_agent/core`, the actions and the policy import no ROS code. Only
`TurtleBot3Driver`, the ROS sensors and `nodes/dance_node.py` do, and
`TurtleBot3Driver` is the only place that publishes `cmd_vel`.

Decisions taken where the design document left a choice open:

- `Skill.execute` **blocks** until the action completes, fails or is cancelled, and
  returns an `ExecutionResult` (`succeeded`, `cancelled`, `failed`).
- An Agent holds **one** Policy. `Policy.get_action` returning `None` ends the run.
- The Agent hands the Policy a `CompositeObservation` holding the latest reading of
  every Sensor by name; a Sensor with no data yet reads as `None`.
- Durations follow **simulation time**, so the dance is the same at any real-time factor.

## Changing the dance

Edit [clair_agent/config/dance.yaml](clair_agent/config/dance.yaml) or pass your own
file with `dance_file:=/path/to/dance.yaml`:

```yaml
dance:
  - {name: step forward, linear: 0.15, duration: 2.0}   # m/s, seconds
  - {name: spin,         angular: 2.0, duration: 3.14}  # rad/s
  - {name: pause,        duration: 0.5, repeat: 2}
```

## Tests

```bash
cd clair_agent && python3 -m pytest test        # no ROS or simulator needed
```

The tests drive the Agent with a fake Driver and clock and cover the full
Policy → Action → Skill → Driver path, velocity clamping, cancellation, repeat
runs, failure reporting and choreography parsing.

## Next

The POC (pick and place with a simulated UR arm) adds manipulation Actions, Skills
and an arm Driver on the same core classes. It is not started.
