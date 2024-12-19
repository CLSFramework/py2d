from typing import TYPE_CHECKING
from src.interfaces.IDecisionMaker import IDecisionMaker
from service_pb2 import *
from src.behaviors.bhv_penalty import BhvPenalty
from src.behaviors.starter.bhv_starter_penalty import BhvStarterPenalty

if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent

class PenaltyDecisionMaker(IDecisionMaker):
    def __init__(self, agent: "SamplePlayerAgent"):
        self.bhv_penalty = BhvPenalty() if not agent.use_starter_code else BhvStarterPenalty()
    
    def make_decision(self, agent: "SamplePlayerAgent"):
        agent.logger.debug("PenaltyDecisionMaker.make_decision")
        self.bhv_penalty.execute(agent)