from src.interfaces.IDecisionMaker import IDecisionMaker
from src.interfaces.IAgent import IAgent
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *

class NoBallDecisionMaker(IDecisionMaker):
    def __init__(self):
        pass
    
    def make_decision(self, agent: IAgent):
        agent.add_action(PlayerAction(helios_basic_move=HeliosBasicMove()))
        #agent.add_action(PlayerAction(neck_turn_to_ball=Neck_TurnToBall()))
        