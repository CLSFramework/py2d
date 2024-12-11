from src.interfaces.IDecisionMaker import IDecisionMaker
from src.interfaces.IAgent import IAgent
from service_pb2 import *
from src.behaviors.bhv_setplay import BhvSetPlay
from src.behaviors.starter_setplay.bhv_starter_setplay import BhvStarterSetPlay


class SetPlayDecisionMaker(IDecisionMaker):
    def __init__(self):
        self.bhv_setplay = BhvSetPlay()
        #self.bhv_setplay = BhvStarterSetPlay()
    
    def make_decision(self, agent: IAgent):
        agent.logger.debug("SetPlayDecisionMaker.make_decision")
        from src.sample_player_agent import SamplePlayerAgent  # Local import to avoid circular import
        assert isinstance(agent, SamplePlayerAgent)
        self.bhv_setplay.execute(agent)