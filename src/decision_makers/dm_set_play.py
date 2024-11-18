from src.interfaces.IDecisionMaker import IDecisionMaker
from src.interfaces.IAgent import IAgent
from service_pb2 import *


class SetPlayDecisionMaker(IDecisionMaker):
    def __init__(self):
        pass
    
    def make_decision(self, agent: IAgent, wm: WorldModel):
        agent.add_action(PlayerAction(helios_set_play=HeliosSetPlay()))