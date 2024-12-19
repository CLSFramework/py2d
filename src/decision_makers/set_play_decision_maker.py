from typing import TYPE_CHECKING
from src.interfaces.IDecisionMaker import IDecisionMaker
from service_pb2 import *
from src.behaviors.bhv_setplay import BhvSetPlay
from src.behaviors.starter.bhv_starter_setplay import BhvStarterSetPlay

if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent

class SetPlayDecisionMaker(IDecisionMaker):
    def __init__(self, agent: "SamplePlayerAgent"):
        self.bhv_setplay = BhvSetPlay() if not agent.use_starter_code else BhvStarterSetPlay()
    
    def make_decision(self, agent: "SamplePlayerAgent"):
        agent.logger.debug("SetPlayDecisionMaker.make_decision")
        self.bhv_setplay.execute(agent)