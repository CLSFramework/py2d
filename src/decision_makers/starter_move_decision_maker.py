from src.interfaces.IDecisionMaker import IDecisionMaker
from src.interfaces.IAgent import IAgent
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from src.behaviors.starter_bhv_basic_move import BhvBasicMove


class StarterMoveDecisionMaker(IDecisionMaker):
    def __init__(self):
        pass
    
    def make_decision(self, agent: IAgent):
        # Queued actions are reversed and send here
        bhv_basic_move_actions = (BhvBasicMove.Decision(agent))
        for act in bhv_basic_move_actions:
            if act == None:
                continue
            agent.add_action(act)