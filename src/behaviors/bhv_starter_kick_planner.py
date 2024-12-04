from src.interfaces.IBehavior import IBehavior
from src.interfaces.IAgent import IAgent
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *
from src.behaviors.bhv_starter_clearball import ClearBall
from src.behaviors.bhv_starter_pass import Pass
from src.behaviors.bhv_starter_dribble import Dribble
from src.behaviors.bhv_starter_shoot import Shoot
from src.utils.tools import Tools

class BhvStarterKickPlanner(IBehavior):
    def __init__(self):
        self.shoot = Shoot()
        self.clear_ball = ClearBall()
        self.dribble = Dribble()
        self.pass_ball = Pass()

    def execute(self, agent: IAgent):
        agent.logger.debug("BhvStarterKickPlanner.execute")
        from src.sample_player_agent import SamplePlayerAgent  # Local import to avoid circular import
        actions = []
        actions += [shoot] if (shoot := self.shoot.execute(agent)) is not None else []
        opps = Tools.OpponentsFromSelf(agent)
        nearest_opp = opps[0] if opps else None
        nearest_opp_dist = nearest_opp.dist_from_self if nearest_opp else 1000.0
        
        if nearest_opp_dist < 10:
            actions += [passing] if (passing := self.pass_ball.execute(agent)) is not None else []
            
        actions += [dribble] if (dribble := self.dribble.execute(agent)) is not None else []
        
        if nearest_opp_dist > 2.5:
            actions.append(PlayerAction(body_hold_ball=Body_HoldBall()))

        actions.append(self.clear_ball.execute(agent))
        
        #Sending actions' queue
        for i in actions:
            if not i == []:
                agent.add_action(i)
