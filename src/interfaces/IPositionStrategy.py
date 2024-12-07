from abc import ABC, abstractmethod
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *
from src.interfaces.IAgent import IAgent


class IPositionStrategy(ABC):
    @abstractmethod
    def get_position(self, uniform_number, agent: IAgent) -> Vector2D:
        pass
    
    @abstractmethod
    def update(self, agent: IAgent):
        pass
    