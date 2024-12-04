from src.interfaces.IBehavior import IBehavior
from src.interfaces.IAgent import IAgent
from src.utils.tools import Tools
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.sector_2d import Sector2D
from service_pb2 import *


class Dribble(IBehavior):

    def __init__(self):
        pass

    def execute(self, agent: IAgent):
        wm = agent.wm
        ball_pos = Vector2D(wm.ball.position.x, wm.ball.position.y)
        dribble_angle = (Vector2D(52.5, 0) - ball_pos).th().degree()
        dribble_speed = 0.8
        dribble_threshold = 0.7
        dribble_sector = Sector2D(ball_pos, 0, 3, dribble_angle - 15, dribble_angle + 15)
        
        if not Tools.ExistOpponentIn(agent , dribble_sector):
            Target = Vector2D.polar2vector(3, dribble_angle) + ball_pos
            return PlayerAction(body_smart_kick=Body_SmartKick(target_point=RpcVector2D(x=Target.x(), y=Target.y()),
                                                                first_speed=dribble_speed,
                                                                    first_speed_threshold=dribble_threshold,
                                                                        max_steps=2))
        return


    


