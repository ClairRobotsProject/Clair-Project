"""Policy: decides *what* to do."""

from abc import ABC, abstractmethod
from typing import Optional

from .action import Action
from .observation import Observation


class Policy(ABC):
    """Chooses the next Action from an Observation.

    A Policy must not contain robot transport or simulator code; it only
    returns Actions. Returning ``None`` means the behavior is complete.
    """

    @abstractmethod
    def get_action(self, observation: Observation) -> Optional[Action]:
        ...

    def reset(self) -> None:
        """Return to the initial state so the behavior can run again."""
