from typing import TYPE_CHECKING
from src.interfaces.IBehavior import IBehavior
from src.interfaces.IAgent import IAgent
from pyrusgeom.vector_2d import Vector2D
from service_pb2 import *


if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent


class BhvStarterShoot(IBehavior):
    def __init__(self):
        pass
    
    def execute(self, agent: "SamplePlayerAgent") -> bool:
        wm = agent.wm
        ball_pos = Vector2D(wm.ball.position.x, wm.ball.position.y)
        ball_max_velocity = agent.server_params.ball_speed_max

        center_goal = Vector2D ( agent.server_params.pitch_half_length, 0.0 )
        right_goal = Vector2D ( agent.server_params.pitch_half_length , agent.server_params.goal_width / 2.0 ) # Lower Pole 
        left_goal = Vector2D ( agent.server_params.pitch_half_length , -(agent.server_params.goal_width / 2.0) ) # Upper Pole 
        
        if ball_pos.dist(center_goal) <= 25.0:

            if left_goal.dist(ball_pos) < right_goal.dist(ball_pos):
                agent.add_log_message(LoggerLevel.SHOOT, f": Shooting to {left_goal}", agent.wm.self.position.x, agent.wm.self.position.y - 2, '\033[31m')
                agent.add_action(PlayerAction(body_smart_kick=Body_SmartKick(target_point=RpcVector2D(x=left_goal.x(), y=left_goal.y()),
                                                                             first_speed=ball_max_velocity,
                                                                             first_speed_threshold=0.1,
                                                                             max_steps=3)))
            else:
                agent.add_log_message(LoggerLevel.SHOOT, f": Shooting to {right_goal}", agent.wm.self.position.x, agent.wm.self.position.y - 2, '\033[31m')
                agent.add_action(PlayerAction(body_smart_kick=Body_SmartKick(target_point=RpcVector2D(x=right_goal.x(), y=right_goal.y()),
                                                                             first_speed=ball_max_velocity,
                                                                             first_speed_threshold=0.1,
                                                                             max_steps=3)))
            return True
        return False


        

