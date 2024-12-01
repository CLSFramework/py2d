from src.interfaces.IDecisionMaker import IDecisionMaker
from src.interfaces.IAgent import IAgent
from service_pb2 import *


class PenaltyDecisionMaker(IDecisionMaker):
    def __init__(self):
        pass
    
    def make_decision(self, agent: IAgent):
        agent.add_action(PlayerAction(helios_penalty=HeliosPenalty()))