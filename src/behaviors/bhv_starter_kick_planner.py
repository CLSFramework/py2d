from src.interfaces.IBehavior import IBehavior
from src.interfaces.IAgent import IAgent
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *
from src.behaviors.bhv_starter_clearball import BhvStarterClearBall
from src.behaviors.bhv_starter_pass import BhvStarterPass
from src.behaviors.bhv_starter_dribble import BhvStarterDribble
from src.behaviors.bhv_starter_shoot import BhvStarterShoot
from src.utils.tools import Tools

class BhvStarterKickPlanner(IBehavior):
    def __init__(self):
        self.starter_shoot = BhvStarterShoot()
        self.starter_clear_ball = BhvStarterClearBall()
        self.starter_dribble = BhvStarterDribble()
        self.starter_pass = BhvStarterPass()

    def execute(self, agent: IAgent):
        agent.logger.debug("BhvStarterKickPlanner.execute")
        self.starter_shoot.execute(agent)
        opps = Tools.get_opponents_from_self(agent)
        nearest_opp = opps[0] if opps else None
        nearest_opp_dist = nearest_opp.dist_from_self if nearest_opp else 1000.0
        
        if nearest_opp_dist < 10:
            self.starter_pass.execute(agent)
            
        self.starter_dribble.execute(agent)
        
        if nearest_opp_dist > 2.5:
            agent.add_action(PlayerAction(body_hold_ball=Body_HoldBall()))

        self.starter_clear_ball.execute(agent)
