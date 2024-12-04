from src.interfaces.IBehavior import IBehavior
from src.interfaces.IAgent import IAgent
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *


class BhvStarterKickPlanner(IBehavior):
    def __init__(self):
        pass

    def execute(self, agent: IAgent):
        agent.logger.debug("BhvStarterKickPlanner.execute")
        from src.sample_player_agent import SamplePlayerAgent  # Local import to avoid circular import
        assert isinstance(agent, SamplePlayerAgent)
        raise NotImplementedError("BhvStarterKickPlanner.execute not implemented")
