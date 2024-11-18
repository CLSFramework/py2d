from abc import ABC, abstractmethod
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *


class IPositionStrategy(ABC):
    @abstractmethod
    def get_position(self, uniform_number) -> Vector2D:
        pass
    
    @abstractmethod
    def update(self, wm: WorldModel):
        pass
    