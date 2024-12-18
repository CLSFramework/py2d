from typing import TYPE_CHECKING
from src.interfaces.IBehavior import IBehavior
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from src.utils.tools import Tools
from service_pb2 import *


if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent
    
class BhvStarterClearBall(IBehavior):

    def __init__(self):
        pass

    def execute(self, agent: "SamplePlayerAgent") -> bool:
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
        agent.add_action(PlayerAction(body_smart_kick=Body_SmartKick(target_point=Tools.convert_vector2d_to_rpc_vector2d(target),
                                                                     first_speed=2.7,
                                                                     first_speed_threshold=2.7,
                                                                     max_steps=2)))
        return True
                         
        