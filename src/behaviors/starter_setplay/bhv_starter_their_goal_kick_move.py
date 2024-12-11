from src.interfaces.IAgent import IAgent
#from src.setplay.BhvSetPlay import BhvSetPlay
from service_pb2 import *
from src.strategy.starter_strategy import StarterStrategy
from pyrusgeom.vector_2d import Vector2D
from src.utils.tools import Tools
from pyrusgeom.soccer_math import inertia_n_step_point
from pyrusgeom.ray_2d import Ray2D
from pyrusgeom.size_2d import Size2D
from pyrusgeom.rect_2d import Rect2D
from pyrusgeom.angle_deg import AngleDeg
from src.utils.convertor import Convertor

class BhvStarterTheirGoalKickMove:
    def __init__(self):
        pass
    
    def execute(agent: IAgent) -> bool:
        expand_their_penalty = Rect2D(
            Vector2D(agent.server_params.their_penalty_area_line_x - 0.75,
                      -agent.server_params.penalty_area_half_width - 0.75),
            Size2D(agent.server_params.penalty_area_length + 0.75,
                   (agent.server_params.penalty_area_half_width*2) + 1.5)
        )

        wm = agent.wm
        actions = []
        actions += BhvStarterTheirGoalKickMove.do_chase_ball(agent)

        
        self_position = Vector2D(wm.self.position.x, wm.self.position.y)
        ball_position = Vector2D(wm.ball.position.x, wm.ball.position.y)
        ball_velocity = Vector2D(wm.ball.velocity.x, wm.ball.velocity.y)
        intersection_list = expand_their_penalty.intersection(Ray2D(ball_position, ball_velocity.th()))
        intersection = intersection_list[0]
        if ball_velocity.r()  > 0.2:
            if not expand_their_penalty.contains(ball_position) or len(intersection_list)  != 1: #TODO Check
                return BhvStarterTheirGoalKickMove.do_normal(agent)
        else:
            if (wm.ball.position.x > agent.server_params.their_penalty_area_line_x + 7.0 and
                abs(wm.ball.position.y) < (agent.server_params.goal_width/2.0) + 2.0):
                return BhvStarterTheirGoalKickMove.do_normal(agent)

            intersection.set_x(agent.server_params.their_penalty_area_line_x - 0.76)
            intersection.set_y(wm.ball.position.y)

        min_dist = 100.0
        nearest_tm = Tools.GetTeammateNearestTo(agent, intersection)
        nearest_tm_pos = Vector2D(nearest_tm.position.x, nearest_tm.position.y)
        min_dist = nearest_tm_pos.dist(intersection)
        if min_dist < self_position.dist(intersection):
            return BhvStarterTheirGoalKickMove.do_normal(agent)
        dash_power = wm.self.get_safety_dash_power #TODO

        if intersection.x() < agent.server_params.their_penalty_area_line_x and wm.self.position.x > agent.server_params.their_penalty_area_line_x - 0.5:
            intersection.set_y(agent.server_params.penalty_area_half_width - 0.5)
            if wm.self.position.y < 0.0:
                intersection.set_y(intersection.y() * -1.0)
                
        elif intersection.y() > agent.server_params.penalty_area_half_width and abs(wm.self.position.y) < agent.server_params.penalty_area_half_width + 0.5:
            intersection.set_y(agent.server_params.penalty_area_half_width + 0.5)
            if wm.self.position.y < 0.0:
                intersection.set_y(intersection.y() * -1.0)

        dist_thr = max(wm.ball.dist_from_self * 0.07, 1.0)
        
        actions.append(PlayerAction(body_go_to_point=Body_GoToPoint(Convertor.convert_vector2d_to_rpc_vector2d(intersection), distance_threshold=dist_thr, max_dash_power=dash_power)))
        actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=0)))
        
        return actions

    def do_normal(agent: IAgent):
        wm = agent.wm
        actions = []
        from src.behaviors.starter_setplay.bhv_starter_setplay import BhvStarterSetPlay
        dash_power = BhvStarterSetPlay.get_set_play_dash_power(agent)
        targ = StarterStrategy.get_position(agent, wm.self.uniform_number)
        target_point = Vector2D(targ.x, targ.y)

        # Attract to ball
        if target_point.x() > 25.0 and (target_point.y() * wm.ball.position.y < 0.0 or target_point.abs_y() < 10.0):
            y_diff = wm.ball.position.y - target_point.y()
            target_point.set_y(target_point.y() + (y_diff * 0.4))

        # Check penalty area
        if wm.self.position.x > agent.server_params.their_penalty_area_line_x and target_point.abs_y() < agent.server_params.penalty_area_half_width:
            target_point.set_y(agent.server_params.penalty_area_half_width + 0.5)
            if wm.self.position.y < 0.0:
                target_point.set_y(target_point.y() * -1)

        dist_thr = max(wm.ball.dist_from_self * 0.07, 1.0)
        actions.append(PlayerAction(body_go_to_point=Body_GoToPoint(Convertor.convert_vector2d_to_rpc_vector2d(target_point), distance_threshold=dist_thr, max_dash_power=dash_power)))
        actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=0)))
        
        return actions

    def do_chase_ball(agent: IAgent) -> bool:
        wm = agent.wm
        actions = []
        ball_position = Vector2D(wm.ball.position.x, wm.ball.position.y)
        ball_velocity = Vector2D(wm.ball.velocity.x, wm.ball.velocity.y)

        if ball_velocity.r() < 0.2:
            return []

        self_min = wm.intercept_table.self_reach_steps

        if self_min > 10:
            return []

        get_pos = Tools.inertia_point(ball_position, ball_velocity,self_min, agent.server_params.ball_decay)

        pen_x = agent.server_params.their_penalty_area_line_x - 1.0
        pen_y = agent.server_params.penalty_area_half_width + 1.0
        their_penalty = Rect2D(
            Vector2D(pen_x, -pen_y),
            Size2D(agent.server_params.penalty_area_length + 1.0,
                   (agent.server_params.penalty_area_half_width * 2) - 2.0)
        )
        if their_penalty.contains(get_pos):
            return []

        if (get_pos.x() > pen_x and wm.self.position.x < pen_x and abs(wm.self.position.y) < pen_y - 0.5):
            return []


        # Can chase!!
        
        actions.append(PlayerAction(body_intercept=Body_Intercept()))
        return actions
