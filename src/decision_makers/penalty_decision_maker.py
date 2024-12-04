from src.interfaces.IDecisionMaker import IDecisionMaker
from src.interfaces.IAgent import IAgent
from service_pb2 import *
from src.behaviors.bhv_penalty import BhvPenalty
from src.behaviors.bhv_starter_penalty import BhvStarterPenalty


class PenaltyDecisionMaker(IDecisionMaker):
    def __init__(self):
        self.bhv_penalty = BhvPenalty()
        # self.bhv_penalty = BhvStarterPenalty()
    
    def make_decision(self, agent: IAgent):
        agent.logger.debug("PenaltyDecisionMaker.make_decision")
        from src.sample_player_agent import SamplePlayerAgent  # Local import to avoid circular import
        assert isinstance(agent, SamplePlayerAgent)
        self.bhv_penalty.execute(agent)