#!/usr/bin/env python3
"""Design verification: keep the layers of the architecture apart.

Rules (from docs/robot-agent-architecture.md):
  * Core interfaces, Actions, Policies, Skills and the Driver base classes are
    robot- and simulator-agnostic: they must not import ROS or Gazebo code.
  * Only a Driver implementation may publish ``cmd_vel``; a Policy must not
    contain transport or simulator command code.

Exit status 1 and a list of violations when a rule is broken.
"""

import ast
import pathlib
import sys

PKG = pathlib.Path(__file__).resolve().parent.parent / 'clair_agent' / 'clair_agent'

FORBIDDEN_IMPORTS = ('rclpy', 'geometry_msgs', 'nav_msgs', 'sensor_msgs', 'std_srvs',
                     'ros_gz_interfaces', 'ros_gz_bridge', 'launch', 'launch_ros',
                     'ament_index_python')
# Packages that must stay free of ROS, and files inside them that are exempt.
PURE = ('core', 'actions', 'policies', 'skills')
PURE_FILES = ('drivers/differential_drive.py', 'drivers/__init__.py')
POLICY_FORBIDDEN_WORDS = ('cmd_vel', 'Twist', 'publish')


def imported_modules(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.lineno, node.module


def main() -> int:
    problems = []
    for path in sorted(PKG.rglob('*.py')):
        rel = path.relative_to(PKG).as_posix()
        pure = rel.split('/')[0] in PURE or rel in PURE_FILES
        source = path.read_text()
        if pure:
            for line, module in imported_modules(ast.parse(source, rel)):
                if module.split('.')[0] in FORBIDDEN_IMPORTS:
                    problems.append(f'{rel}:{line}: {module} is not allowed in the '
                                    'ROS-free layers')
        if rel.startswith('policies/'):
            for word in POLICY_FORBIDDEN_WORDS:
                if word in source:
                    problems.append(f'{rel}: a Policy must not contain {word!r}')
        if 'cmd_vel' in source and not rel.startswith(('drivers/', 'nodes/', 'launch_common')):
            problems.append(f'{rel}: only a Driver (or the node wiring) may touch cmd_vel')
    for problem in problems:
        print(problem)
    print('architecture check:', 'FAILED' if problems else 'ok')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
