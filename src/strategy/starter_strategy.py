from src.interfaces.IPositionStrategy import IPositionStrategy
from src.strategy.formation_file import *
from src.interfaces.IAgent import IAgent
from src.strategy.player_role import PlayerRole, RoleName, RoleType, RoleSide
from pyrusgeom.soccer_math import *
from service_pb2 import *
import logging


class StarterStrategy(IPositionStrategy):
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def update(self, agent: IAgent):
        raise NotImplementedError("StarterStrategy.update not implemented")
        pass
        
    def get_position(self, uniform_number, agent: IAgent) -> Vector2D:
        raise NotImplementedError("StarterStrategy.get_position not implemented")