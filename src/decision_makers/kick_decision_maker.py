from src.interfaces.IDecisionMaker import IDecisionMaker
from src.interfaces.IAgent import IAgent
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *
from src.behaviors.bhv_kick_planner import BhvKickPlanner
from src.behaviors.bhv_starter_kick_planner import BhvStarterKickPlanner


class KickDecisionMaker(IDecisionMaker):
    def __init__(self):
        self.bhv_kick_planner = BhvKickPlanner()
        self.bhv_kick_planner = BhvStarterKickPlanner()

    def make_decision(self, agent: IAgent):
        agent.logger.debug("--- WithBallDecisionMaker ---")
        from src.sample_player_agent import SamplePlayerAgent  # Local import to avoid circular import
        assert isinstance(agent, SamplePlayerAgent)
        #self.bhv_kick_planner.execute(agent)
        self.bhv_kick_planner.execute(agent)
