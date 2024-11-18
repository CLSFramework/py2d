# from pyparsing import col
from src.interfaces.IDecisionMaker import IDecisionMaker
from src.interfaces.IAgent import IAgent
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *


class WithBallDecisionMaker(IDecisionMaker):
    def __init__(self):
        pass
    
    def make_decision(self, agent: IAgent):
        agent.add_action(PlayerAction(helios_offensive_planner=HeliosOffensivePlanner(lead_pass=True,
                                                                                  direct_pass=True,
                                                                                  through_pass=True,
                                                                                  simple_pass=True,
                                                                                  short_dribble=True,
                                                                                  long_dribble=True,
                                                                                  simple_shoot=True,
                                                                                  simple_dribble=True,
                                                                                  cross=True)))