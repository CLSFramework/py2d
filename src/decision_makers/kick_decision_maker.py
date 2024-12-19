from typing import TYPE_CHECKING
from src.interfaces.IDecisionMaker import IDecisionMaker
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *
from src.behaviors.bhv_kick_planner import BhvKickPlanner
from src.behaviors.starter.bhv_starter_kick_planner import BhvStarterKickPlanner

if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent

class KickDecisionMaker(IDecisionMaker):
    def __init__(self, agent: "SamplePlayerAgent"):
        self.bhv_kick_planner = BhvKickPlanner() if not agent.use_starter_code else BhvStarterKickPlanner()

    def make_decision(self, agent: "SamplePlayerAgent"):
        agent.logger.debug("--- WithBallDecisionMaker ---")
        self.bhv_kick_planner.execute(agent)