from src.interfaces.IAgent import IAgent
from service_pb2 import *
from pyrusgeom.vector_2d import Vector2D
#from src.behaviors.starter_setplay.bhv_starter_setplay import BhvStarterSetPlay #TODO
from src.utils.tools import Tools
from src.utils.tools import Tools
class BhvStarterGoToPlacedBall:
    
    def __init__(self, angle: float):
        self.M_ball_place_angle = angle  
        

    def execute(self, agent: IAgent):
        actions = []
        from src.behaviors.starter_setplay.bhv_starter_setplay import BhvStarterSetPlay
        setplay = BhvStarterSetPlay()
        
        dir_margin = 15.0
        sp = agent.server_params
        wm = agent.wm
        angle_diff = wm.ball.angle_from_self - self.M_ball_place_angle

        if abs(angle_diff) < dir_margin and wm.ball.dist_from_self < (agent.player_types[wm.self.id].player_size + sp.ball_size + 0.08):
            # already reach
            return actions

        # decide sub-target point
        ball_position = Tools.convert_rpc_vector2d_to_vector2d(wm.ball.position)
        self_position = Tools.convert_rpc_vector2d_to_vector2d(wm.self.position)
        sub_target = ball_position + Vector2D.polar2vector(2.0, self.M_ball_place_angle + 180.0)

        dash_power = 20.0
        dash_speed = -1.0
        if wm.ball.dist_from_self > 2.0:
            dash_power = setplay.get_set_play_dash_power(agent)
        else:
            dash_speed = agent.player_types[wm.self.id].player_size
            dash_power = Tools.get_dash_power_to_keep_speed(agent, dash_speed, wm.self.effort) #DEBUG NEEDED
        # it is necessary to go to sub target point
        if abs(angle_diff) > dir_margin:
            actions.append(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=Tools.convert_vector2d_to_rpc_vector2d(sub_target), distance_threshold=0.1, max_dash_power=50)))
        # dir diff is small. go to ball
        else:
            # body dir is not right
            if abs(wm.ball.angle_from_self - wm.self.body_direction) > 1.5:
                actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=1)))
            # dash to ball
            else:
                actions.append(PlayerAction(dash=Dash(power=dash_power, relative_direction=0)))
                
        return actions