"""Action: what a Policy asks the robot to do, free of transport details."""

from abc import ABC


class Action(ABC):
    """Base class for every request a Policy can make.

    Concrete actions are plain data (see ``clair_agent.actions``). They carry
    no ROS types, so a Policy never depends on how the action is executed.
    """

    @property
    def name(self) -> str:
        return type(self).__name__
