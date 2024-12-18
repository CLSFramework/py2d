from abc import ABC, abstractmethod
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *
from src.interfaces.IAgent import IAgent


class IPositionStrategy(ABC):
    @abstractmethod
    def get_position(self, uniform_number, agent: IAgent) -> Vector2D:
        """
        Get the position for a given uniform number.

        Args:
            uniform_number (int): The uniform number of the player.
            agent (IAgent): The agent instance.

        Returns:
            Vector2D: The position of the player.
        """
        pass
    
    @abstractmethod
    def update(self, agent: IAgent):
        """
        Update the strategy based on the agent's world model.

        Args:
            agent (IAgent): The agent instance.
        """
        pass
