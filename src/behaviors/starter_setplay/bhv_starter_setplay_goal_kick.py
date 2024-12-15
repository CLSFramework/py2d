from typing import TYPE_CHECKING
from src.interfaces.IAgent import IAgent
from service_pb2 import *
from pyrusgeom.vector_2d import Vector2D
#from src.setplay.BhvSetPlay import BhvSetPlay
from src.behaviors.bhv_starter_clearball import BhvStarterClearBall
from src.utils.tools import Tools
from src.behaviors.bhv_starter_kick_planner import BhvStarterKickPlanner
from src.behaviors.bhv_starter_pass import BhvStarterPass
from src.strategy.starter_strategy import StarterStrategy
from src.behaviors.bhv_starter_clearball import BhvStarterClearBall
from src.utils.convertor import Convertor

if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent
class BhvStarterSetPlayGoalKick:
    def __init__():
        pass
    
    def execute(agent:IAgent):
        from src.behaviors.starter_setplay.bhv_starter_setplay import BhvStarterSetPlay
        if BhvStarterSetPlay.is_kicker(agent):
            return BhvStarterSetPlayGoalKick.do_kick(agent)
        else:
            return BhvStarterSetPlayGoalKick.do_move(agent)

    def do_kick(agent: IAgent):
        from src.behaviors.starter_setplay.bhv_starter_go_to_placed_ball import BhvStarterGoToPlacedBall
        
        actions = []
        actions += BhvStarterSetPlayGoalKick.do_second_kick(agent)
        
        actions += BhvStarterGoToPlacedBall(0.0).execute(agent)

        wait = BhvStarterSetPlayGoalKick.do_kick_wait(agent)
        if wait != []:
            actions += wait
            return actions
        
        actions += BhvStarterSetPlayGoalKick.do_pass(agent)
        
        actions += BhvStarterSetPlayGoalKick.do_kick_to_far_side(agent)
        
        wm = agent.wm
        real_set_play_count = wm.cycle - agent.wm.last_set_play_start_time
        if real_set_play_count <= agent.server_params.drop_ball_time - 10:
            actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=1)))
            return actions
        actions.append(BhvStarterClearBall.execute(agent))
        return actions

    def do_second_kick(agent:IAgent):
        wm = agent.wm
        actions = []
        ball_position = Vector2D(wm.ball.position.x, wm.ball.position.y)
        ball_velocity = Vector2D(wm.ball.velocity.x, wm.ball.velocity.y)
        if wm.ball.position.x < -agent.server_params.pitch_half_length + agent.server_params.goal_area_length + 1.0 and abs(wm.ball.position.y) < agent.server_params.goal_width * 0.5 + 1.0:
            return []
        
        if wm.self.is_kickable:
            actions += BhvStarterSetPlayGoalKick.do_pass(agent)
            actions += BhvStarterClearBall.execute(agent)
        
        actions += BhvStarterSetPlayGoalKick.do_intercept(agent)
        
        ball_final = Tools.BallInertiaFinalPoint(ball_position, ball_velocity, agent.server_params.ball_decay)
        
        actions.append(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=Convertor.convert_vector2d_to_rpc_vector2d(ball_final), distance_threshold=2.0, max_dash_power=agent.server_params.max_dash_power)))
        
        actions.append(PlayerAction(body_turn_to_point=Body_TurnToPoint(target_point=RpcVector2D(0, 0), cycle=2)))
        
        return actions

    def do_kick_wait(agent:IAgent):
        wm = agent.wm
        actions = []
        real_set_play_count = wm.cycle - wm.last_set_play_start_time

        if real_set_play_count >= agent.server_params.drop_ball_time - 10:
            return []
        from src.behaviors.starter_setplay.bhv_starter_setplay import BhvStarterSetPlay
        if BhvStarterSetPlay.is_delaying_tactics_situation(agent):
            actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=1)))
            return actions
        
        if abs(wm.ball.angle_from_self - wm.self.body_direction) > 3.0:
            actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=1)))
            return actions
        
        if wm.set_play_count <= 6:
            actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=1)))
            return actions

        if wm.set_play_count <= 30 and len(Tools.TeammatesFromSelf(agent)) == 0:
            actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=1)))
            return actions
        
        if wm.set_play_count >= 15 and wm.see_time == wm.cycle and wm.self.stamina > agent.server_params.stamina_max:
            return []
        
        if wm.set_play_count <= 3 or wm.see_time != wm.cycle or wm.self.stamina < agent.server_params.stamina_max * 0.9:
            actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=1)))
            return actions
            
        return []

    def do_pass(agent:IAgent):
        return [BhvStarterPass.execute(agent)]

    def do_intercept(agent:IAgent):
        wm = agent.wm
        actions = []
        
        if wm.ball.position.x < -agent.server_params.pitch_half_length + agent.server_params.goal_area_length + 1.0 and abs(wm.ball.position.y) < agent.server_params.goal_area_width * 0.5 + 1.0:
            return []
        
        if wm.self.is_kickable:
            return []

        self_min = wm.intercept_table.self_reach_steps
        mate_min = wm.intercept_table.first_teammate_reach_steps
        if self_min > mate_min:
            return []
        
        ball_position = Vector2D(wm.ball.position.x, wm.ball.position.y)
        ball_velocity = Vector2D(wm.ball.velocity.x, wm.ball.velocity.y)
        trap_pos = Tools.inertia_point(ball_position, ball_velocity, self_min, agent.server_params.ball_decay)
        if (trap_pos.x() > agent.server_params.our_penalty_area_line_x - 8.0 and abs(trap_pos.y()) > agent.server_params.penalty_area_half_width - 5.0) or ball_velocity.r2() < 0.25:
            actions.append(PlayerAction(body_intercept=Body_Intercept()))
        
        return actions

    def do_move(agent:"SamplePlayerAgent"):
        actions = []
        actions += BhvStarterSetPlayGoalKick.do_intercept(agent)
        from src.behaviors.starter_setplay.bhv_starter_setplay import BhvStarterSetPlay
        wm = agent.wm
        ball_position = Vector2D(wm.ball.position.x, wm.ball.position.y)
        dash_power = BhvStarterSetPlay.get_set_play_dash_power(agent)
        dist_thr = max(wm.ball.dist_from_self * 0.07, 1.0)

        target_rpc = Convertor.convert_vector2d_to_rpc_vector2d(agent.strategy.get_position(wm.self.uniform_number, agent))
        target_point = Vector2D(target_rpc.x, target_rpc.y)
        target_point.set_y(target_point.y() + wm.ball.position.y * 0.5)

        if abs(target_point.y()) > agent.server_params.pitch_half_width - 1.0:
            target_point.set_y((target_point.y() / abs(target_point.y())) * (agent.server_params.pitch_half_width - 1.0))

        if wm.self.stamina > agent.server_params.stamina_max * 0.9:
            
            nearest_opp = Tools.GetOpponentNearestToSelf(agent)
            if nearest_opp and nearest_opp.dist_from_self < 3.0:
                add_vec = ball_position - target_point
                add_vec.set_length(3.0)

                time_val = wm.cycle % 60
                if time_val < 20:
                    pass
                elif time_val < 40:
                    target_point += add_vec.rotated_vector(90.0)
                else:
                    target_point += add_vec.rotated_vector(-90.0)

                target_point.set_x(min(max(-agent.server_params.pitch_half_length, target_point.x()), agent.server_params.pitch_half_length))
                target_point.set_y(min(max(-agent.server_params.pitch_half_width, target_point.y()), agent.server_params.pitch_half_width))

        actions.append(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=Convertor.convert_vector2d_to_rpc_vector2d(target_point), distance_threshold=dist_thr, max_dash_power=dash_power)))
        actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=1)))
        
        self_position = Vector2D(wm.self.position.x, wm.self.position.y)
        if (self_position.dist(target_point) > ball_position.dist(target_point) * 0.2 + 6.0 or wm.self.stamina < agent.server_params.stamina_max * 0.7):
            if not wm.self.stamina_capacity == 0: #TODO
                pass

        return actions

    def do_kick_to_far_side(agent:IAgent):
        wm = agent.wm
        actions = []
        target_point = Vector2D(agent.server_params.our_penalty_area_line_x - 5.0, agent.server_params.penalty_area_half_width)
        if wm.ball.position.y > 0.0:
            target_point.set_y( target_point.y() * -1.0)
        ball_position = Vector2D(wm.ball.position.x, wm.ball.position.y)
        ball_move_dist = ball_position.dist(target_point)
        ball_first_speed = Tools.calc_first_term_geom_series_last(0.7, ball_move_dist, agent.server_params.ball_decay)
        ball_first_speed = min(agent.server_params.ball_speed_max, ball_first_speed)
        ball_first_speed = min(wm.self.kick_rate * agent.server_params.max_power, ball_first_speed)

        accel = target_point - ball_position
        accel.set_length(ball_first_speed)

        kick_power = min(agent.server_params.max_power, accel.r() / wm.self.kick_rate)
        kick_angle = accel.th()
        actions.append(PlayerAction(kick=Kick(power=kick_power, relative_direction=kick_angle.degree() - wm.self.body_direction)))
        return actions
