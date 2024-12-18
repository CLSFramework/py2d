from src.interfaces.IBehavior import IBehavior
from src.interfaces.IAgent import IAgent
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from src.utils.tools import Tools
from service_pb2 import *


class BhvStarterPass():

    def __init__(self):
        pass

    def execute(self, agent: IAgent) -> PlayerAction:
        
        wm = agent.wm
        target = []
        ball_pos = Vector2D(wm.ball.position.x, wm.ball.position.y)
        self_pos = Vector2D(wm.self.position.x, wm.self.position.y)
        for i in wm.teammates :
            if i == None or i.uniform_number == wm.self.uniform_number or i.uniform_number < 0:
                continue
            tm_pos = Vector2D(i.position.x, i.position.y)
            if tm_pos.dist(ball_pos) > 30.0 :
                continue
            if self_pos.dist(tm_pos) < 2.0:
                continue
            check_root = Sector2D(ball_pos, 1.0, tm_pos.dist(ball_pos) + 3.0, (tm_pos - ball_pos).th().degree() - 15.0, (tm_pos - ball_pos).th().degree() + 15.0)
            if not Tools.exist_opponent_in(agent, check_root):
                target.append(i)
                
        if not target == []:
            best_target = target[0]
            for i in target:
                if i.position.x > best_target.position.x:
                    best_target = i
            if not wm.game_mode_type == GameModeType.PlayOn:
                return PlayerAction(body_smart_kick=Body_SmartKick(target_point=best_target.position, first_speed=2.7, first_speed_threshold=2.5, max_steps=1))
            else :
                return PlayerAction(body_smart_kick=Body_SmartKick(target_point=best_target.position, first_speed=2.5, first_speed_threshold=2.5, max_steps=1))
        
        return
                
