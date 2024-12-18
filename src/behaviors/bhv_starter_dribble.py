from typing import TYPE_CHECKING
from src.interfaces.IBehavior import IBehavior
from src.utils.tools import Tools
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.sector_2d import Sector2D
from service_pb2 import *


if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent
    
class BhvStarterDribble(IBehavior):

    def __init__(self):
        pass

    def execute(self, agent: "SamplePlayerAgent") -> bool:
        wm = agent.wm
        ball_pos = Vector2D(wm.ball.position.x, wm.ball.position.y)
        dribble_angle = (Vector2D(52.5, 0) - ball_pos).th().degree()
        dribble_speed = 0.8
        dribble_threshold = 0.7
        dribble_sector = Sector2D(ball_pos, 0, 3, dribble_angle - 15, dribble_angle + 15)
        
        if not Tools.exist_opponent_in(agent , dribble_sector):
            target = Vector2D.polar2vector(3, dribble_angle) + ball_pos
            agent.add_action(PlayerAction(body_smart_kick=Body_SmartKick(target_point=Tools.convert_vector2d_to_rpc_vector2d(target),
                                                                         first_speed=dribble_speed,
                                                                         first_speed_threshold=dribble_threshold,
                                                                         max_steps=2)))
            return True
        return False


    


