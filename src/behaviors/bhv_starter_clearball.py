from src.interfaces.IBehavior import IBehavior
from src.interfaces.IAgent import IAgent
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from src.utils.tools import Tools
from pyrusgeom import vector_2d
from service_pb2 import *

class BhvStarterClearBall():

    def __init__(self):
        pass
    

    def execute(self, agent: IAgent):
        wm = agent.wm
        ball_pos = Vector2D(wm.ball.position.x, wm.ball.position.y)
        target = Vector2D(agent.server_params.pitch_half_length, 0.0)
        if ball_pos.x() > -25.0 :
            if ball_pos.dist(Vector2D(0.0, -agent.server_params.pitch_half_width)) < ball_pos.dist(Vector2D(0.0, agent.server_params.pitch_half_width)) :
                target = Vector2D(0.0,-34.0)
            else:
                target = Vector2D(0.0,34.0)
        else :
            if abs(ball_pos.y()) < 10 and ball_pos.x() < -10.0 :
                if ball_pos.y() > 0.0 :
                    target = Vector2D(-agent.server_params.pitch_half_length, 20.0)
                else :
                    target = Vector2D(-agent.server_params.pitch_half_length, -20.0)
            else:
                if ball_pos.y() > 0.0 :
                    target = Vector2D(ball_pos.x(), 34.0)
                else : 
                    target = Vector2D(ball_pos.x(), -34.0)
        return PlayerAction(body_smart_kick=Body_SmartKick(target_point=RpcVector2D(x=target.x(), y=target.y()),
                                                                        first_speed=2.7,
                                                                            first_speed_threshold=2.7,
                                                                                max_steps=2))
        