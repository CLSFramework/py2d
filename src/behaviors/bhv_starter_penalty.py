
from src.interfaces.IAgent import IAgent
from src.utils.convertor import Convertor
from pyrusgeom.geom_2d import *
from pyrusgeom.soccer_math import *
from service_pb2 import *
from src.interfaces.IBehavior import IBehavior


class BhvStarterPenalty(IBehavior):
    def __init__(self):
        pass
    
    def execute(self, agent: IAgent) -> bool:
        agent.logger.debug("BhvStarterPenalty.execute")
        from src.sample_player_agent import SamplePlayerAgent  # Local import to avoid circular import
        assert isinstance(agent, SamplePlayerAgent)
        raise NotImplementedError("BhvStarterPenalty.execute not implemented")